"""One fight between two fighters in an arena: the deterministic simulation.

`Match.step` takes both players' inputs for one 1/60 s step and returns what happened.
Nothing here reads devices, the clock or the screen, so the same inputs always give
the same fight (tests, replays, and later online play rely on it).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from jojo_arena.combat import interactions
from jojo_arena.combat.arena import Arena, Cage
from jojo_arena.combat.clash import Clash
from jojo_arena.combat.cutscene import Cutscene
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import Attack, Fighter, State
from jojo_arena.combat.kit import ATTACK_SLOTS, Kit, MoveDef, ProjectileDef
from jojo_arena.combat.projectile import Projectile
from jojo_arena.combat.rules import Rules, per_frame
from jojo_arena.combat.traps import Trap, Web, web_layout
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Rect, Vec2, circles_overlap


@dataclass(frozen=True)
class Strike:
    """One hit about to land, whatever delivered it (fist, projectile...)."""

    damage: int
    hitstun_f: int
    blockstun_f: int
    knockback: Vec2
    wall_bounce: bool
    hitstop_f: int
    source: Vec2  # where it comes from, to know if the guard faces it
    where: Vec2  # contact point, for effects
    unblockable: bool = False
    drain: float = 0.0
    melee: bool = False  # a blow (counters catch blows, not projectiles)
    guard_mult: float = 1.0  # multiplies the guard gauge damage
    key: tuple | None = None  # which move it belongs to, for combo scaling
    super_move: bool = False  # supers are built around stopped time: not softened in it
    hamon: bool = False  # Hamon burns vampires and Pillar Men
    freeze_f: int = 0  # frozen solid this long on a clean hit
    status: str = ""  # left burning, frozen stiff or crackling on a clean hit
    status_f: int = 0


class Match:
    def __init__(self, kits: tuple[Kit, Kit], rules: Rules, arena: Arena) -> None:
        self.rules = rules
        self.arena = arena
        self.fighters = [
            Fighter(0, kits[0], rules, arena.spawns[0], Vec2(1, 0)),
            Fighter(1, kits[1], rules, arena.spawns[1], Vec2(-1, 0)),
        ]
        self.projectiles: list[Projectile] = []
        self.traps: list[Trap] = []
        self.webs: list[Web] = []
        self._last_prop_pos: dict[int, Vec2] = {}
        # Training can stretch or shorten stopped time; a real fight leaves it at 1.
        self.time_stop_mult = 1.0
        self.cutscene: Cutscene | None = None
        self.hitstop = 0
        self.slowmo = 0  # steps left at half speed (Stylish Evade)
        self.super_freeze = 0  # steps left of a super move's flash
        self.super_user: int | None = None
        self.clash: Clash | None = None
        self.time_stop: interactions.TimeStop | None = None
        self.time_stops_endured = [0, 0]  # per fighter, for the time stopper rule
        self.tick = 0
        self.dawn_announced = False

    def opponent(self, fighter: Fighter) -> Fighter:
        return self.fighters[1 - fighter.index]

    @property
    def cinematic(self) -> bool:
        """Moments that pause the round timer: clash, super flash, stopped time, cutscene."""
        return (
            self.clash is not None
            or self.super_freeze > 0
            or self.time_stop is not None
            or self.cutscene is not None
        )

    # Main step ------------------------------------------------------------------------

    def step(self, inputs: tuple[InputFrame, InputFrame]) -> list[Event]:
        self.tick += 1
        for fighter, frame in zip(self.fighters, inputs, strict=True):
            fighter.remember_presses(frame)
        if self.cutscene is not None:
            return self._update_cutscene()
        if self.clash is not None:
            return self._update_clash(inputs)
        if self.super_freeze > 0:
            self.super_freeze -= 1
            if self.super_freeze == 0:
                self.super_user = None
            return []
        if self.slowmo > 0:
            self.slowmo -= 1
            if self.slowmo % 2:
                return []  # half speed: simulate every other step
        if self.hitstop > 0:
            # Impact freeze: everything holds still for a few frames.
            self.hitstop -= 1
            return []
        events: list[Event] = []
        inputs = self._possession_inputs(inputs)
        inputs, prop_events = self._handle_props(inputs)
        events += prop_events
        moving = [f for f in self.fighters if not f.frozen]
        for fighter in moving:
            for event in fighter.control(inputs[fighter.index], self.opponent(fighter).pos):
                if event.kind in ("hha", "gha", "awaken"):
                    self.super_freeze = self.rules.super_freeze_f
                    self.super_user = fighter.index
                elif event.kind == "flash_cancel":
                    self.hitstop = max(self.hitstop, self.rules.flash_cancel_freeze_f)
                events.append(event)
        events += self._trigger_time_stops()
        for fighter in self.fighters:
            attack = fighter.attack
            if attack is None or attack.cutscene_done or attack.move.cinematic_at != "start":
                continue
            if attack.move.cinematic:
                events += self._start_cutscene(fighter, self.opponent(fighter), attack)
                return events  # the whole fight holds from now on
        moved: list[Event] = []
        for fighter in self.fighters:
            if not fighter.frozen:
                moved += fighter.integrate(self.arena)
        events += moved
        events += self._take_exits(moved)
        for fighter in self.fighters:
            if fighter.possessed_f > 0 and fighter.possessor is not None:
                # The Stand is inside the possessed body and moves with it.
                possessor = self.fighters[fighter.possessor]
                if possessor.remote:
                    possessor.remote_pos = fighter.pos.copy()
        events += self._update_infiltration()
        self._separate_bodies()
        self._release_attacks()
        self._apply_suction()
        events += self._update_projectiles()
        events += self._update_traps()
        events += self._update_webs()
        events += self._resolve_melee()
        events += self._resolve_projectile_hits()
        events += self._apply_sunlight()
        events += self._apply_statuses()
        events += self._update_hazards()
        events += self._update_awakenings()
        events += self._update_cage()
        for fighter in self.fighters:
            if fighter.frozen:
                continue
            fighter.advance()
            if fighter.in_resolve and not fighter.resolve_announced:
                fighter.resolve_announced = True
                events.append(Event("resolve", fighter.pos, fighter.index))
        events += self._settle_props()
        for obstacle in self.arena.obstacles:
            obstacle.tick()
        events += interactions.tick_time_stop(self)
        return events

    def _trigger_time_stops(self) -> list[Event]:
        events: list[Event] = []
        for fighter in self.fighters:
            attack = fighter.attack
            if fighter.frozen or attack is None or attack.stopped_time:
                continue
            move = attack.move
            if move.time_stop_f and (move.time_stop_at == "start" or attack.active):
                attack.stopped_time = True
                frames = max(1, round(move.time_stop_f * self.time_stop_mult))
                events += interactions.start_time_stop(self, fighter, frames)
        return events

    # Bodies -----------------------------------------------------------------------------

    def _separate_bodies(self) -> None:
        a, b = self.fighters
        if not (a.alive and b.alive) or State.DASH in (a.state, b.state):
            return  # dashes go through the opponent
        if a.inside is not None or b.inside is not None:
            return  # one body is inside the other
        r = self.rules.body_radius
        if not circles_overlap(a.pos, r, b.pos, r):
            return
        offset = a.pos - b.pos
        distance = offset.length()
        normal = offset.normalized() if distance > 1e-6 else Vec2(1, 0)
        overlap = 2 * r - distance
        # A frozen body does not budge: the other one takes the whole push.
        share_a = 0.0 if a.frozen else (1.0 if b.frozen else 0.5)
        share_b = 0.0 if b.frozen else (1.0 if a.frozen else 0.5)
        a.pos, _, _ = self.arena.constrain(a.pos + normal * overlap * share_a, r)
        b.pos, _, _ = self.arena.constrain(b.pos - normal * overlap * share_b, r)

    def _apply_suction(self) -> None:
        """A move with `pull` drags the other fighter in while it is active: a vortex, or
        veins round an ankle. It runs before the hitboxes, so whoever is dragged into the
        mouth of the move is then ground up by it."""
        for fighter in self.fighters:
            attack = fighter.attack
            move = attack.move if attack is not None else None
            if fighter.frozen or attack is None or not attack.active or move.pull <= 0:
                continue
            target = self.opponent(fighter)
            if not target.alive or target.frozen or target.state is State.CLASH:
                continue
            offset = fighter.pos - target.pos
            distance = offset.length()
            floor = self.rules.body_radius * 2
            reach = move.pull_range or move.reach + move.radius
            if distance > reach or distance <= floor:
                continue  # out of the wind, or already in the middle of it
            step = min(move.pull, distance - floor)
            pulled = target.pos + offset.normalized() * step
            target.pos, _, _ = self.arena.constrain(pulled, self.rules.body_radius)

    # Projectiles and traps ------------------------------------------------------------------

    def _release_attacks(self) -> None:
        """Fire projectiles and lay traps on the first active frame of a move."""
        for fighter in self.fighters:
            attack = fighter.attack
            if fighter.frozen or attack is None or attack.fired or not attack.active:
                continue
            move = attack.move
            if move.trap is not None:
                attack.fired = True
                self._lay_trap(fighter, attack)
            elif move.projectile is not None:
                defn = move.projectile
                if move.detonate and attack.volleys == 0:
                    self._detonate(fighter, attack, defn)
                if attack.active_offset < attack.volleys * defn.wave_every_f:
                    continue  # the next volley is not due yet
                attack.volleys += 1
                attack.fired = attack.volleys >= defn.waves
                target = self.opponent(fighter).pos
                aim = attack.aim
                if attack.volleys % 2 == 0 and defn.count > 1:
                    # Every other volley fills the gaps of the previous one.
                    gap = math.radians(defn.spread_deg) / (defn.count - 1) / 2
                    aim = Vec2.from_angle(aim.angle() + gap)
                origin = fighter.strike_origin()
                volley = self._spawn(fighter.index, origin, aim, defn, target)
                for projectile in volley:
                    projectile.key = (fighter.index, attack.serial)
                    projectile.hamon = attack.hamon or defn.hamon
                    projectile.boost = attack.boost
                self.projectiles += volley
                if move.disarm_f:
                    fighter.disarmed_f = move.disarm_f

    def _spawn(
        self, owner: int, origin: Vec2, aim: Vec2, defn: ProjectileDef, target: Vec2
    ) -> list[Projectile]:
        """One or more projectiles: a fan from `origin`, or a ring closing on `target`."""
        stop_after = self.rules.time_stop_projectile_flight_f if self.time_stop else None
        spawned = []
        for i in range(defn.count):
            if defn.origin == "ring":
                angle = 2 * math.pi * i / defn.count
                start = target + Vec2.from_angle(angle, defn.ring_radius)
                start, _, _ = self.arena.constrain(start, defn.radius)
                direction = (target - start).normalized() if target != start else aim
            else:
                offset = 0.0
                if defn.count > 1:
                    offset = math.radians(defn.spread_deg) * (i / (defn.count - 1) - 0.5)
                direction = Vec2.from_angle(aim.angle() + offset)
                start = origin + direction * (self.rules.body_radius + defn.radius + 2)
            spawned.append(
                Projectile(
                    owner, start, direction * defn.speed, defn, defn.lifetime_f, True, stop_after
                )
            )
        return spawned

    def _reflects(self, fighter: Fighter) -> bool:
        attack = fighter.attack
        return (
            fighter.state == State.ATTACK
            and attack is not None
            and attack.move.reflect
            and attack.active
            and not fighter.frozen
        )

    def _reflect(self, projectile: Projectile, fighter: Fighter) -> list[Event]:
        """A parry sends the projectile back where it came from: it is the parrier's now."""
        projectile.owner = fighter.index
        projectile.velocity = projectile.velocity * -1
        projectile.life = projectile.defn.lifetime_f
        projectile.key = (fighter.index, fighter.attack.serial)
        projectile.returning = projectile.spent = False
        return [Event("reflect", projectile.pos, fighter.index)]

    def _detonate(self, fighter: Fighter, attack: Attack, defn: ProjectileDef) -> None:
        """The hidden plan: every trap the fighter laid turns into a blast, and every
        grenade still rolling goes off now."""
        for trap in [t for t in self.traps if t.owner == fighter.index]:
            self.traps.remove(trap)
            blast = Projectile(fighter.index, trap.pos.copy(), Vec2(), defn, 1)
            blast.key = (fighter.index, attack.serial)
            blast.hamon, blast.boost = attack.hamon, attack.boost
            self.projectiles.append(blast)
        for projectile in self.projectiles:
            if projectile.owner == fighter.index and projectile.defn.explode_radius:
                projectile.life = min(projectile.life, 1)

    def _lay_trap(self, fighter: Fighter, attack: Attack) -> None:
        defn = attack.move.trap
        origin = fighter.strike_origin()
        pos, _, _ = self.arena.constrain(origin + attack.aim * defn.distance, defn.radius)
        own = [t for t in self.traps if t.owner == fighter.index]
        if len(own) >= defn.max_count:
            self.traps.remove(own[0])  # the oldest gives way
        self.traps.append(Trap(fighter.index, pos, defn, defn.lifetime_f))

    def _update_traps(self) -> list[Event]:
        events: list[Event] = []
        kept = []
        for trap in self.traps:
            owner = self.fighters[trap.owner]
            if owner.frozen:
                kept.append(trap)
                continue
            trap.life -= 1
            target = self.fighters[1 - trap.owner]
            if trap.defn.fragile and owner.state in (State.HITSTUN, State.GUARD_BROKEN):
                # A bubble is a bubble: one blow on Caesar and every lens pops, empty.
                events.append(Event("trap_popped", trap.pos, trap.owner))
                continue
            if target.alive and trap.touched_by(target.pos, self.rules.hurt_radius):
                aim = trap.pos.copy()
                direction = (target.pos - aim).normalized()
                shots = self._spawn(
                    trap.owner, aim - direction * 6, direction, trap.defn.projectile, target.pos
                )
                for shot in shots:
                    shot.hamon = trap.defn.projectile.hamon
                self.projectiles += shots
                events.append(Event("trap_triggered", trap.pos, trap.owner))
            elif trap.life > 0:
                kept.append(trap)
        self.traps = kept
        return events

    def _explode(self, projectile: Projectile, blast: Event) -> list[Event]:
        """A grenade blows up: everyone but its thrower within the blast is hit."""
        target = self.fighters[1 - projectile.owner]
        reach = blast.value + self.rules.body_radius
        if not target.alive or (target.pos - blast.pos).length() > reach:
            return []
        defn = projectile.defn
        away = (target.pos - blast.pos).normalized() if target.pos != blast.pos else Vec2(1, 0)
        strike = Strike(
            damage=round(defn.damage * projectile.boost),
            hitstun_f=defn.hitstun_f,
            blockstun_f=defn.blockstun_f or round(defn.hitstun_f * self.rules.blockstun_ratio),
            knockback=away * defn.knockback,
            wall_bounce=defn.wall_bounce,
            hitstop_f=defn.hitstop_f,
            source=blast.pos,
            where=target.pos,
            key=projectile.key,
            hamon=projectile.hamon,
            status=defn.status,
            status_f=defn.status_f,
            drain=defn.drain,
        )
        _, events = self._strike(self.fighters[projectile.owner], target, strike)
        return events

    def _fly_home(self, projectile: Projectile) -> list[Event]:
        """A boomerang: halfway through its flight it heads back to its owner, who
        catches it."""
        owner = self.fighters[projectile.owner]
        if not projectile.returning and projectile.life <= projectile.defn.lifetime_f // 2:
            projectile.turn_back()
        if not projectile.returning:
            return []
        home = owner.pos - projectile.pos
        if home.length() < self.rules.body_radius + projectile.radius:
            projectile.alive = False
            return [Event("catch", owner.pos, owner.index)]
        projectile.velocity = home.normalized() * projectile.defn.speed
        return []

    def _projectile_moves(self, projectile: Projectile) -> bool:
        return not self.fighters[projectile.owner].frozen and not projectile.hanging

    def _update_projectiles(self) -> list[Event]:
        events: list[Event] = []
        for projectile in self.projectiles:
            if self.fighters[projectile.owner].frozen:
                continue
            if projectile.defn.homing and self._projectile_moves(projectile):
                target = self.fighters[1 - projectile.owner]
                projectile.steer(target.pos, projectile.defn.homing)
            if projectile.defn.returns and self._projectile_moves(projectile):
                events += self._fly_home(projectile)
                if not projectile.alive:
                    continue
            update = projectile.update(self.arena)
            events += update
            for event in update:
                if event.kind in ("explosion", "burst"):
                    events += self._explode(projectile, event)
        # Grenades roll on the ground, under the flying projectiles.
        live = [
            p
            for p in self.projectiles
            if p.alive and self._projectile_moves(p) and not p.defn.explode_radius
        ]
        for i, a in enumerate(live):
            for b in live[i + 1 :]:
                if (
                    a.owner != b.owner
                    and a.alive
                    and b.alive
                    and circles_overlap(a.pos, a.radius, b.pos, b.radius)
                ):
                    a.alive = b.alive = False
                    events.append(Event("projectile_clash", (a.pos + b.pos) * 0.5))
        self.projectiles = [p for p in self.projectiles if p.alive]
        return events

    def _touches(self, center: Vec2, radius: float, defender: Fighter) -> bool:
        """Does a circle reach the defender's body or Stand?"""
        return any(circles_overlap(center, radius, c, r) for c, r in defender.hurtboxes())

    def _resolve_projectile_hits(self) -> list[Event]:
        events: list[Event] = []
        for projectile in self.projectiles:
            target = self.fighters[1 - projectile.owner]
            if not target.alive or projectile.spent or not self._projectile_moves(projectile):
                continue
            if projectile.defn.explode_radius:
                continue  # a grenade only hurts when it blows up
            if not self._touches(projectile.pos, projectile.radius, target):
                continue
            if self._reflects(target):
                events += self._reflect(projectile, target)
                continue
            defn = projectile.defn
            strike = Strike(
                damage=round(defn.damage * projectile.boost),
                hitstun_f=defn.hitstun_f,
                blockstun_f=defn.blockstun_f or round(defn.hitstun_f * self.rules.blockstun_ratio),
                knockback=projectile.velocity.normalized() * defn.knockback,
                wall_bounce=defn.wall_bounce,
                hitstop_f=defn.hitstop_f,
                source=projectile.pos - projectile.velocity * 4,
                where=projectile.pos,
                key=projectile.key,
                hamon=projectile.hamon,
                status=defn.status,
                status_f=defn.status_f,
                drain=defn.drain,
            )
            landed, strike_events = self._strike(self.fighters[projectile.owner], target, strike)
            events += strike_events
            if landed and projectile.defn.returns:
                projectile.spent = True  # a boomerang flies home after one hit
                projectile.turn_back()
            elif landed:
                projectile.alive = False  # dodged projectiles keep flying
        self.projectiles = [p for p in self.projectiles if p.alive]
        return events

    # Melee ------------------------------------------------------------------------------

    def _resolve_melee(self) -> list[Event]:
        clash_pos = self._rush_collision() or self._detect_clash()
        if clash_pos is not None:
            return self._start_clash(clash_pos)
        events: list[Event] = []
        hits = []
        for attacker in self.fighters:
            boxes = attacker.hitboxes()
            for center, radius in boxes:
                for i, obstacle in enumerate(self.arena.obstacles):
                    if i in attacker.attack.props_hit or not obstacle.solid:
                        continue
                    if obstacle.rect.inflate(radius).contains(center):
                        attacker.attack.props_hit.add(i)
                        broke = obstacle.damage(attacker.attack.move.damage)
                        events.append(Event("prop_break" if broke else "prop_hit", center))
            defender = self.opponent(attacker)
            if not defender.alive:
                continue
            touching = next((c for c, r in boxes if self._touches(c, r, defender)), None)
            if touching is not None:
                hits.append((attacker, attacker.attack, defender, touching))
        # Collect first, apply after: two hits on the same frame both land (a trade),
        # even though the first one interrupts the second attacker's move.
        for attacker, attack, defender, center in hits:
            move = attack.move
            # Moves centered on the body (reach 0) or on the target push away from it.
            if move.reach > 0 and not move.at_target:
                direction = attack.aim
            else:
                direction = defender.pos - (center if move.at_target else attacker.pos)
            knockback, wall_bounce = move.knockback, move.wall_bounce
            damage = move.damage
            if move.hits > 1 and attack.last_hit:
                if move.last_knockback is not None:
                    knockback = move.last_knockback
                if move.last_damage is not None:
                    damage = move.last_damage
                wall_bounce = wall_bounce or move.last_wall_bounce
            strike = Strike(
                damage=round(damage * attack.boost),
                hitstun_f=move.hitstun_f,
                blockstun_f=move.blockstun_f or round(move.hitstun_f * self.rules.blockstun_ratio),
                knockback=direction.normalized() * knockback,
                wall_bounce=wall_bounce,
                hitstop_f=move.hitstop_f,
                source=attacker.pos,
                where=center,
                unblockable=move.unblockable or (attack.boost > 1 and move.hamon_unblockable),
                drain=move.drain,
                melee=True,
                hamon=attack.hamon,
                guard_mult=move.guard_damage,
                freeze_f=move.freeze_f,
                status=move.status,
                status_f=move.status_f,
                key=(attacker.index, attack.serial),
                super_move=move.name in ("hha", "gha"),
            )
            landed, strike_events = self._strike(attacker, defender, strike)
            events += strike_events
            if landed:
                attack.connected = True
                attack.hits_done += 1
            clean = any(e.kind == "hit" and e.fighter == defender.index for e in strike_events)
            if clean and move.possess_f and defender.alive and attacker.remote:
                events += self._possess(attacker, defender, move.possess_f)
            if clean and move.infiltrate_f and defender.alive and attacker.inside is None:
                events += self._infiltrate(attacker, defender, move)
            if clean and move.cage_f and defender.alive:
                center = (attacker.pos + defender.pos) * 0.5
                self.arena.cage = Cage(center, move.cage_radius, move.cage_f, attacker.index)
                events.append(Event("cage", center, attacker.index))
            if clean and self._confirms(attack) and defender.alive:
                events += self._start_cutscene(attacker, defender, attack)
        return events

    # Clash -------------------------------------------------------------------------------

    # Props: pick up, throw, drop, respawn -----------------------------------------------

    def _handle_props(
        self, inputs: tuple[InputFrame, InputFrame]
    ) -> tuple[tuple[InputFrame, InputFrame], list[Event]]:
        """Pose near a prop: the Stand grabs it (even called back) and holds it, while its
        user keeps fighting as usual. Pose again: the Stand throws it. Those Pose presses
        are used up and do nothing else."""
        events: list[Event] = []
        frames = list(inputs)
        for fighter in self.fighters:
            if fighter.frozen:
                continue
            frame = frames[fighter.index]
            if fighter.carrying is not None:
                if fighter.state in (State.HITSTUN, State.GUARD_BROKEN, State.KO):
                    events += self._drop(fighter, fighter.pos)  # knocked: it falls
                elif fighter.state != State.CLASH and frame.was_pressed("pose"):
                    events += self._throw(fighter)
                elif fighter.can_act() and frame.was_pressed("heavy"):
                    events += self._swing(fighter)
                    frames[fighter.index] = _without(frame, ("pose", "heavy"))
                    continue
                frames[fighter.index] = _without(frame, ("pose",))  # no posing with it
                continue
            if fighter.remote or not fighter.can_act() or not frame.was_pressed("pose"):
                continue
            index = self._prop_within_reach(fighter)
            if index is not None:
                self.arena.obstacles[index].carried_by = fighter.index
                fighter.carrying = index
                frames[fighter.index] = _without(frame, ("pose",))
                events.append(Event("pickup", fighter.pos, fighter.index))
        return (frames[0], frames[1]), events

    def _swing(self, fighter: Fighter) -> list[Event]:
        """Heavy button while carrying: he swings the thing. Hair and tendrils carry
        further than an arm does, so they swing it from further out, over a wider arc."""
        wrapped = fighter.kit.prop_hold != "hands"  # hair or tendrils, not arms
        values = self.rules.prop_swing
        move = MoveDef(
            name="prop_swing",
            startup_f=values["startup_f"],
            active_f=values["active_f"],
            recovery_f=values["recovery_f"],
            damage=values["wrapped_damage"] if wrapped else values["damage"],
            reach=values["wrapped_reach"] if wrapped else values["reach"],
            radius=values["wrapped_radius"] if wrapped else values["radius"],
            shape="line" if wrapped else "circle",
            hitstun_f=values["hitstun_f"],
            knockback=per_frame(values["knockback"]),
            hitstop_f=values["hitstop_f"],
            wall_bounce=True,
            anim="heavy",
            label="COUP D'OBJET",
        )
        fighter.start_attack(move, self.opponent(fighter).pos)
        return [Event("prop_swing", fighter.pos, fighter.index)]

    def _prop_within_reach(self, fighter: Fighter) -> int | None:
        best, best_gap = None, self.rules.throw_reach + self.rules.body_radius
        for i, obstacle in enumerate(self.arena.obstacles):
            if not obstacle.free:
                continue
            gap = obstacle.rect.distance_to(fighter.pos)
            if gap <= best_gap:
                best, best_gap = i, gap
        return best

    def _throw(self, fighter: Fighter) -> list[Event]:
        rules = self.rules
        obstacle = self.arena.obstacles[fighter.carrying]
        fighter.carrying = None
        obstacle.carried_by, obstacle.flying = None, True
        target = self.opponent(fighter).pos
        aim = (target - fighter.pos).normalized()
        if not aim.length_sq():
            aim = fighter.facing
        # A Stand built for brute force (Star Platinum, The World...) hurls it much harder.
        # Hair and tendrils reach further than arms, but cannot put a body behind a throw.
        power = fighter.kit.strength
        if fighter.kit.prop_hold != "hands":
            power *= rules.prop_swing["wrapped_throw"]
        defn = ProjectileDef(
            speed=rules.throw_speed * power,
            radius=rules.throw_radius,
            damage=round(obstacle.throw_damage * power),
            lifetime_f=rules.throw_lifetime_f,
            hitstun_f=round(rules.throw_hitstun_f * min(power, 1.5)),
            knockback=rules.throw_knockback * power,
            hitstop_f=rules.throw_hitstop_f,
            look="prop",
            wall_bounce=power >= rules.strong_throw,
        )
        start = fighter.pos + aim * (rules.body_radius + defn.radius + 2)
        # Thrown in stopped time it flies a moment, then hangs there like the knives do.
        stop_after = rules.time_stop_projectile_flight_f if self.time_stop else None
        projectile = Projectile(
            fighter.index, start, aim * defn.speed, defn, defn.lifetime_f, stop_after=stop_after
        )
        projectile.prop = self.arena.obstacles.index(obstacle)
        projectile.key = (fighter.index, -1 - projectile.prop)
        self.projectiles.append(projectile)
        return [Event("throw", fighter.pos, fighter.index, power)]

    def _drop(self, fighter: Fighter, spot: Vec2) -> list[Event]:
        """The held prop lands on the ground at `spot` (kept inside the arena)."""
        obstacle = self.arena.obstacles[fighter.carrying]
        fighter.carrying = None
        obstacle.carried_by = None
        w, h = obstacle.rect.w, obstacle.rect.h
        center, _ = self.arena.bounds.constrain_circle(spot, max(w, h) / 2 + 1)
        obstacle.rect = Rect(center.x - w / 2, center.y - h / 2, w, h)
        return [Event("drop", center, fighter.index)]

    def _settle_props(self) -> list[Event]:
        """Thrown props break where their flight ends; broken props come back home."""
        events: list[Event] = []
        flying = {p.prop: p.pos for p in self.projectiles if p.prop is not None}
        for i, obstacle in enumerate(self.arena.obstacles):
            if obstacle.flying:
                if i in flying:
                    self._last_prop_pos[i] = flying[i]
                    continue
                spot = self._last_prop_pos.pop(i, obstacle.rect.center)
                w, h = obstacle.rect.w, obstacle.rect.h
                obstacle.shatter(Rect(spot.x - w / 2, spot.y - h / 2, w, h))
                events.append(Event("prop_break", spot))
            elif obstacle.ready_to_respawn:
                home = obstacle.home
                if all(home.distance_to(f.pos) > self.rules.body_radius for f in self.fighters):
                    obstacle.respawn()
                    events.append(Event("prop_respawn", home.center))
        return events

    # Possession -------------------------------------------------------------------------

    def _possess(self, user: Fighter, victim: Fighter, frames: int) -> list[Event]:
        """The Stand slips inside the victim: its user steers the victim's walk."""
        victim.stun_f = 0
        victim.velocity = Vec2()
        victim.buffer.clear()
        victim.set_state(State.IDLE)
        victim.possessed_f = frames
        victim.possessor = user.index
        return [Event("possessed", victim.pos, victim.index)]

    def _possession_inputs(
        self, inputs: tuple[InputFrame, InputFrame]
    ) -> tuple[InputFrame, InputFrame]:
        """While possessed, a fighter walks where its possessor pushes; the possessor
        can only let go (Stand key)."""
        frames = list(inputs)
        for victim in self.fighters:
            if victim.possessed_f <= 0 or victim.possessor is None:
                continue
            user = self.fighters[victim.possessor]
            if user.inside == victim.index:
                # A whole body in there: the host fights it by mashing anything at all.
                raw = inputs[victim.index]
                mash = sum(raw.presses(a) for a in (*ATTACK_SLOTS, "dash", "guard", "stand"))
                if mash:
                    hamon = victim.kit.style == "hamon"
                    cut = self.rules.struggle_f * (self.rules.hamon_struggle_mult if hamon else 1)
                    user.inside_f -= round(mash * cut)
                    user.expelled_by_hamon = hamon and user.inside_f <= 0
                if inputs[user.index].presses("stand"):
                    user.inside_f = 0  # the intruder lets go on its own
            elif not user.remote:
                victim.possessed_f, victim.possessor = 0, None
                continue
            frames[victim.index] = InputFrame(move=inputs[user.index].move)
            presses = inputs[user.index].presses("stand")
            frames[user.index] = InputFrame(press_counts={"stand": presses} if presses else {})
        return frames[0], frames[1]

    def _infiltrate(self, user: Fighter, victim: Fighter, move: MoveDef) -> list[Event]:
        """The user's body goes into the victim's: hidden in it, steering it, eating it."""
        events = self._possess(user, victim, move.infiltrate_f)
        user.inside = victim.index
        victim.host = True
        user.inside_f = move.infiltrate_f
        user.inside_move = move
        user.expelled_by_hamon = False
        user.velocity = Vec2()
        user.pos = victim.pos.copy()
        return events + [Event("infiltrate", victim.pos, user.index)]

    def _update_infiltration(self) -> list[Event]:
        """Whoever is inside someone: follow the host, take a bite now and then, and come
        out when the time is up, the host has fought it out, or either one falls."""
        events: list[Event] = []
        for user in self.fighters:
            if user.inside is None:
                continue
            host = self.fighters[user.inside]
            user.pos = host.pos.copy()
            if user.state != State.IDLE and user.alive:
                user.set_state(State.IDLE)  # the grab is over: the body is in there now
            user.inside_f -= 1
            move = user.inside_move
            tick = self.rules.inside_tick_f
            if move is not None and tick and user.inside_f % tick == 0 and host.alive:
                bite = round(move.inside_dps * tick / 60)
                alive = host.alive
                host.hurt(bite)
                user.hp = min(user.max_hp, user.hp + round(bite * move.drain))
                events.append(Event("drain", host.pos, host.index, bite))
                if alive and not host.alive:
                    events.append(Event("ko", host.pos, host.index))
            if user.inside_f <= 0 or not host.alive or not user.alive:
                events += self._expel(user, host)
        return events

    def _expel(self, user: Fighter, host: Fighter) -> list[Event]:
        """The body tears back out, behind the host, which staggers."""
        user.inside, user.inside_f, user.inside_move = None, 0, None
        host.possessed_f, host.possessor, host.host = 0, None, False
        out = host.pos - host.facing.normalized() * (self.rules.body_radius * 2)
        user.pos, _, _ = self.arena.constrain(out, self.rules.body_radius)
        user.facing = (host.pos - user.pos).normalized()
        if user.state not in (State.KO,):
            user.attack = None
            user.set_state(State.IDLE)
        events = [Event("infiltrate_end", user.pos, user.index)]
        if user.expelled_by_hamon:
            # Repelled by the Ripple: it burns on the way out, doubly so on the undead.
            weak = user.kit.nature in self.rules.hamon_weak_natures
            burn = round(
                self.rules.hamon_expel_damage * (self.rules.hamon_vs_weak_mult if weak else 1)
            )
            alive = user.alive
            user.hurt(burn)
            events.append(Event("hamon", user.pos, user.index, 1 if weak else 0))
            if alive and not user.alive:
                events.append(Event("ko", user.pos, user.index))
        user.expelled_by_hamon = False
        if host.alive:
            host.stun_f = self.rules.expel_stun_f
            host.set_state(State.HITSTUN)
        return events

    # Cutscenes ---------------------------------------------------------------------------

    def _confirms(self, attack: Attack) -> bool:
        """A clean hit of this attack starts its cutscene."""
        move = attack.move
        cued = move.cinematic and move.cinematic_at == "hit" and not attack.cutscene_done
        return bool(cued) and self.cutscene is None

    def _update_cage(self) -> list[Event]:
        cage = self.arena.cage
        if cage is None:
            return []
        cage.frames_left -= 1
        if cage.frames_left > 0:
            return []
        self.arena.cage = None
        return [Event("cage_end", cage.center, cage.owner)]

    @property
    def sun_active(self) -> bool:
        """The sun shines in through the arena's windows (late in the round)."""
        return bool(self.arena.sun_windows) and self.tick >= self.arena.sun_after_f

    def _apply_sunlight(self) -> list[Event]:
        """Sunlight on the floor: it burns the undead standing in it."""
        events: list[Event] = []
        active = self.sun_active
        if active and not self.dawn_announced:
            self.dawn_announced = True
            if self.arena.sun_after_f > 0:  # in broad daylight, there is no dawn to call
                events.append(Event("dawn", None))
        spread = self.arena.sun_spread(self.tick)
        for fighter in self.fighters:
            fighter.in_sun = active and fighter.alive and self.arena.in_sun(fighter.pos, spread)
            undead = fighter.kit.nature in self.rules.sun_undead_natures and not fighter.sun_proof
            if not fighter.in_sun or not undead or fighter.frozen:
                if undead and not fighter.frozen:
                    # In stopped time nothing happens at all, not even cooling down.
                    fighter.leave_the_sun()
                continue
            if fighter.burn_in_sun():
                events.append(Event("ko", fighter.pos, fighter.index))
            if self.tick % 10 == 0:
                events.append(Event("sunburn", fighter.pos, fighter.index, int(fighter.blood == 0)))
        return events

    # The arena itself ---------------------------------------------------------------------

    def _update_hazards(self) -> list[Event]:
        """What falls from the ceiling and what springs from the floor. Stopped time
        stops it too: nothing in the room moves but the one who stopped it."""
        hazards = self.arena.hazards
        if self.time_stop is not None:
            return []
        events: list[Event] = []
        for drop in hazards.drops:
            events += self._update_drop(drop)
        for zone in hazards.zones:
            events += self._update_trap_zone(zone)
        return events

    def _take_exits(self, moved: list[Event]) -> list[Event]:
        """A body slammed through a wall that gives way: the fight goes on in the arena
        behind it. Both fighters keep their place along the wall and their distance from
        it; what was flying or laid in the old room stays there."""
        hazards = self.arena.hazards
        if not hazards.exits or self.arena.elsewhere is None:
            return []
        for event in moved:
            if event.kind != "wall_bounce" or event.fighter is None:
                continue
            exit_ = next((e for e in hazards.exits if e.rect.contains(event.pos)), None)
            if exit_ is None:
                continue
            old, new = self.arena, self.arena.elsewhere(exit_.to)
            for fighter in self.fighters:
                # Out through the wall: the same place along it, the same distance from
                # it, now on the other side of it in the new arena.
                share = (fighter.pos.x - old.bounds.rect.left) / max(1.0, old.bounds.rect.w)
                depth = fighter.pos.y - old.bounds.rect.top
                spot = Vec2(
                    new.bounds.rect.left + share * new.bounds.rect.w,
                    new.bounds.rect.top + depth,
                )
                fighter.pos, _, _ = new.constrain(spot, self.rules.body_radius)
                fighter.glide = Vec2()
                fighter.carrying = None  # props belong to their room: it stays behind
            self.arena = new
            self.projectiles, self.traps, self.webs = [], [], []
            return [Event("arena_exit", event.pos, event.fighter)]
        return []

    def _update_drop(self, drop) -> list[Event]:
        defn = drop.defn
        if drop.wreck_left > 0:
            drop.wreck_left -= 1
        drop.countdown -= 1
        if drop.countdown == defn.warning_f:
            # It starts to give: over whoever's turn it is, its shadow on the floor.
            aimed = self.fighters[drop.turn % 2].pos
            drop.turn += 1
            drop.spot = min(defn.spots, key=lambda spot: (spot - aimed).length_sq())
            return [Event("hazard_warn", drop.spot.copy(), None, defn.radius)]
        if drop.countdown > 0 or drop.spot is None:
            if drop.countdown <= 0:
                drop.countdown = defn.every_f  # nobody to aim at: try again later
            return []
        spot, drop.spot = drop.spot, None
        drop.countdown = defn.every_f
        drop.wreck_at, drop.wreck_left = spot, defn.wreck_f
        events = [Event("hazard_drop", spot, None, defn.radius)]
        reach = defn.radius + self.rules.hurt_radius
        for fighter in self.fighters:
            if not fighter.alive or fighter.invincible:
                continue
            away = fighter.pos - spot
            if away.length_sq() > reach * reach:
                continue
            push = away.normalized() if away.length_sq() > 1e-6 else Vec2(1, 0)
            events += self._hazard_hit(fighter, defn.damage, defn.hitstun_f, push * defn.knockback)
        return events

    def _update_trap_zone(self, zone) -> list[Event]:
        defn = zone.defn
        zone.sprung_left = max(0, zone.sprung_left - 1)
        if zone.rearm_left > 0:
            zone.rearm_left -= 1
            return []
        for fighter in self.fighters:
            knocked = fighter.state == State.HITSTUN and fighter.velocity.length() >= defn.min_speed
            if not knocked or not fighter.alive or not defn.rect.contains(fighter.pos):
                continue
            zone.rearm_left, zone.sprung_left = defn.rearm_f, defn.rearm_f
            events = [Event("hazard_spikes", fighter.pos.copy(), fighter.index)]
            if defn.spare_style and fighter.kit.style == defn.spare_style:
                return events  # it springs, and does not bite this one
            out = fighter.pos - defn.rect.center
            push = out.normalized() if out.length_sq() > 1e-6 else Vec2(0, 1)
            return events + self._hazard_hit(
                fighter, defn.damage, defn.hitstun_f, push * defn.knockback
            )
        return []

    def _hazard_hit(self, fighter: Fighter, damage: int, hitstun_f: int, knock: Vec2) -> list:
        """The arena strikes: no guard holds against a falling chandelier."""
        alive = fighter.alive
        fighter.take_hit(damage, hitstun_f, knock, True)
        events = [Event("hit", fighter.pos.copy(), fighter.index, damage)]
        if alive and not fighter.alive:
            events.append(Event("ko", fighter.pos.copy(), fighter.index))
        return events

    def _apply_statuses(self) -> list[Event]:
        """Fire, cold and a current keep working between blows: this is their step. The
        life they take is announced now and then, not sixty times a second."""
        events: list[Event] = []
        for fighter in self.fighters:
            if fighter.frozen or not fighter.alive or not fighter.statuses.active:
                continue
            hurt = fighter.statuses.damage_this_frame()
            if hurt:
                alive = fighter.alive
                fighter.hurt(hurt)
                if alive and not fighter.alive:
                    events.append(Event("ko", fighter.pos, fighter.index))
            if self.rules.status_tick_f and self.tick % self.rules.status_tick_f == 0:
                # A beat for the view and the sound: what it is doing is read off the
                # fighter, so one event is enough however many statuses are on him.
                events.append(Event("status_tick", fighter.pos, fighter.index, hurt))
        return events

    def _update_awakenings(self) -> list[Event]:
        """Whoever is putting a mask on: count it down, and let it land."""
        for fighter in self.fighters:
            awakening = fighter.kit.awakening
            if fighter.state != State.AWAKENING or awakening is None:
                continue
            if fighter.state_f < awakening.charge_f:
                continue
            fighter.complete_awakening()
            events = [Event("awaken", fighter.pos, fighter.index)]
            if awakening.cinematic:
                events += self._start_scene(
                    awakening.cinematic,
                    fighter,
                    self.opponent(fighter),
                    awakening.cinematic_f,
                )
            return events
        return []

    def _start_scene(
        self, name: str, user: Fighter, target: Fighter, frames: int, move=None, serial: int = 0
    ) -> list[Event]:
        """Hold the fight for a cutscene. `move` carries a finishing blow; an awakening
        has none - it is the state it leaves behind that matters."""
        self.cutscene = Cutscene(name, user.index, target.index, frames, frames, move, serial)
        self.super_freeze = 0
        self.super_user = None
        self.hitstop = 0
        return [Event("cutscene_start", user.pos, user.index)]

    def _start_cutscene(self, user: Fighter, target: Fighter, attack: Attack) -> list[Event]:
        move = attack.move
        attack.cutscene_done = True
        return self._start_scene(
            move.cinematic, user, target, move.cinematic_f, move, attack.serial
        )

    def _update_cutscene(self) -> list[Event]:
        """The fight holds while the cutscene plays, then its outcome lands at once."""
        scene = self.cutscene
        scene.frames_left -= 1
        if scene.frames_left > 0:
            return []
        self.cutscene = None
        user, target = self.fighters[scene.user], self.fighters[scene.target]
        move = scene.move
        events = [Event("cutscene_end", user.pos, user.index)]
        if move is None:
            return events  # an awakening: what it changed is already done
        if move.finish_damage and target.alive:
            away = (target.pos - user.pos).normalized() if target.pos != user.pos else user.facing
            strike = Strike(
                damage=move.finish_damage,
                hitstun_f=move.finish_hitstun_f,
                blockstun_f=0,
                knockback=away * move.finish_knockback,
                wall_bounce=move.finish_wall_bounce,
                hitstop_f=12,
                source=user.pos,
                where=target.pos,
                unblockable=True,
                drain=move.finish_drain,
                key=(user.index, scene.serial),
                super_move=True,
                hamon=move.hamon,
            )
            _, strike_events = self._strike(user, target, strike)
            events += strike_events
        if move.web is not None:
            nodes, edges = web_layout(self.arena.bounds.rect, move.web)
            self.webs = [w for w in self.webs if w.owner != user.index]
            self.webs.append(Web(user.index, nodes, edges, move.web, move.web.lifetime_f))
        attack = user.attack
        if attack is not None and attack.serial == scene.serial:
            attack.frame = max(attack.frame, move.startup_f + move.active_f)  # recovery now
        return events

    def _update_webs(self) -> list[Event]:
        events: list[Event] = []
        for web in self.webs:
            if self.fighters[web.owner].frozen:
                continue
            web.life -= 1
            web.rearm -= 1
            target = self.fighters[1 - web.owner]
            if web.rearm > 0 or not target.alive:
                continue
            if web.touched_by(target.pos, self.rules.hurt_radius):
                web.rearm = web.defn.rearm_f
                for node in web.nearest_nodes(target.pos, 2):
                    direction = (target.pos - node).normalized()
                    self.projectiles += self._spawn(
                        web.owner, node - direction * 6, direction, web.defn.projectile, target.pos
                    )
                    events.append(Event("trap_triggered", node, web.owner))
        self.webs = [w for w in self.webs if w.life > 0]
        return events

    def _rush_collision(self) -> Vec2 | None:
        """Rush against rush (Ora against Muda): when a barrage reaches someone who is
        starting or throwing one too, the two meet and the duel starts, whatever the
        timing. Where they meet, or None."""
        for attacker in self.fighters:
            defender = self.opponent(attacker)
            if not (attacker.rushing and defender.rushing):
                continue
            if not (attacker.attack.move.clashable and defender.attack.move.clashable):
                continue
            other_boxes = defender.hitboxes()
            for center, radius in attacker.hitboxes():
                if self._touches(center, radius, defender) or any(
                    circles_overlap(center, radius, c, r) for c, r in other_boxes
                ):
                    return (attacker.pos + defender.pos) * 0.5
        return None

    def _detect_clash(self) -> Vec2 | None:
        """Where two attacks meet "at the same instant", or None."""
        window = self.rules.clash_window_f
        for attacker in self.fighters:
            boxes = attacker.hitboxes()
            if not boxes or not attacker.attack.move.clashable:
                continue
            defender = self.opponent(attacker)
            other = defender.attack
            if defender.frozen or defender.state != State.ATTACK or other is None:
                continue
            if not other.move.clashable or other.connected or other.countered:
                continue
            if abs(attacker.attack.active_offset - other.active_offset) > window:
                continue
            other_boxes = defender.hitboxes()
            for center, radius in boxes:
                touches = self._touches(center, radius, defender) or any(
                    circles_overlap(center, radius, c, r) for c, r in other_boxes
                )
                if touches:
                    return center
        return None

    def _start_clash(self, pos: Vec2) -> list[Event]:
        duration = self.rules.clash_duration_f
        a, b = self.fighters
        # Face off at a set distance: the two barrages meet in the middle.
        axis = (b.pos - a.pos).normalized() if (b.pos - a.pos).length_sq() else Vec2(1, 0)
        half = self.rules.clash_spacing / 2
        for fighter, side in ((a, -1), (b, 1)):
            spot = pos + axis * (side * half)
            fighter.pos, _, _ = self.arena.constrain(spot, self.rules.body_radius)
        self.clash = Clash((a.pos + b.pos) * 0.5, duration, duration)
        for fighter in self.fighters:
            fighter.enter_clash(fighter.aim_at(self.opponent(fighter).pos))
        return [Event("clash_start", self.clash.pos)]

    def _update_clash(self, inputs: tuple[InputFrame, InputFrame]) -> list[Event]:
        clash = self.clash
        clash.count(inputs)
        clash.frames_left -= 1
        if not clash.over:
            return []
        self.clash = None
        rules = self.rules
        for fighter in self.fighters:
            fighter.buffer.clear()  # mashing must not turn into attacks afterwards
        winner = clash.winner()
        if winner is None:
            for fighter in self.fighters:
                away = (fighter.pos - self.opponent(fighter).pos).normalized()
                fighter.take_hit(0, 12, away * rules.clash_tie_knockback, False)
            return [Event("clash_tie", clash.pos)]
        champion, loser = self.fighters[winner], self.fighters[1 - winner]
        damage = rules.clash_loser_damage
        direction = (loser.pos - champion.pos).normalized()
        loser.take_hit(
            damage, rules.clash_loser_hitstun_f, direction * rules.clash_loser_knockback, True
        )
        champion.set_state(State.IDLE)
        champion.gain_hh(damage * rules.hh_per_damage_dealt)
        loser.gain_hh(damage * rules.hh_per_damage_taken)
        self.hitstop = max(self.hitstop, 12)
        events = [
            Event("clash_win", clash.pos, champion.index),
            Event("hit", clash.pos, loser.index, damage),
        ]
        if loser.state == State.KO:
            events.append(Event("ko", loser.pos, loser.index))
        return events

    # Resolving one strike -----------------------------------------------------------------

    def _combo_scale(self, defender: Fighter, strike: Strike) -> float:
        """Long combos hit softer: each move after the first few deals a bit less (a rush
        counts as one move). Blows in stopped time are softened too."""
        rules = self.rules
        key = strike.key
        if key is None or key != defender.combo_key:
            defender.combo_moves += 1
            defender.combo_key = key
        extra = max(0, defender.combo_moves - rules.combo_full_moves)
        scale = max(rules.combo_min_scale, 1 - rules.combo_step * extra)
        if defender.frozen and not strike.super_move:
            scale *= rules.time_stop_damage_mult
        return scale

    def _foreseen(self, defender: Fighter, attacker: Fighter) -> bool:
        """A counter move catches any blow. A pose counter ("your next line is...") only
        catches the one it predicted: the attacker pressing the same button again."""
        if defender.state != State.POSE:
            return True
        attack = attacker.attack
        return attack is not None and attack.slot == attacker.prev_slot

    def _counter(self, defender: Fighter, attacker: Fighter) -> list[Event]:
        """A counter catches the blow: the answer comes out at once, both freeze."""
        if defender.attack is not None and defender.attack.move.counter:
            name, slot = defender.attack.move.counter, defender.attack.slot
        else:
            name, slot = defender.kit.pose_counter, ""  # called from a pose
        answer = defender.kit.move(defender.stance, name)
        defender.start_attack(answer, attacker.pos, slot)
        if attacker.attack is not None:
            attacker.attack.countered = True
        self.hitstop = max(self.hitstop, self.rules.counter_freeze_f)
        events = [Event("counter", defender.pos, defender.index)]
        if not slot:
            events.append(Event("foreseen", attacker.pos, attacker.index))
        return events

    def _strike(self, attacker: Fighter, defender: Fighter, strike: Strike) -> tuple[bool, list]:
        """Dodge, block or hit. Returns (did it touch the defender, events)."""
        rules = self.rules
        if strike.melee and defender.countering and self._foreseen(defender, attacker):
            return False, self._counter(defender, attacker)
        if defender.invincible:
            if defender.in_stylish_window():
                defender.evaded = True
                defender.gain_hh(rules.hh_stylish_gain)
                self.slowmo = rules.stylish_slowmo_f
                return False, [Event("stylish", defender.pos, defender.index)]
            return False, []
        damage = strike.damage * attacker.damage_dealt_mult * defender.damage_taken_mult
        if attacker.in_resolve:
            damage *= 1 + rules.resolve_damage_bonus
        burns = strike.hamon and defender.kit.nature in rules.hamon_weak_natures
        if burns:
            damage *= rules.hamon_vs_weak_mult
        damage = round(damage)
        sparks = [Event("hamon", strike.where, defender.index, int(burns))] if strike.hamon else []
        if not strike.unblockable and defender.guards_against(strike.source):
            chip = 0 if defender.in_resolve else round(damage * (1 - rules.guard_damage_reduction))
            broke = defender.take_block(
                chip,
                damage * rules.guard_gauge_per_damage * strike.guard_mult,
                strike.blockstun_f,
                strike.knockback * rules.block_pushback_ratio,
            )
            attacker.gain_hh(damage * rules.hh_per_damage_dealt * rules.hh_block_ratio)
            defender.gain_hh(damage * rules.hh_per_damage_taken * rules.hh_block_ratio)
            self.hitstop = max(self.hitstop, strike.hitstop_f // 2)
            events = [Event("guard_break" if broke else "block", strike.where, defender.index)]
            events += sparks
            if defender.state == State.KO:
                events.append(Event("ko", defender.pos, defender.index))
            return True, events
        damage = round(damage * self._combo_scale(defender, strike))
        armored = defender.take_hit(damage, strike.hitstun_f, strike.knockback, strike.wall_bounce)
        if burns:
            # Hamon in an undead body: the wound will not close for a while.
            defender.regen_wait = max(defender.regen_wait, rules.hamon_regen_block_f)
        if strike.drain:
            drained = round(damage * strike.drain)
            attacker.hp = min(attacker.max_hp, attacker.hp + drained)
            attacker.feed(drained)
        attacker.gain_hh(damage * rules.hh_per_damage_dealt)
        defender.gain_hh(damage * rules.hh_per_damage_taken)
        if not defender.frozen:
            self.hitstop = max(self.hitstop, strike.hitstop_f)
        events = [Event("hit", strike.where, defender.index, damage), *sparks]
        if armored:
            events.append(Event("armor", defender.pos, defender.index))
        caught = strike.status and not armored and defender.alive
        if caught and defender.statuses.apply(strike.status, strike.status_f):
            # It took: the kind of status is the kind of the event, and the value is how
            # long it will last.
            frames = defender.statuses.frames(strike.status)
            events.append(Event(f"status_{strike.status}", strike.where, defender.index, frames))
        if strike.freeze_f and not armored and defender.alive and not defender.frozen:
            defender.stun_f = max(defender.stun_f, strike.freeze_f)
            defender.iced_f = strike.freeze_f
            events.append(Event("freeze", defender.pos, defender.index, strike.freeze_f))
        if strike.drain:
            events.append(
                Event("drain", attacker.pos, attacker.index, round(damage * strike.drain))
            )
        if defender.state == State.KO:
            events.append(Event("ko", defender.pos, defender.index))
        return True, events


def _without(frame: InputFrame, actions: tuple[str, ...]) -> InputFrame:
    """The same input, minus the presses (and holds) of some actions."""
    counts = {a: n for a, n in frame.press_counts.items() if a not in actions}
    held = frozenset(a for a in frame.held if a not in actions)
    return InputFrame(frame.move, held, counts, frame.cursor, frame.stick)
