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
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import Attack, Fighter, State
from jojo_arena.combat.kit import Kit, ProjectileDef
from jojo_arena.combat.projectile import Projectile
from jojo_arena.combat.rules import Rules
from jojo_arena.combat.traps import Trap
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Vec2, circles_overlap


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
        """Moments that pause the round timer: clash, super flash, stopped time."""
        return self.clash is not None or self.super_freeze > 0 or self.time_stop is not None

    # Main step ------------------------------------------------------------------------

    def step(self, inputs: tuple[InputFrame, InputFrame]) -> list[Event]:
        self.tick += 1
        for fighter, frame in zip(self.fighters, inputs, strict=True):
            fighter.remember_presses(frame)
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
            if not fighter.frozen:
                events += fighter.integrate(self.arena)
        self._separate_bodies()
        self._release_attacks()
        events += self._update_projectiles()
        events += self._update_traps()
        events += self._resolve_melee()
        events += self._resolve_projectile_hits()
        for fighter in self.fighters:
            if fighter.frozen:
                continue
            fighter.advance()
            if fighter.in_resolve and not fighter.resolve_announced:
                fighter.resolve_announced = True
                events.append(Event("resolve", fighter.pos, fighter.index))
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
                attack.fired = True
                target = self.opponent(fighter).pos
                self.projectiles += self._spawn(
                    fighter.index, fighter.pos, attack.aim, move.projectile, target
                )
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
        pos, _, _ = self.arena.constrain(fighter.pos + attack.aim * defn.distance, defn.radius)
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
                wall_bounce=False,
                hitstop_f=defn.hitstop_f,
                source=projectile.pos - projectile.velocity * 4,
                where=projectile.pos,
            )
            landed, strike_events = self._strike(self.fighters[projectile.owner], target, strike)
            events += strike_events
            if landed:
                projectile.alive = False  # dodged projectiles keep flying
        self.projectiles = [p for p in self.projectiles if p.alive]
        return events

    # Melee ------------------------------------------------------------------------------

    def _resolve_melee(self) -> list[Event]:
        clash_pos = self._detect_clash()
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
            if move.hits > 1 and attack.last_hit:
                if move.last_knockback is not None:
                    knockback = move.last_knockback
                wall_bounce = wall_bounce or move.last_wall_bounce
            strike = Strike(
                damage=move.damage,
                hitstun_f=move.hitstun_f,
                blockstun_f=move.blockstun_f or round(move.hitstun_f * self.rules.blockstun_ratio),
                knockback=direction.normalized() * knockback,
                wall_bounce=wall_bounce,
                hitstop_f=move.hitstop_f,
                source=attacker.pos,
                where=center,
                unblockable=move.unblockable,
                drain=move.drain,
            )
            landed, strike_events = self._strike(attacker, defender, strike)
            events += strike_events
            if landed:
                attack.connected = True
                attack.hits_done += 1
        return events

    # Clash -------------------------------------------------------------------------------

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
            if not other.move.clashable or other.connected:
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
        self.clash = Clash(pos, duration, duration)
        for fighter in self.fighters:
            fighter.enter_clash(fighter.aim_at(self.opponent(fighter).pos))
        return [Event("clash_start", pos)]

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

    def _strike(self, attacker: Fighter, defender: Fighter, strike: Strike) -> tuple[bool, list]:
        """Dodge, block or hit. Returns (did it touch the defender, events)."""
        rules = self.rules
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
                damage * rules.guard_gauge_per_damage,
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
        defender.take_hit(damage, strike.hitstun_f, strike.knockback, strike.wall_bounce)
        if strike.drain:
            attacker.hp = min(attacker.max_hp, attacker.hp + round(damage * strike.drain))
        attacker.gain_hh(damage * rules.hh_per_damage_dealt)
        defender.gain_hh(damage * rules.hh_per_damage_taken)
        if not defender.frozen:
            self.hitstop = max(self.hitstop, strike.hitstop_f)
        events = [Event("hit", strike.where, defender.index, damage)]
        if strike.drain:
            events.append(
                Event("drain", attacker.pos, attacker.index, round(damage * strike.drain))
            )
        if defender.state == State.KO:
            events.append(Event("ko", defender.pos, defender.index))
        return True, events
