"""Projectiles: fly straight, stop on walls and props, cancel each other."""

from __future__ import annotations

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

    @property
    def radius(self) -> float:
        return self.defn.radius

    def update(self, arena: Arena) -> list[Event]:
        self.pos = self.pos + self.velocity
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return [Event("projectile_fade", self.pos)]
        if arena.outside_walls(self.pos, self.radius):
            self.alive = False
            return [Event("projectile_wall", self.pos)]
        obstacle = arena.obstacle_at(self.pos, self.radius)
        if obstacle is not None:
            self.alive = False
            broke = obstacle.damage(self.defn.damage)
            return [Event("prop_break" if broke else "projectile_wall", self.pos)]
        return []
