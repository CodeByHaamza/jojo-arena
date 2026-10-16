"""The Swiss castle of the Pillar Men: flagstones, snow through the arched windows,
braziers against the cold, and dawn over the Alps - all generated in code.

What makes this hall its own: it is cold (blue stone, frost creeping from the walls,
snow drifting across the floor), and the sun that comes up over the mountains fills
almost all of it, so an undead fighter runs out of shadow here faster than anywhere.
"""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.stages.base import StageDef
from jojo_arena.stages.cairo_night import HOLE, OUTLINE, _jitter, _to_pygame

STONE = (142, 150, 168)
STONE_LIGHT = (174, 182, 198)
STONE_DARK = (100, 106, 124)
IRON = (76, 78, 92)
IRON_LIGHT = (108, 112, 128)
EMBER = (255, 150, 60)
WOOD = (104, 78, 54)
WOOD_DARK = (74, 54, 38)
WINDOW_W, WINDOW_H = 24, 32
SNOWFLAKES = 26


class SwissCastleRenderer:
    def __init__(self, stage: StageDef, size: tuple[int, int] = (480, 270)) -> None:
        self.stage = stage
        self.palette = {key: tuple(value) for key, value in stage.palette.items()}
        self.size = size
        self.tick_hint = 0
        self.background = self._build_background()
        self.snow = self._build_snow()

    # Static layers --------------------------------------------------------------------

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface(self.size)
        self._draw_flagstones(surface)
        self._draw_frost(surface)
        surface.blit(self._build_frame(), (0, 0))
        self._draw_curb(surface)
        for torch in self.stage.lanterns:
            self._draw_torch(surface, torch.as_ints())
        return surface

    def _draw_flagstones(self, surface: pygame.Surface) -> None:
        """Big cut slabs, their seams dark, worn unevenly: a floor walked on for ages."""
        pal = self.palette
        rng = random.Random(1939)
        surface.fill(pal["seam"])
        bounds = self.stage.bounds.rect
        row_h = 15
        y = int(bounds.top) - row_h
        row = 0
        while y < bounds.bottom + row_h:
            # Every other row is offset half a slab, the way a mason lays them.
            x = int(bounds.left) - (9 if row % 2 else 0) - rng.randint(0, 6)
            while x < bounds.right + 6:
                width = rng.randint(17, 26)
                base = rng.choices([pal["slab"], pal["slab_light"], pal["slab_dark"]], [6, 2, 3])
                color = _jitter(base[0], rng, 3)
                slab = pygame.Rect(x + 1, y + 1, width - 2, row_h - 2)
                surface.fill(color, slab)
                surface.fill(tuple(min(255, c + 6) for c in color), (slab.x, slab.y, slab.w, 1))
                surface.fill(
                    tuple(max(0, c - 8) for c in color), (slab.x, slab.bottom - 1, slab.w, 1)
                )
                if rng.random() < 0.22:  # a chip out of the stone
                    surface.fill(
                        pal["slab_dark"], (slab.x + rng.randrange(slab.w - 3), slab.y + 4, 3, 2)
                    )
                x += width
            y += row_h
            row += 1

    def _draw_frost(self, surface: pygame.Surface) -> None:
        """Frost creeping in from the walls, and moss in the corners the sun never finds."""
        pal = self.palette
        rng = random.Random(7)
        bounds = self.stage.bounds.rect
        for _ in range(140):
            edge = rng.random()
            if edge < 0.5:
                x = rng.uniform(bounds.left, bounds.right)
                y = rng.choice([bounds.top, bounds.bottom]) + rng.uniform(-2, 10) * (
                    1 if edge < 0.25 else -1
                )
            else:
                x = rng.choice([bounds.left, bounds.right]) + rng.uniform(-2, 12) * (
                    1 if edge < 0.75 else -1
                )
                y = rng.uniform(bounds.top, bounds.bottom)
            if not (bounds.left <= x <= bounds.right and bounds.top <= y <= bounds.bottom):
                continue
            color = pal["frost"] if rng.random() < 0.7 else pal["moss"]
            surface.set_at((int(x), int(y)), color)
            if rng.random() < 0.4:
                surface.set_at((int(x) + 1, int(y)), color)

    def window_rects(self) -> list[pygame.Rect]:
        """The arched windows of the north wall, one over each patch of sunlight."""
        rects = []
        for sun in self.stage.sun_windows:
            rect = pygame.Rect(0, 0, WINDOW_W, WINDOW_H)
            rect.midbottom = (round(sun.x + sun.w / 2), 39)
            rects.append(rect)
        return rects

    def _build_frame(self) -> pygame.Surface:
        pal = self.palette
        frame = pygame.Surface(self.size)
        frame.fill(pal["frame"])
        width, _ = self.size
        # The north wall: coursed blocks, and the arched windows cut through it.
        frame.fill(pal["wall"], (0, 0, width, 40))
        rng = random.Random(21)
        for row in range(0, 40, 8):
            for x in range(-6 + (7 if (row // 8) % 2 else 0), width, 22):
                block = pygame.Rect(x + 1, row + 1, 20, 6)
                frame.fill(_jitter(pal["wall_light"], rng, 4), block)
                frame.fill(pal["wall"], (block.x, block.bottom - 1, block.w, 1))
        frame.fill(pal["trim"], (0, 36, width, 4))
        for rect in self.window_rects():
            self._draw_window(frame, rect, pal["glass_night"])
        # The south wall, in shadow: the mountain side of the hall.
        frame.fill(pal["frame_dark"], (0, 254, width, 16))
        frame.set_colorkey(HOLE)
        bounds = self.stage.bounds
        pygame.draw.rect(frame, HOLE, _to_pygame(bounds.rect), border_radius=int(bounds.radius))
        return frame

    def _draw_window(self, surface: pygame.Surface, rect: pygame.Rect, glass) -> None:
        """A tall window under a round arch, with a stone mullion down the middle."""
        surface.fill(OUTLINE, rect.inflate(4, 2))
        surface.fill(self.palette["trim"], rect.inflate(2, 0))
        pane = rect.inflate(-2, -2)
        surface.fill(glass, pane)
        pygame.draw.ellipse(surface, glass, (pane.x, pane.y - 8, pane.w, 16))
        pygame.draw.ellipse(
            surface, self.palette["trim"], (pane.x - 1, pane.y - 9, pane.w + 2, 18), 1
        )
        pygame.draw.line(
            surface,
            self.palette["trim"],
            (pane.centerx, pane.y - 6),
            (pane.centerx, pane.bottom),
            1,
        )

    def _draw_curb(self, surface: pygame.Surface) -> None:
        bounds = self.stage.bounds
        radius = int(bounds.radius)
        rect = _to_pygame(bounds.rect)
        pygame.draw.rect(surface, OUTLINE, rect.inflate(10, 10), 1, border_radius=radius + 5)
        pygame.draw.rect(
            surface, self.palette["curb"], rect.inflate(8, 8), 4, border_radius=radius + 4
        )
        pygame.draw.rect(surface, OUTLINE, rect.inflate(2, 2), 1, border_radius=radius + 1)

    def _draw_torch(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        x, y = pos
        surface.fill(OUTLINE, (x - 3, y - 2, 7, 6))
        surface.fill(IRON, (x - 2, y - 1, 5, 4))
        surface.fill(IRON_LIGHT, (x - 2, y - 1, 5, 1))
        surface.fill(WOOD_DARK, (x - 1, y - 5, 3, 4))

    def _build_snow(self) -> list[tuple[float, float, float, int]]:
        """Flakes blowing in from the north: (x, y, speed, size), looped in code."""
        rng = random.Random(1939)
        return [
            (
                rng.uniform(0, self.size[0]),
                rng.uniform(40, self.size[1]),
                rng.uniform(0.25, 0.75),
                1 if rng.random() < 0.75 else 2,
            )
            for _ in range(SNOWFLAKES)
        ]

    # Per-frame drawing ----------------------------------------------------------------

    def draw_background(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (0, 0))

    def draw_sun(
        self, surface: pygame.Surface, arena: Arena, amount: float, spread: float = 1.0
    ) -> None:
        """Dawn over the Alps: the glass catches fire, then the light walks the floor."""
        if amount <= 0:
            return
        pal = self.palette
        glass = tuple(
            round(n + (d - n) * min(1.0, amount))
            for n, d in zip(pal["glass_night"], pal["glass_dawn"], strict=True)
        )
        for rect in self.window_rects():
            self._draw_window(surface, rect, glass)
        light = pygame.Surface(self.size)  # added on top: black adds nothing
        sun = pal["sun"]

        def glow(strength: float):
            return tuple(round(c * strength) for c in sun)

        for window in arena.sun_windows:
            rect = _to_pygame(arena.sun_patch(window, spread))
            for i in range(rect.h):
                strength = 0.34 * amount * (1 - 0.45 * i / max(1, rect.h))
                light.fill(glow(strength * 0.5), (rect.x, rect.y + i, rect.w, 1))
                light.fill(glow(strength), (rect.x + 3, rect.y + i, rect.w - 6, 1))
            # Snow caught in the beam, bright against the cold stone.
            rng = random.Random(rect.x)
            for k in range(5):
                drift = (self.tick_hint * 0.4 + k * 23) % max(1, rect.h)
                x = rect.x + 4 + rng.randrange(max(1, rect.w - 8))
                light.fill(glow(0.55 * amount), (x, rect.y + round(drift), 1, 1))
        surface.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def draw_lights(self, surface: pygame.Surface, tick: int) -> None:
        """Torchlight pooling on the stone, and the snow blowing across the hall."""
        self.tick_hint = tick
        lantern = self.palette["lantern"]
        for i, torch in enumerate(self.stage.lanterns):
            flicker = 0.30 + 0.06 * math.sin(tick * 0.19 + i * 1.7)
            pos = torch.as_ints()
            blit_glow(surface, radial_glow(34, tuple(round(c * flicker) for c in lantern)), pos)
            height = 4 + round(3 * (0.5 + 0.5 * math.sin(tick * 0.33 + i * 2.2)))
            pygame.draw.polygon(
                surface,
                (255, 180, 80),
                [(pos[0] - 3, pos[1] - 4), (pos[0], pos[1] - 4 - height), (pos[0] + 3, pos[1] - 4)],
            )
            pygame.draw.polygon(
                surface,
                (255, 238, 170),
                [
                    (pos[0] - 1, pos[1] - 4),
                    (pos[0], pos[1] - 4 - height // 2),
                    (pos[0] + 1, pos[1] - 4),
                ],
            )
        self._draw_snow(surface, tick)

    def _draw_snow(self, surface: pygame.Surface, tick: int) -> None:
        frost = self.palette["frost"]
        bounds = self.stage.bounds.rect
        height = bounds.bottom - bounds.top
        for x0, y0, speed, size in self.snow:
            y = bounds.top + (y0 - bounds.top + tick * speed) % height
            x = x0 + math.sin((tick * 0.02) + y0) * 6
            if not (bounds.left < x < bounds.right):
                continue
            surface.fill(frost, (int(x), int(y), size, size))

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
        damaged = obstacle.hp < obstacle.max_hp / 2
        if obstacle.kind == "pillar":
            self._draw_pillar(surface, rect, damaged)
        elif obstacle.kind == "brazier":
            self._draw_brazier(surface, rect, damaged)
        else:
            self._draw_crate(surface, rect, damaged)

    def _shadow(self, surface, rect: pygame.Rect, grow: int = 4) -> None:
        shadow = pygame.Surface((rect.w + grow, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surface.blit(shadow, (rect.x - grow // 2, rect.bottom - 3))

    def _draw_pillar(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        """One of the pillars they slept in: a carved shaft, a face barely visible."""
        self._shadow(surface, rect, 6)
        body = pygame.Rect(rect.x, rect.y - 22, rect.w, rect.h + 22)
        surface.fill(OUTLINE, body.inflate(2, 2))
        surface.fill(STONE, body)
        surface.fill(STONE_LIGHT, (body.x + 1, body.y, 3, body.h))
        surface.fill(STONE_DARK, (body.right - 3, body.y, 2, body.h))
        # The carving: two sunken eyes and a mouth, the shape of whoever was inside.
        carve = STONE_DARK if not damaged else (86, 70, 74)
        surface.fill(carve, (body.x + 4, body.y + 7, 2, 3))
        surface.fill(carve, (body.right - 7, body.y + 7, 2, 3))
        surface.fill(carve, (body.x + 4, body.y + 13, body.w - 9, 1))
        surface.fill(STONE_LIGHT, (body.x - 1, body.y - 3, body.w + 2, 3))  # capital
        surface.fill(OUTLINE, (body.x - 2, body.y - 4, body.w + 4, 1))
        if damaged:
            for i, dy in enumerate((6, 14, 20)):
                surface.fill(OUTLINE, (body.x + 3 + i * 2, body.y + dy, 1, 4))

    def _draw_brazier(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        """An iron bowl of coals on three legs, still burning."""
        self._shadow(surface, rect)
        surface.fill(OUTLINE, rect.inflate(2, 2))
        surface.fill(IRON, rect)
        surface.fill(IRON_LIGHT, (rect.x, rect.y, rect.w, 2))
        glow = (120, 50, 20) if damaged else EMBER
        surface.fill(glow, (rect.x + 2, rect.y + 2, rect.w - 4, 3))
        if not damaged:
            surface.fill((255, 226, 160), (rect.centerx - 1, rect.y + 2, 2, 2))

    def _draw_crate(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        self._shadow(surface, rect)
        surface.fill(OUTLINE, rect.inflate(2, 2))
        surface.fill(WOOD if not damaged else WOOD_DARK, rect)
        surface.fill(WOOD_DARK, (rect.x, rect.centery, rect.w, 1))
        surface.fill(WOOD_DARK, (rect.centerx, rect.y, 1, rect.h))

    def _draw_debris(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        rect = _to_pygame(obstacle.rect)
        rng = random.Random(self.stage_index(obstacle))
        color = STONE_DARK if obstacle.kind == "pillar" else WOOD_DARK
        for _ in range(7):
            x = rect.x + rng.randrange(max(1, rect.w))
            y = rect.bottom - 3 + rng.randrange(4)
            surface.fill(color, (x, y, rng.choice((1, 2)), 1))
