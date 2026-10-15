"""One fight between two fighters in an arena: the deterministic simulation.

`Match.step` takes both players' inputs for one 1/60 s step and returns what happened.
Nothing here reads devices, the clock or the screen, so the same inputs always give
the same fight (tests, replays, and later online play rely on it).
"""

from __future__ import annotations

from jojo_arena.combat.arena import Arena
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.combat.kit import Kit
from jojo_arena.combat.projectile import Projectile
from jojo_arena.combat.rules import Rules
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Vec2, circles_overlap


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
        self.tick = 0

    def opponent(self, fighter: Fighter) -> Fighter:
        return self.fighters[1 - fighter.index]

    # Main step ------------------------------------------------------------------------

    def step(self, inputs: tuple[InputFrame, InputFrame]) -> list[Event]:
        self.tick += 1
        for fighter, frame in zip(self.fighters, inputs, strict=True):
            fighter.remember_presses(frame)
        if self.hitstop > 0:
            # Impact freeze: everything holds still for a few frames.
            self.hitstop -= 1
            return []
        events: list[Event] = []
        for fighter, frame in zip(self.fighters, inputs, strict=True):
            fighter.control(frame, self.opponent(fighter).pos)
        for fighter in self.fighters:
            events += fighter.integrate(self.arena)
        self._separate_bodies()
        self._fire_projectiles()
        events += self._update_projectiles()
        events += self._resolve_melee()
        events += self._resolve_projectile_hits()
        for fighter in self.fighters:
            fighter.advance()
        for obstacle in self.arena.obstacles:
            obstacle.tick()
        return events

    # Bodies -----------------------------------------------------------------------------

    def _separate_bodies(self) -> None:
        a, b = self.fighters
        if not (a.alive and b.alive):
            return
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
            if circles_overlap(
                projectile.pos, projectile.radius, target.pos, self.rules.hurt_radius
            ):
                projectile.alive = False
                defn = projectile.defn
                direction = projectile.velocity.normalized()
                events += self._hit(
                    self.fighters[projectile.owner],
                    target,
                    defn.damage,
                    defn.hitstun_f,
                    direction * defn.knockback,
                    False,
                    defn.hitstop_f,
                    projectile.pos,
                )
        self.projectiles = [p for p in self.projectiles if p.alive]
        return events

    # Melee ------------------------------------------------------------------------------

    def _resolve_melee(self) -> list[Event]:
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
            attack.connected = True
            move = attack.move
            events += self._hit(
                attacker,
                defender,
                move.damage,
                move.hitstun_f,
                attack.aim * move.knockback,
                move.wall_bounce,
                move.hitstop_f,
                center,
            )
        return events

    def _hit(
        self,
        attacker: Fighter,
        defender: Fighter,
        damage: int,
        hitstun_f: int,
        knockback: Vec2,
        wall_bounce: bool,
        hitstop_f: int,
        where: Vec2,
    ) -> list[Event]:
        defender.take_hit(damage, hitstun_f, knockback, wall_bounce)
        self.hitstop = max(self.hitstop, hitstop_f)
        events = [Event("hit", where, defender.index, damage)]
        if defender.state == State.KO:
            events.append(Event("ko", defender.pos, defender.index))
        return events
