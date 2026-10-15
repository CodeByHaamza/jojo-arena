"""One fight between two fighters in an arena: the deterministic simulation.

`Match.step` takes both players' inputs for one 1/60 s step and returns what happened.
Nothing here reads devices, the clock or the screen, so the same inputs always give
the same fight (tests, replays, and later online play rely on it).
"""

from __future__ import annotations

from dataclasses import dataclass

from jojo_arena.combat.arena import Arena
from jojo_arena.combat.clash import Clash
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.combat.kit import Kit
from jojo_arena.combat.projectile import Projectile
from jojo_arena.combat.rules import Rules
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


class Match:
    def __init__(self, kits: tuple[Kit, Kit], rules: Rules, arena: Arena) -> None:
        self.rules = rules
        self.arena = arena
        self.fighters = [
            Fighter(0, kits[0], rules, arena.spawns[0], Vec2(1, 0)),
            Fighter(1, kits[1], rules, arena.spawns[1], Vec2(-1, 0)),
        ]
        self.projectiles: list[Projectile] = []
        self.hitstop = 0
        self.slowmo = 0  # steps left at half speed (Stylish Evade)
        self.super_freeze = 0  # steps left of the Heart Heat Attack flash
        self.super_user: int | None = None
        self.clash: Clash | None = None
        self.tick = 0

    def opponent(self, fighter: Fighter) -> Fighter:
        return self.fighters[1 - fighter.index]

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
        for fighter, frame in zip(self.fighters, inputs, strict=True):
            for event in fighter.control(frame, self.opponent(fighter).pos):
                if event.kind == "hha":
                    self.super_freeze = self.rules.super_freeze_f
                    self.super_user = fighter.index
                elif event.kind == "flash_cancel":
                    self.hitstop = max(self.hitstop, self.rules.flash_cancel_freeze_f)
                events.append(event)
        for fighter in self.fighters:
            events += fighter.integrate(self.arena)
        self._separate_bodies()
        self._fire_projectiles()
        events += self._update_projectiles()
        events += self._resolve_melee()
        events += self._resolve_projectile_hits()
        for fighter in self.fighters:
            fighter.advance()
            if fighter.in_resolve and not fighter.resolve_announced:
                fighter.resolve_announced = True
                events.append(Event("resolve", fighter.pos, fighter.index))
        for obstacle in self.arena.obstacles:
            obstacle.tick()
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
        push = normal * ((2 * r - distance) / 2)
        a.pos, _, _ = self.arena.constrain(a.pos + push, r)
        b.pos, _, _ = self.arena.constrain(b.pos - push, r)

    # Projectiles ------------------------------------------------------------------------

    def _fire_projectiles(self) -> None:
        for fighter in self.fighters:
            attack = fighter.attack
            if attack is None or attack.fired or not attack.active:
                continue
            defn = attack.move.projectile
            if defn is None:
                continue
            attack.fired = True
            start = fighter.pos + attack.aim * (self.rules.body_radius + defn.radius + 2)
            self.projectiles.append(
                Projectile(fighter.index, start, attack.aim * defn.speed, defn, defn.lifetime_f)
            )

    def _update_projectiles(self) -> list[Event]:
        events: list[Event] = []
        for projectile in self.projectiles:
            events += projectile.update(self.arena)
        live = [p for p in self.projectiles if p.alive]
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

    def _resolve_projectile_hits(self) -> list[Event]:
        events: list[Event] = []
        for projectile in self.projectiles:
            target = self.fighters[1 - projectile.owner]
            if not target.alive:
                continue
            if not circles_overlap(
                projectile.pos, projectile.radius, target.pos, self.rules.hurt_radius
            ):
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
            hitbox = attacker.hitbox()
            if hitbox is None:
                continue
            center, radius = hitbox
            for i, obstacle in enumerate(self.arena.obstacles):
                if i in attacker.attack.props_hit or not obstacle.solid:
                    continue
                if obstacle.rect.inflate(radius).contains(center):
                    attacker.attack.props_hit.add(i)
                    broke = obstacle.damage(attacker.attack.move.damage)
                    events.append(Event("prop_break" if broke else "prop_hit", center))
            defender = self.opponent(attacker)
            if defender.alive and circles_overlap(
                center, radius, defender.pos, self.rules.hurt_radius
            ):
                hits.append((attacker, attacker.attack, defender, center))
        # Collect first, apply after: two hits on the same frame both land (a trade),
        # even though the first one interrupts the second attacker's move.
        for attacker, attack, defender, center in hits:
            move = attack.move
            # Moves centered on the body (reach 0) push away from the attacker.
            direction = attack.aim if move.reach > 0 else (defender.pos - attacker.pos)
            strike = Strike(
                damage=move.damage,
                hitstun_f=move.hitstun_f,
                blockstun_f=move.blockstun_f or round(move.hitstun_f * self.rules.blockstun_ratio),
                knockback=direction.normalized() * move.knockback,
                wall_bounce=move.wall_bounce,
                hitstop_f=move.hitstop_f,
                source=attacker.pos,
                where=center,
            )
            landed, strike_events = self._strike(attacker, defender, strike)
            events += strike_events
            if landed:
                attack.connected = True
        return events

    # Clash -------------------------------------------------------------------------------

    def _detect_clash(self) -> Vec2 | None:
        """Where two attacks meet "at the same instant", or None."""
        window = self.rules.clash_window_f
        for attacker in self.fighters:
            hitbox = attacker.hitbox()
            if hitbox is None or not attacker.attack.move.clashable:
                continue
            defender = self.opponent(attacker)
            other = defender.attack
            if defender.state != State.ATTACK or other is None:
                continue
            if not other.move.clashable or other.connected:
                continue
            if abs(attacker.attack.active_offset - other.active_offset) > window:
                continue
            center, radius = hitbox
            touches = circles_overlap(center, radius, defender.pos, self.rules.hurt_radius)
            other_box = defender.hitbox()
            if other_box is not None:
                touches = touches or circles_overlap(center, radius, *other_box)
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
        damage = strike.damage
        if attacker.in_resolve:
            damage = round(damage * (1 + rules.resolve_damage_bonus))
        if defender.guards_against(strike.source):
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
        attacker.gain_hh(damage * rules.hh_per_damage_dealt)
        defender.gain_hh(damage * rules.hh_per_damage_taken)
        self.hitstop = max(self.hitstop, strike.hitstop_f)
        events = [Event("hit", strike.where, defender.index, damage)]
        if defender.state == State.KO:
            events.append(Event("ko", defender.pos, defender.index))
        return True, events
