"""Projectiles: fly straight, stop on walls and props, cancel each other."""

from __future__ import annotations

import math
from dataclasses import dataclass

from jojo_arena.combat.arena import Arena
from jojo_arena.combat.events import Event
from jojo_arena.combat.kit import ProjectileDef
from jojo_arena.engine.geometry import Vec2


@dataclass
class Projectile:
    owner: int
    pos: Vec2
    velocity: Vec2
    defn: ProjectileDef
    life: int
    alive: bool = True
    # Thrown in stopped time: flies this many more steps, then hangs in the air until
    # time moves again (None = normal flight).
    stop_after: int | None = None
    key: tuple | None = None  # the move that fired it, for combo scaling
    prop: int | None = None  # index of the arena prop being thrown, if it is one
    hamon: bool = False  # carries Hamon, like the move that fired it
    returning: bool = False  # a boomerang on its way back
    spent: bool = False  # a boomerang that already hit: it only flies back now
    boost: float = 1.0  # damage multiplier of that move

    @property
    def radius(self) -> float:
        return self.defn.radius

    @property
    def hanging(self) -> bool:
        return self.stop_after == 0

    def steer(self, target: Vec2, max_turn: float) -> None:
        """Turn toward `target` by at most `max_turn` radians (homing)."""
        speed = self.velocity.length()
        if speed == 0:
            return
        current = self.velocity.angle()
        wanted = (target - self.pos).angle()
        delta = (wanted - current + math.pi) % (2 * math.pi) - math.pi
        turn = max(-max_turn, min(max_turn, delta))
        self.velocity = Vec2.from_angle(current + turn, speed)

    def update(self, arena: Arena) -> list[Event]:
        if self.stop_after is not None:
            if self.stop_after <= 0:
                return []
            self.stop_after -= 1
        self.pos = self.pos + self.velocity
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return [Event("projectile_fade", self.pos)]
        if arena.outside_walls(self.pos, self.radius):
            if self.defn.returns:
                return self.turn_back()  # a boomerang glances off and comes home
            self.alive = False
            return [Event("projectile_wall", self.pos)]
        obstacle = arena.obstacle_at(self.pos, self.radius)
        if obstacle is not None:
            broke = obstacle.damage(self.defn.damage)
            if self.defn.returns and not self.returning:
                return [*self.turn_back(), Event("prop_break" if broke else "prop_hit", self.pos)]
            self.alive = False
            return [Event("prop_break" if broke else "projectile_wall", self.pos)]
        return []

    def turn_back(self) -> list[Event]:
        """A boomerang starts back toward its owner, with time enough to get there."""
        if not self.returning:
            self.returning = True
            self.velocity = self.velocity * -1
            self.life = self.defn.lifetime_f
            return [Event("projectile_wall", self.pos)]
        return []
