"""Closed arena with walls and destructible obstacles."""

from __future__ import annotations

from dataclasses import dataclass, field

from jojo_arena.engine.geometry import Rect, RoundedRect, Vec2, push_circle_out_of_rect


@dataclass
class Obstacle:
    kind: str
    rect: Rect
    max_hp: int
    hp: int = -1
    broken: bool = False
    flash: int = 0  # frames of "just got hit" feedback left

    FLASH_FRAMES = 8

    def __post_init__(self) -> None:
        if self.hp < 0:
            self.hp = self.max_hp

    def tick(self) -> None:
        if self.flash:
            self.flash -= 1

    @property
    def solid(self) -> bool:
        return not self.broken

    @property
    def breakable(self) -> bool:
        return self.max_hp > 0

    def damage(self, amount: float) -> bool:
        """Apply damage; return True only on the hit that breaks it."""
        if self.broken or not self.breakable:
            return False
        self.flash = self.FLASH_FRAMES
        self.hp = max(0, self.hp - round(amount))
        if self.hp == 0:
            self.broken = True
            return True
        return False


@dataclass
class Arena:
    bounds: RoundedRect
    spawns: tuple[Vec2, Vec2]
    obstacles: list[Obstacle] = field(default_factory=list)

    def constrain(self, pos: Vec2, radius: float) -> tuple[Vec2, Vec2 | None, Obstacle | None]:
        """Keep a body inside the walls and out of solid obstacles.

        Returns (new position, normal of the surface hit or None, obstacle hit or None).
        """
        normal: Vec2 | None = None
        hit: Obstacle | None = None
        for _ in range(2):  # second pass settles bodies wedged between two surfaces
            for obstacle in self.obstacles:
                if not obstacle.solid:
                    continue
                pushed = push_circle_out_of_rect(pos, radius, obstacle.rect)
                if pushed is not None:
                    pos, normal = pushed
                    hit = obstacle
            pos, wall_normal = self.bounds.constrain_circle(pos, radius)
            if wall_normal is not None:
                normal = wall_normal
        return pos, normal, hit

    def obstacle_at(self, pos: Vec2, radius: float) -> Obstacle | None:
        for obstacle in self.obstacles:
            if obstacle.solid and push_circle_out_of_rect(pos, radius, obstacle.rect):
                return obstacle
        return None

    def outside_walls(self, pos: Vec2, radius: float) -> bool:
        constrained, _ = self.bounds.constrain_circle(pos, radius)
        return constrained.distance_to(pos) > 0.01
