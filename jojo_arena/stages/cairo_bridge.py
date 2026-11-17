"""The Cairo bridge at night: an asphalt roadway between two railings, the Nile black
below, a car burning by the railing, an oil tanker on its side, a hole torn in the deck.
Drawn in code (no image files needed)."""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.stages.base import StageDef
from jojo_arena.stages.cairo_night import OUTLINE, CairoNightRenderer, _to_pygame

STEEL = (120, 124, 138)
STEEL_DARK = (78, 80, 94)
STEEL_LIGHT = (176, 180, 192)
TANK = (196, 196, 200)
TANK_DARK = (140, 140, 148)
STRIPE = (190, 64, 52)
CAR = (110, 40, 36)
CAR_DARK = (70, 26, 24)
FLAME = (255, 170, 60)
FLAME_CORE = (255, 236, 170)
BARREL = (150, 70, 44)
BARREL_DARK = (104, 46, 30)


class CairoBridgeRenderer(CairoNightRenderer):
    def __init__(self, stage: StageDef, size: tuple[int, int] = (480, 270)) -> None:
        super().__init__(stage, size)

    # Static layers --------------------------------------------------------------------

    def _draw_cobbles(self, surface: pygame.Surface) -> None:
        """The roadway: worn asphalt, its lane markings, the hole in the deck."""
        pal = self.palette
        rng = random.Random(9)
        surface.fill(pal["road"])
        for _ in range(900):
            x, y = rng.randrange(self.size[0]), rng.randrange(self.size[1])
            surface.set_at((x, y), pal["road_light"] if rng.random() < 0.5 else pal["road_dark"])
        bounds = _to_pygame(self.stage.bounds.rect)
        middle = bounds.centery
        for x in range(bounds.left + 8, bounds.right - 8, 24):
            surface.fill(pal["marking"], (x, middle - 1, 12, 2))
        for zone in self.stage.trap_zones:
            self._draw_gap(surface, _to_pygame(zone.rect))

    def _draw_markings(self, surface: pygame.Surface) -> None:
        pass

    def _draw_gap(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """The torn deck: the girders and the black water far below, ragged edges."""
        surface.fill((8, 10, 20), rect)
        for x in range(rect.left + 3, rect.right - 2, 9):
            surface.fill(STEEL_DARK, (x, rect.top, 3, rect.h))
        surface.fill(STEEL, (rect.left, rect.centery, rect.w, 3))
        rng = random.Random(rect.x)
        for x in range(rect.left - 2, rect.right + 2, 3):
            depth = rng.randint(1, 4)
            surface.fill(OUTLINE, (x, rect.bottom - 1, 3, depth))

    def _build_frame(self) -> pygame.Surface:
        """Beyond the railings: the Nile, black, and the lights of Cairo on the far bank."""
        pal = self.palette
        rng = random.Random(17)
        frame = pygame.Surface(self.size)
        frame.fill(pal["water"])
        for y in range(0, self.size[1], 3):
            for x in range(rng.randrange(6), self.size[0], rng.randint(18, 40)):
                frame.fill(pal["water_light"], (x, y, rng.randint(4, 10), 1))
        x = 0
        while x < self.size[0]:  # the far bank, along the top
            width = rng.randint(20, 48)
            height = rng.randint(8, 26)
            frame.fill(pal["frame_dark"], (x, 30 - height, width - 2, height))
            for wx in range(x + 3, x + width - 5, 6):
                for wy in range(32 - height, 28, 5):
                    if rng.random() < 0.22:
                        frame.fill(pal["window"], (wx, wy, 2, 2))
            x += width
        frame.set_colorkey((255, 0, 255))
        pygame.draw.rect(frame, (255, 0, 255), _to_pygame(self.stage.bounds.rect))
        return frame

    def _draw_curb(self, surface: pygame.Surface) -> None:
        """The railings, top and bottom: a rail on posts."""
        pal = self.palette
        rect = _to_pygame(self.stage.bounds.rect)
        for y in (rect.top - 6, rect.bottom + 2):
            surface.fill(OUTLINE, (rect.left - 4, y - 1, rect.w + 8, 6))
            surface.fill(pal["rail"], (rect.left - 3, y, rect.w + 6, 2))
            surface.fill(pal["curb"], (rect.left - 3, y + 2, rect.w + 6, 2))
            for x in range(rect.left, rect.right, 16):
                surface.fill(OUTLINE, (x - 1, y - 3, 4, 8))
                surface.fill(STEEL_LIGHT, (x, y - 2, 2, 6))

    # Per-frame drawing ----------------------------------------------------------------

    def draw_lights(self, surface: pygame.Surface, tick: int) -> None:
        super().draw_lights(surface, tick)
        # The burning car lights the road round it.
        for prop in self.stage.props:
            if prop.kind == "car":
                center = _to_pygame(prop.rect).center
                flicker = 0.45 + 0.08 * math.sin(tick * 0.3)
                color = tuple(round(c * flicker) for c in self.palette["fire"])
                blit_glow(surface, radial_glow(46, color), center)

    def draw_floor_details(self, surface: pygame.Surface, arena: Arena) -> None:
        super().draw_floor_details(surface, arena)

    def draw_obstacle(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        if obstacle.broken:
            return
        shake = (1 if obstacle.flash % 2 else -1) if obstacle.flash else 0
        rect = _to_pygame(obstacle.rect).move(shake, 0)
        if obstacle.kind == "car":
            self._draw_car(surface, rect)
        elif obstacle.kind == "tanker":
            self._draw_tanker(surface, rect)
        else:
            self._draw_barrel(surface, rect)

    def _draw_car(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """A car seen from above, burning: the roof caved in, flames out of the windows."""
        pygame.draw.rect(surface, OUTLINE, rect.inflate(2, 2), border_radius=4)
        pygame.draw.rect(surface, CAR, rect, border_radius=4)
        roof = rect.inflate(-14, -6)
        surface.fill(CAR_DARK, roof)
        tick = pygame.time.get_ticks() // 90
        for i in range(4):
            x = roof.left + 2 + i * (roof.w - 4) // 3
            h = 4 + (tick + i * 3) % 4
            pygame.draw.polygon(
                surface,
                FLAME,
                [(x - 3, roof.centery), (x, roof.centery - h - 4), (x + 3, roof.centery)],
            )
            surface.set_at((x, roof.centery - 2), FLAME_CORE)

    def _draw_tanker(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """An oil tanker on its side: the round tank, a red stripe, the cab crushed."""
        tank = rect.inflate(-10, -2).move(5, 0)
        cab = pygame.Rect(rect.left, rect.top + 3, 12, rect.h - 6)
        for part in (tank, cab):
            pygame.draw.rect(surface, OUTLINE, part.inflate(2, 2), border_radius=6)
        pygame.draw.rect(surface, TANK, tank, border_radius=6)
        surface.fill(TANK_DARK, (tank.x, tank.bottom - 6, tank.w, 5))
        surface.fill(STRIPE, (tank.x + 3, tank.centery - 1, tank.w - 6, 3))
        pygame.draw.rect(surface, STEEL, cab, border_radius=3)
        surface.fill((40, 50, 70), cab.inflate(-6, -8))

    def _draw_barrel(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.ellipse(surface, OUTLINE, rect.inflate(2, 2))
        pygame.draw.ellipse(surface, BARREL, rect)
        pygame.draw.ellipse(surface, BARREL_DARK, rect.inflate(-4, -4), 1)
