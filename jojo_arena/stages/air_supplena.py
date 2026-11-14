"""Air Supplena Island: a paved terrace over the Adriatic, the oil-soaked Hell Climb
Pillar in the middle, and a spiked pit on either side - all generated in code.

What makes it its own: the sea all around (it is an island), the black pool of oil that
only a Ripple user can stand on, and the pits that bite whoever is knocked into them.
"""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.stages.base import StageDef
from jojo_arena.stages.cairo_night import HOLE, OUTLINE, _jitter, _to_pygame

PIT = (40, 32, 34)
SPIKE = (150, 146, 152)
SPIKE_LIGHT = (206, 204, 210)
CLAY = (184, 108, 66)
CLAY_DARK = (134, 74, 46)


class AirSupplenaRenderer:
    def __init__(self, stage: StageDef, size: tuple[int, int] = (480, 270)) -> None:
        self.stage = stage
        self.palette = {key: tuple(value) for key, value in stage.palette.items()}
        self.size = size
        self.background = self._build_background()

    # Static layers --------------------------------------------------------------------

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface(self.size)
        self._draw_paving(surface)
        for zone in self.stage.trap_zones:
            self._draw_pit(surface, _to_pygame(zone.rect))
        for floor in self.stage.surfaces:
            if floor.rect is not None and floor.look == "oil":
                self._draw_oil(surface, _to_pygame(floor.rect))
        surface.blit(self._build_frame(), (0, 0))
        self._draw_curb(surface)
        for lamp in self.stage.lanterns:
            self._draw_brazier(surface, lamp.as_ints())
        return surface

    def _draw_paving(self, surface: pygame.Surface) -> None:
        """Pale stone slabs, sun-bleached and salted by the sea wind."""
        pal = self.palette
        rng = random.Random(1938)
        surface.fill(pal["seam"])
        bounds = self.stage.bounds.rect
        size = 13
        for row, y in enumerate(range(int(bounds.top) - size, int(bounds.bottom) + size, size)):
            x = int(bounds.left) - (6 if row % 2 else 0)
            while x < bounds.right + size:
                width = rng.randint(12, 18)
                base = rng.choices(
                    [pal["paving"], pal["paving_light"], pal["paving_dark"]], [6, 2, 2]
                )[0]
                color = _jitter(base, rng, 3)
                slab = pygame.Rect(x + 1, y + 1, width - 1, size - 1)
                surface.fill(color, slab)
                surface.fill(tuple(min(255, c + 7) for c in color), (slab.x, slab.y, slab.w, 1))
                x += width

    def _draw_pit(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """A sunken pit, its floor bristling with spike tips that are still down."""
        pygame.draw.rect(surface, OUTLINE, rect.inflate(4, 4), border_radius=4)
        pygame.draw.rect(surface, self.palette["cliff_dark"], rect.inflate(2, 2), border_radius=4)
        pygame.draw.rect(surface, PIT, rect, border_radius=3)
        for y in range(rect.top + 5, rect.bottom - 3, 8):
            for x in range(rect.left + 4 + (y // 8 % 2) * 4, rect.right - 3, 8):
                surface.fill(SPIKE, (x, y, 2, 2))
                surface.set_at((x, y), SPIKE_LIGHT)

    def _draw_oil(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """The pool the oil runs down into: black, with a sheen that catches the light."""
        pal = self.palette
        pygame.draw.ellipse(surface, OUTLINE, rect.inflate(4, 4))
        pygame.draw.ellipse(surface, pal["oil"], rect)
        rng = random.Random(72)
        for _ in range(16):
            x = rect.x + 8 + rng.randrange(max(1, rect.w - 16))
            y = rect.y + 6 + rng.randrange(max(1, rect.h - 12))
            surface.fill(pal["oil_sheen"], (x, y, rng.randint(3, 7), 1))

    def _build_frame(self) -> pygame.Surface:
        """The sea all around the island, and the cliff it stands on."""
        pal = self.palette
        frame = pygame.Surface(self.size)
        frame.fill(pal["sea"])
        rng = random.Random(9)
        for _ in range(180):
            x, y = rng.randrange(self.size[0]), rng.randrange(self.size[1])
            frame.fill(
                rng.choice((pal["sea_light"], pal["sea_dark"])), (x, y, rng.randint(2, 5), 1)
            )
        bounds = self.stage.bounds
        cliff = _to_pygame(bounds.rect).inflate(14, 14)
        pygame.draw.rect(
            frame, pal["foam"], cliff.inflate(4, 4), border_radius=int(bounds.radius) + 9
        )
        pygame.draw.rect(frame, pal["cliff"], cliff, border_radius=int(bounds.radius) + 7)
        pygame.draw.rect(
            frame, pal["cliff_dark"], cliff.move(0, 4), 3, border_radius=int(bounds.radius) + 7
        )
        frame.set_colorkey(HOLE)
        pygame.draw.rect(frame, HOLE, _to_pygame(bounds.rect), border_radius=int(bounds.radius))
        return frame

    def _draw_curb(self, surface: pygame.Surface) -> None:
        bounds = self.stage.bounds
        radius = int(bounds.radius)
        rect = _to_pygame(bounds.rect)
        pygame.draw.rect(
            surface, self.palette["curb"], rect.inflate(6, 6), 3, border_radius=radius + 3
        )
        pygame.draw.rect(surface, OUTLINE, rect.inflate(2, 2), 1, border_radius=radius + 1)

    def _draw_brazier(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        x, y = pos
        surface.fill(OUTLINE, (x - 4, y - 2, 9, 6))
        surface.fill(self.palette["iron"], (x - 3, y - 1, 7, 4))
        surface.fill(self.palette["iron_light"], (x - 3, y - 1, 7, 1))

    # Per-frame drawing ----------------------------------------------------------------

    def draw_background(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (0, 0))

    def draw_sun(
        self, surface: pygame.Surface, arena: Arena, amount: float, spread: float = 1.0
    ) -> None:
        """No roof here: the light comes down over the island from the north."""
        if amount <= 0:
            return
        light = pygame.Surface(self.size)
        sun = self.palette["sun"]
        for window in arena.sun_windows:
            rect = _to_pygame(arena.sun_patch(window, spread))
            for i in range(rect.h):
                strength = 0.22 * amount * (1 - 0.3 * i / max(1, rect.h))
                light.fill(tuple(round(c * strength) for c in sun), (rect.x, rect.y + i, rect.w, 1))
        surface.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def draw_lights(self, surface: pygame.Surface, tick: int) -> None:
        """Braziers on the terrace, and the oil running down the pillar, catching it."""
        lantern = self.palette["lantern"]
        for i, lamp in enumerate(self.stage.lanterns):
            flicker = 0.26 + 0.05 * math.sin(tick * 0.17 + i * 1.9)
            blit_glow(surface, radial_glow(30, tuple(round(c * flicker) for c in lantern)), lamp)
        for obstacle in self.stage_pillars():
            rect = _to_pygame(obstacle)
            drip = (tick // 3) % 10
            for k in range(3):
                x = rect.x + 4 + k * 8
                surface.fill(
                    self.palette["oil_sheen"], (x, rect.y - 30 + (drip + k * 4) % 30, 1, 3)
                )

    def stage_pillars(self) -> list:
        return [p.rect for p in self.stage.props if p.kind == "hell_pillar"]

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
        if obstacle.kind == "hell_pillar":
            self._draw_hell_pillar(surface, rect)
        elif obstacle.kind == "column":
            self._draw_column(surface, rect, obstacle.hp < obstacle.max_hp / 2)
        else:
            self._draw_amphora(surface, rect)

    def _draw_hell_pillar(self, surface, rect: pygame.Rect) -> None:
        """Twenty-four metres of stone seen from above: its top, high over the pool,
        and the oil sheeting down its sides."""
        pal = self.palette
        body = pygame.Rect(rect.x, rect.y - 34, rect.w, rect.h + 34)
        surface.fill(OUTLINE, body.inflate(2, 2))
        surface.fill(pal["marble_dark"], body)
        surface.fill(pal["marble"], (body.x + 2, body.y, body.w - 6, body.h))
        for x in range(body.x + 3, body.right - 2, 5):
            surface.fill(pal["oil"], (x, body.y + 4, 2, body.h - 6))
        surface.fill(pal["marble"], (body.x - 2, body.y - 4, body.w + 4, 5))
        surface.fill(OUTLINE, (body.x - 3, body.y - 5, body.w + 6, 1))

    def _draw_column(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        pal = self.palette
        body = pygame.Rect(rect.x, rect.y - 18, rect.w, rect.h + 18)
        surface.fill(OUTLINE, body.inflate(2, 2))
        surface.fill(pal["marble"], body)
        surface.fill(pal["marble_dark"], (body.right - 3, body.y, 2, body.h))
        for x in range(body.x + 3, body.right - 3, 3):
            surface.fill(pal["marble_dark"], (x, body.y + 2, 1, body.h - 4))
        if damaged:
            surface.fill(OUTLINE, (body.x + 4, body.y + 6, 1, 6))

    def _draw_amphora(self, surface, rect: pygame.Rect) -> None:
        pygame.draw.ellipse(surface, OUTLINE, rect.inflate(2, 2))
        pygame.draw.ellipse(surface, CLAY, rect)
        surface.fill(CLAY_DARK, (rect.x + 2, rect.bottom - 3, rect.w - 4, 2))
        surface.fill(OUTLINE, (rect.centerx - 1, rect.y - 3, 3, 3))

    def _draw_debris(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        rect = _to_pygame(obstacle.rect)
        rng = random.Random(self.stage_index(obstacle))
        color = self.palette["marble_dark"] if obstacle.kind == "column" else CLAY_DARK
        for _ in range(7):
            x = rect.x + rng.randrange(max(1, rect.w))
            y = rect.bottom - 3 + rng.randrange(4)
            surface.fill(color, (x, y, rng.choice((1, 2)), 1))
