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
    throwable: bool = False  # can be picked up and thrown
    throw_damage: int = 0
    respawn_f: int = 0  # once broken, back in its place after this long (0 = never)
    home: Rect | None = None  # where it stands at the start, and comes back to
    respawn_left: int = 0
    carried_by: int | None = None  # index of the fighter holding it over their head
    flying: bool = False  # thrown: a projectile carries it

    FLASH_FRAMES = 8

    def __post_init__(self) -> None:
        if self.hp < 0:
            self.hp = self.max_hp
        if self.home is None:
            self.home = self.rect

    def tick(self) -> None:
        if self.flash:
            self.flash -= 1
        if self.broken and self.respawn_f and self.respawn_left > 0:
            self.respawn_left -= 1

    @property
    def solid(self) -> bool:
        return not self.broken and self.carried_by is None and not self.flying

    @property
    def free(self) -> bool:
        """Lying in the arena, whole, ready to be picked up."""
        return self.throwable and self.solid

    def shatter(self, at: Rect | None = None) -> None:
        """Broken to pieces (thrown, or smashed), maybe somewhere else than its home."""
        self.rect = at or self.rect
        self.hp, self.broken, self.flying, self.carried_by = 0, True, False, None
        self.respawn_left = self.respawn_f

    @property
    def ready_to_respawn(self) -> bool:
        return self.broken and self.respawn_f > 0 and self.respawn_left <= 0

    def respawn(self) -> None:
        self.rect, self.hp, self.broken, self.flash = self.home, self.max_hp, False, 0

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
            self.shatter()
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
