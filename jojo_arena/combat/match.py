"""One fight between two fighters in an arena: the deterministic simulation.

`Match.step` takes both players' inputs for one 1/60 s step and returns what happened.
Nothing here reads devices, the clock or the screen, so the same inputs always give
the same fight (tests, replays, and later online play rely on it).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from jojo_arena.combat import interactions
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.clash import Clash
from jojo_arena.combat.cutscene import Cutscene
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import Attack, Fighter, State
from jojo_arena.combat.kit import Kit, ProjectileDef
from jojo_arena.combat.projectile import Projectile
from jojo_arena.combat.rules import Rules
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
        self.cutscene: Cutscene | None = None
        self.hitstop = 0
        self.slowmo = 0  # steps left at half speed (Stylish Evade)
        self.super_freeze = 0  # steps left of a super move's flash
        self.super_user: int | None = None
        self.clash: Clash | None = None
        self.time_stop: interactions.TimeStop | None = None
        self.time_stops_endured = [0, 0]  # per fighter, for the time stopper rule
        self.tick = 0

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
                if event.kind in ("hha", "gha"):
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
        for fighter in self.fighters:
            if not fighter.frozen:
                events += fighter.integrate(self.arena)
        for fighter in self.fighters:
            if fighter.possessed_f > 0 and fighter.possessor is not None:
                # The Stand is inside the possessed body and moves with it.
                self.fighters[fighter.possessor].remote_pos = fighter.pos.copy()
        self._separate_bodies()
        self._release_attacks()
        events += self._update_projectiles()
        events += self._update_traps()
        events += self._update_webs()
        events += self._resolve_melee()
        events += self._resolve_projectile_hits()
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
                events += interactions.start_time_stop(self, fighter, move.time_stop_f)
        return events

    # Bodies -----------------------------------------------------------------------------

    def _separate_bodies(self) -> None:
        a, b = self.fighters
        if not (a.alive and b.alive) or State.DASH in (a.state, b.state):
            return  # dashes go through the opponent
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
                direction = (target - start).normalized()
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
            if self.fighters[trap.owner].frozen:
                kept.append(trap)
                continue
            trap.life -= 1
            target = self.fighters[1 - trap.owner]
            if target.alive and trap.touched_by(target.pos, self.rules.hurt_radius):
                aim = trap.pos.copy()
                direction = (target.pos - aim).normalized()
                self.projectiles += self._spawn(
                    trap.owner, aim - direction * 6, direction, trap.defn.projectile, target.pos
                )
                events.append(Event("trap_triggered", trap.pos, trap.owner))
            elif trap.life > 0:
                kept.append(trap)
        self.traps = kept
        return events

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
            events += projectile.update(self.arena)
        live = [p for p in self.projectiles if p.alive and self._projectile_moves(p)]
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
            if not target.alive or not self._projectile_moves(projectile):
                continue
            if not self._touches(projectile.pos, projectile.radius, target):
                continue
            defn = projectile.defn
            strike = Strike(
                damage=defn.damage,
                hitstun_f=defn.hitstun_f,
                blockstun_f=defn.blockstun_f or round(defn.hitstun_f * self.rules.blockstun_ratio),
                knockback=projectile.velocity.normalized() * defn.knockback,
                wall_bounce=defn.wall_bounce,
                hitstop_f=defn.hitstop_f,
                source=projectile.pos - projectile.velocity * 4,
                where=projectile.pos,
                key=projectile.key,
            )
            landed, strike_events = self._strike(self.fighters[projectile.owner], target, strike)
            events += strike_events
            if landed:
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
                damage=damage,
                hitstun_f=move.hitstun_f,
                blockstun_f=move.blockstun_f or round(move.hitstun_f * self.rules.blockstun_ratio),
                knockback=direction.normalized() * knockback,
                wall_bounce=wall_bounce,
                hitstop_f=move.hitstop_f,
                source=attacker.pos,
                where=center,
                unblockable=move.unblockable,
                drain=move.drain,
                melee=True,
                guard_mult=move.guard_damage,
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
        power = fighter.kit.strength
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
        projectile = Projectile(fighter.index, start, aim * defn.speed, defn, defn.lifetime_f)
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
            if not user.remote:
                victim.possessed_f, victim.possessor = 0, None
                continue
            frames[victim.index] = InputFrame(move=inputs[user.index].move)
            presses = inputs[user.index].presses("stand")
            frames[user.index] = InputFrame(press_counts={"stand": presses} if presses else {})
        return frames[0], frames[1]

    # Cutscenes ---------------------------------------------------------------------------

    def _confirms(self, attack: Attack) -> bool:
        """A clean hit of this attack starts its cutscene."""
        move = attack.move
        cued = move.cinematic and move.cinematic_at == "hit" and not attack.cutscene_done
        return bool(cued) and self.cutscene is None

    def _start_cutscene(self, user: Fighter, target: Fighter, attack: Attack) -> list[Event]:
        move = attack.move
        attack.cutscene_done = True
        self.cutscene = Cutscene(
            move.cinematic,
            user.index,
            target.index,
            move.cinematic_f,
            move.cinematic_f,
            move,
            attack.serial,
        )
        self.super_freeze = 0
        self.super_user = None
        self.hitstop = 0
        return [Event("cutscene_start", user.pos, user.index)]

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
                key=(user.index, scene.serial),
                super_move=True,
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

    def _counter(self, defender: Fighter, attacker: Fighter) -> list[Event]:
        """A counter catches the blow: the answer comes out at once, both freeze."""
        answer = defender.kit.move(defender.stance, defender.attack.move.counter)
        defender.start_attack(answer, attacker.pos, defender.attack.slot)
        if attacker.attack is not None:
            attacker.attack.countered = True
        self.hitstop = max(self.hitstop, self.rules.counter_freeze_f)
        return [Event("counter", defender.pos, defender.index)]

    def _strike(self, attacker: Fighter, defender: Fighter, strike: Strike) -> tuple[bool, list]:
        """Dodge, block or hit. Returns (did it touch the defender, events)."""
        rules = self.rules
        if strike.melee and defender.countering:
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
        damage = round(damage)
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
            if defender.state == State.KO:
                events.append(Event("ko", defender.pos, defender.index))
            return True, events
        damage = round(damage * self._combo_scale(defender, strike))
        armored = defender.take_hit(damage, strike.hitstun_f, strike.knockback, strike.wall_bounce)
        if strike.drain:
            attacker.hp = min(attacker.max_hp, attacker.hp + round(damage * strike.drain))
        attacker.gain_hh(damage * rules.hh_per_damage_dealt)
        defender.gain_hh(damage * rules.hh_per_damage_taken)
        if not defender.frozen:
            self.hitstop = max(self.hitstop, strike.hitstop_f)
        events = [Event("hit", strike.where, defender.index, damage)]
        if armored:
            events.append(Event("armor", defender.pos, defender.index))
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
