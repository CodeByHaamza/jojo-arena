"""St. Moritz: the snowed-in courtyard outside Gessler's hotel, the Pillar Men's hideout,
with the Alps behind it - all generated in code.

What makes it its own: it is outside. The whole floor is packed snow that nobody keeps
their footing on (only the path dug to the door grips a little), the hotel's lit
windows watch from the north, and dawn, once it breaks, leaves no shade at all.
"""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.stages.base import StageDef
from jojo_arena.stages.cairo_night import HOLE, OUTLINE, _to_pygame

SNOWFLAKES = 34
CARROT = (232, 120, 40)


class StMoritzRenderer:
    def __init__(self, stage: StageDef, size: tuple[int, int] = (480, 270)) -> None:
        self.stage = stage
        self.palette = {key: tuple(value) for key, value in stage.palette.items()}
        self.size = size
        self.background = self._build_background()
        rng = random.Random(1939)
        self.snow = [
            (rng.uniform(0, size[0]), rng.uniform(0, size[1]), rng.uniform(0.3, 0.8))
            for _ in range(SNOWFLAKES)
        ]

    # Static layers --------------------------------------------------------------------

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface(self.size)
        self._draw_snowfield(surface)
        for floor in self.stage.surfaces:
            if floor.rect is not None and floor.look == "path":
                self._draw_path(surface, _to_pygame(floor.rect))
        surface.blit(self._build_frame(), (0, 0))
        self._draw_curb(surface)
        for lamp in self.stage.lanterns:
            x, y = lamp.as_ints()
            surface.fill(OUTLINE, (x - 2, y - 3, 5, 6))
            surface.fill(self.palette["lantern"], (x - 1, y - 2, 3, 4))
        return surface

    def _draw_snowfield(self, surface: pygame.Surface) -> None:
        """Packed snow: soft drifts, footprints, and the blue of its shadows."""
        pal = self.palette
        surface.fill(pal["snow"])
        rng = random.Random(44)
        bounds = self.stage.bounds.rect
        for _ in range(60):
            x = rng.uniform(bounds.left, bounds.right)
            y = rng.uniform(bounds.top, bounds.bottom)
            w = rng.randint(10, 28)
            pygame.draw.ellipse(surface, pal["snow_shade"], (x, y + 2, w, 3))
            pygame.draw.ellipse(surface, pal["snow_light"], (x + 1, y, w - 2, 3))
        for _ in range(40):  # footprints, in pairs
            x = rng.uniform(bounds.left + 10, bounds.right - 10)
            y = rng.uniform(bounds.top + 10, bounds.bottom - 10)
            surface.fill(pal["snow_shade"], (x, y, 2, 3))
            surface.fill(pal["snow_shade"], (x + 4, y + 3, 2, 3))

    def _draw_path(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """The path shovelled to the hotel door: wet stone showing through."""
        pal = self.palette
        surface.fill(pal["path"], rect)
        rng = random.Random(3)
        for _ in range(50):
            x = rect.x + rng.randrange(rect.w)
            y = rect.y + rng.randrange(rect.h)
            surface.fill(pal["path_dark"], (x, y, rng.randint(2, 5), 1))
        surface.fill(pal["snow_shade"], (rect.x - 2, rect.y, 2, rect.h))
        surface.fill(pal["snow_shade"], (rect.right, rect.y, 2, rect.h))

    def _build_frame(self) -> pygame.Surface:
        """The night sky, the mountains, and the hotel's front along the north side."""
        pal = self.palette
        frame = pygame.Surface(self.size)
        frame.fill(pal["sky"])
        width, height = self.size
        rng = random.Random(1291)
        points = [(0, 40)]
        for x in range(0, width + 40, 40):
            points.append((x, rng.randint(8, 26)))
        points.append((width, 40))
        pygame.draw.polygon(frame, pal["mountain"], points)
        for x, y in points[1:-1]:
            pygame.draw.polygon(
                frame, pal["mountain_snow"], [(x - 6, y + 6), (x, y), (x + 6, y + 6)]
            )
        hotel = pygame.Rect(150, 14, 180, 32)
        frame.fill(OUTLINE, hotel.inflate(2, 2))
        frame.fill(pal["wall"], hotel)
        frame.fill(pal["roof"], (hotel.x - 4, hotel.y - 6, hotel.w + 8, 7))
        frame.fill(pal["snow_light"], (hotel.x - 4, hotel.y - 8, hotel.w + 8, 3))
        for i, x in enumerate(range(hotel.x + 8, hotel.right - 8, 16)):
            lit = i % 3 != 1
            frame.fill(pal["window_lit"] if lit else pal["window_dark"], (x, hotel.y + 8, 6, 8))
        frame.fill(pal["wood_dark"], (232, 30, 16, 16))  # the door
        frame.fill(pal["snow"], (0, height - 18, width, 18))
        frame.set_colorkey(HOLE)
        bounds = self.stage.bounds
        pygame.draw.rect(frame, HOLE, _to_pygame(bounds.rect), border_radius=int(bounds.radius))
        return frame

    def _draw_curb(self, surface: pygame.Surface) -> None:
        bounds = self.stage.bounds
        radius = int(bounds.radius)
        rect = _to_pygame(bounds.rect)
        pygame.draw.rect(
            surface, self.palette["curb"], rect.inflate(8, 8), 4, border_radius=radius + 4
        )
        pygame.draw.rect(surface, OUTLINE, rect.inflate(2, 2), 1, border_radius=radius + 1)

    # Per-frame drawing ----------------------------------------------------------------

    def draw_background(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (0, 0))

    def draw_sun(
        self, surface: pygame.Surface, arena: Arena, amount: float, spread: float = 1.0
    ) -> None:
        """Dawn over the Alps: pink, then gold, down the whole courtyard."""
        if amount <= 0:
            return
        light = pygame.Surface(self.size)
        sun = self.palette["sun"]
        for window in arena.sun_windows:
            rect = _to_pygame(arena.sun_patch(window, spread))
            for i in range(rect.h):
                strength = 0.2 * amount * (1 - 0.35 * i / max(1, rect.h))
                light.fill(tuple(round(c * strength) for c in sun), (rect.x, rect.y + i, rect.w, 1))
        surface.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def draw_lights(self, surface: pygame.Surface, tick: int) -> None:
        lantern = self.palette["lantern"]
        for i, lamp in enumerate(self.stage.lanterns):
            flicker = 0.24 + 0.04 * math.sin(tick * 0.13 + i * 2.1)
            blit_glow(surface, radial_glow(30, tuple(round(c * flicker) for c in lantern)), lamp)
        width, height = self.size
        for x0, y0, speed in self.snow:
            y = (y0 + tick * speed) % height
            x = (x0 + math.sin(tick * 0.02 + y0) * 8) % width
            surface.fill(self.palette["snow_light"], (int(x), int(y), 1, 1))

    def draw_floor_details(self, surface: pygame.Surface, arena: Arena) -> None:
        for obstacle in arena.obstacles:
            if obstacle.broken:
                self._draw_debris(surface, obstacle)

    def stage_index(self, obstacle: Obstacle) -> int:
        return int(obstacle.rect.x * 7 + obstacle.rect.y * 13)

    def draw_obstacle(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        if obstacle.broken:
            return
        shake = (1 if obstacle.flash % 2 else -1) if obstacle.flash else 0
        rect = _to_pygame(obstacle.rect).move(shake, 0)
        if obstacle.kind == "tree":
            self._draw_tree(surface, rect)
        elif obstacle.kind == "snowman":
            self._draw_snowman(surface, rect)
        else:
            self._draw_barrel(surface, rect)

    def _draw_tree(self, surface, rect: pygame.Rect) -> None:
        """A snowed-on pine: three tiers of branches seen from above and the side."""
        pal = self.palette
        cx, base = rect.centerx, rect.bottom
        for tier, (half, top) in enumerate(((12, 30), (9, 20), (6, 11))):
            points = [
                (cx - half, base - top + 12),
                (cx, base - top - 4),
                (cx + half, base - top + 12),
            ]
            pygame.draw.polygon(surface, OUTLINE, [(x, y + 1) for x, y in points])
            pygame.draw.polygon(surface, pal["pine"] if tier % 2 else pal["pine_dark"], points)
            surface.fill(pal["snow_light"], (cx - half // 2, base - top + 2, half, 2))
        surface.fill(pal["wood_dark"], (cx - 1, base - 2, 3, 3))

    def _draw_snowman(self, surface, rect: pygame.Rect) -> None:
        pal = self.palette
        pygame.draw.circle(surface, OUTLINE, (rect.centerx, rect.bottom - 4), 6)
        pygame.draw.circle(surface, pal["snow_light"], (rect.centerx, rect.bottom - 4), 5)
        pygame.draw.circle(surface, OUTLINE, (rect.centerx, rect.bottom - 12), 4)
        pygame.draw.circle(surface, pal["snow_light"], (rect.centerx, rect.bottom - 12), 3)
        surface.fill(CARROT, (rect.centerx + 1, rect.bottom - 12, 3, 1))

    def _draw_barrel(self, surface, rect: pygame.Rect) -> None:
        pal = self.palette
        surface.fill(OUTLINE, rect.inflate(2, 2))
        surface.fill(pal["wood"], rect)
        surface.fill(pal["wood_dark"], (rect.x, rect.y + 2, rect.w, 1))
        surface.fill(pal["wood_dark"], (rect.x, rect.bottom - 3, rect.w, 1))
        surface.fill(pal["snow_light"], (rect.x, rect.y, rect.w, 2))

    def _draw_debris(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        rect = _to_pygame(obstacle.rect)
        rng = random.Random(self.stage_index(obstacle))
        color = (
            self.palette["wood_dark"] if obstacle.kind == "barrel" else self.palette["snow_shade"]
        )
        for _ in range(7):
            x = rect.x + rng.randrange(max(1, rect.w))
            y = rect.bottom - 3 + rng.randrange(4)
            surface.fill(color, (x, y, rng.choice((1, 2)), 1))
