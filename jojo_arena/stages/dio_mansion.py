"""DIO's mansion in Cairo: cracked dark marble, a worn carpet, terracotta walls in the
dark, and the daylight outside held back by heavy curtains, all generated in code (no
image files needed)."""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.stages.cairo_night import HOLE, OUTLINE, _jitter, _to_pygame
from jojo_arena.stages.joestar_mansion import (
    STONE,
    STONE_DARK,
    STONE_LIGHT,
    JoestarMansionRenderer,
)

BRASS = (196, 156, 72)
BRASS_DARK = (128, 96, 44)
CANDLE = (240, 232, 210)
COFFIN = (58, 34, 34)
COFFIN_LIGHT = (84, 52, 48)
WINDOW_W, WINDOW_H = 24, 32


class DioMansionRenderer(JoestarMansionRenderer):
    """Built like the Joestar mansion (windows on the north wall, pillars), dressed as
    DIO's: dark marble instead of parquet, a curtain over every window."""

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface(self.size)
        self._draw_marble(surface)
        self._draw_carpet(surface)
        surface.blit(self._build_frame(), (0, 0))
        self._draw_curb(surface)
        for lamp in self.stage.lanterns:
            self._draw_sconce(surface, lamp.as_ints())
        return surface

    def _draw_marble(self, surface: pygame.Surface) -> None:
        """Big dark marble slabs, a few of them cracked: luxury gone to ruin."""
        pal = self.palette
        rng = random.Random(1989)
        surface.fill(pal["seam"])
        bounds = self.stage.bounds.rect
        size = 24
        for y in range(int(bounds.top) - size, int(bounds.bottom) + size, size):
            for x in range(int(bounds.left) - size, int(bounds.right) + size, size):
                base = rng.choices([pal["tile"], pal["tile_light"], pal["tile_dark"]], [5, 2, 3])
                color = _jitter(base[0], rng, 2)
                surface.fill(color, (x + 1, y + 1, size - 1, size - 1))
                # A vein through the stone.
                vein = tuple(min(255, c + 8) for c in color)
                vx = x + rng.randint(3, size - 4)
                for k in range(rng.randint(4, 9)):
                    surface.set_at((vx + k // 3, y + 3 + k * 2), vein)
                if rng.random() < 0.18:  # cracked
                    cx, cy = x + rng.randint(4, size - 6), y + rng.randint(4, size - 6)
                    for _ in range(rng.randint(5, 9)):
                        cx += rng.choice((-1, 0, 1))
                        cy += 1
                        surface.set_at((cx, cy), pal["seam"])

    def window_rects(self) -> list[pygame.Rect]:
        rects = []
        for sun in self.stage.sun_windows:
            rect = pygame.Rect(0, 0, WINDOW_W, WINDOW_H)
            rect.midbottom = (round(sun.x + sun.w / 2), 37)
            rects.append(rect)
        return rects

    def _build_frame(self) -> pygame.Surface:
        pal = self.palette
        frame = pygame.Surface(self.size)
        frame.fill(pal["frame"])
        width, _ = self.size
        # The north wall: terracotta panels in the dark, a tarnished gold rail.
        frame.fill(pal["wall"], (0, 0, width, 38))
        for x in range(0, width, 30):
            frame.fill(pal["wall_light"], (x + 3, 5, 24, 24))
            frame.fill(pal["wall"], (x + 5, 7, 20, 20))
        frame.fill(pal["trim"], (0, 34, width, 4))
        for rect in self.window_rects():
            self._draw_window(frame, rect, pal["glass_day"])
            self._draw_drapes(frame, rect)
        frame.fill(pal["frame_dark"], (0, 252, width, 18))
        frame.set_colorkey(HOLE)
        bounds = self.stage.bounds
        pygame.draw.rect(frame, HOLE, _to_pygame(bounds.rect), border_radius=int(bounds.radius))
        return frame

    def _draw_drapes(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """The curtain drawn across the window, as it hangs on the wall above the floor."""
        pal = self.palette
        drape = rect.inflate(4, 0)
        surface.fill(OUTLINE, drape.inflate(2, 2))
        surface.fill(pal["velvet"], drape)
        for x in range(drape.x + 2, drape.right - 1, 4):
            surface.fill(pal["velvet_dark"], (x, drape.y + 1, 1, drape.h - 2))
            surface.fill(pal["velvet_light"], (x + 1, drape.y + 1, 1, drape.h - 2))
        surface.fill(pal["trim"], (drape.x - 1, drape.y - 1, drape.w + 2, 2))

    def _draw_sconce(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        x, y = pos
        surface.fill(OUTLINE, (x - 2, y - 1, 5, 6))
        surface.fill(BRASS_DARK, (x - 1, y, 3, 4))
        surface.fill(CANDLE, (x, y - 3, 1, 3))
        surface.set_at((x, y - 4), self.palette["lantern"])

    # Per-frame drawing ----------------------------------------------------------------

    def draw_sun(
        self, surface: pygame.Surface, arena: Arena, amount: float, spread: float = 1.0
    ) -> None:
        """Daylight through every window whose curtain is down; the others stay dark."""
        if amount <= 0:
            return
        lit = arena.lit_windows()
        if not lit:
            return
        light = pygame.Surface(self.size)  # added on top: black adds nothing
        sun = self.palette["sun"]

        def glow(strength: float):
            return tuple(round(c * strength) for c in sun)

        for window in lit:
            rect = _to_pygame(arena.sun_patch(window, spread))
            for i in range(rect.h):
                strength = 0.36 * amount * (1 - 0.45 * i / rect.h)
                light.fill(glow(strength * 0.5), (rect.x, rect.y + i, rect.w, 1))
                light.fill(glow(strength), (rect.x + 3, rect.y + i, rect.w - 6, 1))
            rng = random.Random(rect.x)
            for k in range(7):
                drift = (self.tick_hint * 0.3 + k * 13) % rect.h
                x = rect.x + 4 + rng.randrange(rect.w - 8)
                light.fill(glow(0.5 * amount), (x, rect.y + round(drift), 1, 1))
        # The bare window itself, blazing.
        for window, rect in zip(arena.sun_windows, self.window_rects(), strict=False):
            if window in lit:
                self._draw_window(surface, rect, self.palette["glass_day"])
        surface.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def draw_lights(self, surface: pygame.Surface, tick: int) -> None:
        """Candlelight only: the mansion is dark."""
        self.tick_hint = tick
        lantern = self.palette["lantern"]
        for i, lamp in enumerate(self.stage.lanterns):
            flicker = 0.24 + 0.05 * math.sin(tick * 0.15 + i * 1.7)
            blit_glow(
                surface, radial_glow(34, tuple(round(c * flicker) for c in lantern)), lamp.as_ints()
            )

    def draw_obstacle(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        if obstacle.broken:
            return
        shake = (1 if obstacle.flash % 2 else -1) if obstacle.flash else 0
        rect = _to_pygame(obstacle.rect).move(shake, 0)
        damaged = obstacle.hp < obstacle.max_hp / 2
        if obstacle.kind == "pillar":
            self._draw_pillar(surface, rect, damaged)
        elif obstacle.kind == "curtain":
            self._draw_curtain(surface, rect, damaged)
        elif obstacle.kind == "coffin":
            self._draw_coffin(surface, rect, damaged)
        else:
            self._draw_candelabrum(surface, rect, damaged)

    def _draw_curtain(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        """The hem of the curtain, where it meets the floor: heavy folds of velvet."""
        pal = self.palette
        surface.fill(OUTLINE, rect.inflate(2, 2))
        surface.fill(pal["velvet"], rect)
        for x in range(rect.x + 1, rect.right - 1, 4):
            surface.fill(pal["velvet_dark"], (x, rect.y, 1, rect.h))
            surface.fill(pal["velvet_light"], (x + 1, rect.y, 1, rect.h - 1))
        surface.fill(pal["trim"], (rect.x, rect.bottom - 1, rect.w, 1))
        if damaged:  # torn: light shows through a rip
            surface.fill(pal["sun"], (rect.centerx - 1, rect.y + 1, 2, rect.h - 3))

    def _draw_coffin(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        """DIO's coffin, closed, seen from above."""
        self._shadow(surface, rect, 6)
        body = [
            (rect.x, rect.centery),
            (rect.x + 8, rect.y),
            (rect.right - 4, rect.y + 2),
            (rect.right, rect.centery),
            (rect.right - 4, rect.bottom - 2),
            (rect.x + 8, rect.bottom),
        ]
        pygame.draw.polygon(surface, OUTLINE, body)
        inner = [(x + (1 if x < rect.centerx else -1), y) for x, y in body]
        pygame.draw.polygon(surface, COFFIN, inner)
        surface.fill(COFFIN_LIGHT, (rect.x + 8, rect.y + 2, rect.w - 14, 2))
        surface.fill(BRASS, (rect.x + 12, rect.centery - 1, 6, 2))  # a cross of brass
        surface.fill(BRASS, (rect.x + 14, rect.centery - 3, 2, 6))
        if damaged:
            surface.fill(OUTLINE, (rect.right - 10, rect.y + 3, 1, 5))

    def _draw_candelabrum(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        """A tall brass candelabrum, three candles."""
        self._shadow(surface, rect, 2)
        stem = pygame.Rect(rect.centerx - 1, rect.y - 8, 2, rect.h + 6)
        surface.fill(OUTLINE, stem.inflate(2, 2))
        surface.fill(BRASS, stem)
        surface.fill(OUTLINE, (rect.x - 1, rect.y - 9, rect.w + 2, 3))
        surface.fill(BRASS_DARK, (rect.x, rect.y - 8, rect.w, 1))
        for dx in (0, rect.w // 2, rect.w - 1):
            surface.fill(CANDLE, (rect.x + dx, rect.y - 12, 1, 3))
            surface.set_at((rect.x + dx, rect.y - 13), self.palette["lantern"])
        if damaged:
            surface.fill(OUTLINE, (stem.x, stem.y + 4, 2, 1))

    def _draw_debris(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        if obstacle.kind == "curtain":
            # Torn down: the velvet in a heap at the foot of the window.
            pal = self.palette
            rect = _to_pygame(obstacle.rect)
            heap = pygame.Rect(rect.x - 2, rect.bottom, rect.w + 4, 5)
            pygame.draw.ellipse(surface, OUTLINE, heap.inflate(2, 2))
            pygame.draw.ellipse(surface, pal["velvet_dark"], heap)
            pygame.draw.ellipse(surface, pal["velvet"], heap.inflate(-6, -2))
            return
        rng = random.Random(self.stage_index(obstacle))
        rect = _to_pygame(obstacle.rect)
        colors = {
            "pillar": [STONE, STONE_LIGHT, STONE_DARK],
            "coffin": [COFFIN, COFFIN_LIGHT, BRASS],
        }.get(obstacle.kind, [BRASS, BRASS_DARK, CANDLE])
        for _ in range(10 if obstacle.kind in ("pillar", "coffin") else 5):
            x = rng.randint(rect.x - 6, rect.right + 4)
            y = rng.randint(rect.y - 2, rect.bottom + 3)
            w, h = (rng.randint(3, 6), 2) if rng.random() < 0.5 else (2, rng.randint(2, 4))
            surface.fill(OUTLINE, (x - 1, y - 1, w + 2, h + 2))
            surface.fill(rng.choice(colors), (x, y, w, h))
