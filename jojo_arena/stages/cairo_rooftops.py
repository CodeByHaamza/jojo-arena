"""The rooftops of Cairo at night: a flat roof of concrete slabs, holes torn through it,
the neon "AIR" sign along its edge, a clock tower in one corner and a water tower in the
other. Drawn in code (no image files needed)."""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.stages.base import StageDef
from jojo_arena.stages.cairo_night import OUTLINE, CairoNightRenderer, _to_pygame

STONE = (176, 160, 136)
STONE_DARK = (130, 116, 98)
STONE_LIGHT = (206, 192, 168)
CLOCK_FACE = (232, 226, 206)
TANK = (120, 130, 144)
TANK_DARK = (86, 94, 108)
TANK_LIGHT = (164, 174, 188)
VENT = (138, 140, 150)


class CairoRooftopsRenderer(CairoNightRenderer):
    def __init__(self, stage: StageDef, size: tuple[int, int] = (480, 270)) -> None:
        super().__init__(stage, size)

    # Static layers --------------------------------------------------------------------

    def _draw_cobbles(self, surface: pygame.Surface) -> None:
        """The roof: concrete slabs, their seams, stains; the holes torn through it."""
        pal = self.palette
        rng = random.Random(23)
        surface.fill(pal["roof"])
        for y in range(0, self.size[1], 22):
            for x in range(0, self.size[0], 30):
                tone = pal["roof_light"] if (x // 30 + y // 22) % 3 == 0 else pal["roof_dark"]
                surface.fill(tone, (x + 1, y + 1, 28, 20))
                surface.fill(pal["seam"], (x, y, 30, 1))
                surface.fill(pal["seam"], (x, y, 1, 22))
        for _ in range(14):
            x, y = rng.randrange(self.size[0]), rng.randrange(self.size[1])
            pygame.draw.ellipse(
                surface, pal["roof_dark"], (x, y, rng.randint(6, 16), rng.randint(3, 7))
            )
        for zone in self.stage.trap_zones:
            if zone.look == "roof_hole":
                self._draw_hole(surface, _to_pygame(zone.rect))

    def _draw_markings(self, surface: pygame.Surface) -> None:
        pass

    def _draw_hole(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """A hole through the roof: the dark room below, ragged edges, broken rebar."""
        pygame.draw.ellipse(surface, OUTLINE, rect.inflate(4, 4))
        pygame.draw.ellipse(surface, (16, 12, 20), rect)
        rng = random.Random(rect.x * 7 + rect.y)
        for _ in range(6):
            angle = rng.uniform(0, math.tau)
            x = rect.centerx + math.cos(angle) * rect.w * 0.45
            y = rect.centery + math.sin(angle) * rect.h * 0.45
            pygame.draw.line(
                surface, (110, 70, 50), (round(x), round(y)), (rect.centerx, rect.centery), 1
            )

    def _draw_curb(self, surface: pygame.Surface) -> None:
        """The parapet round the roof; the neon sign standing on its top edge."""
        rect = _to_pygame(self.stage.bounds.rect)
        pygame.draw.rect(surface, OUTLINE, rect.inflate(10, 10), 1)
        pygame.draw.rect(surface, self.palette["curb"], rect.inflate(8, 8), 4)
        pygame.draw.rect(surface, OUTLINE, rect.inflate(2, 2), 1)
        for zone in self.stage.trap_zones:
            if zone.look == "neon":
                self._draw_sign_frame(surface, _to_pygame(zone.rect))

    def _draw_sign_frame(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """The scaffold of the sign, behind its letters."""
        surface.fill(OUTLINE, (rect.left, rect.top - 6, rect.w, 4))
        for x in range(rect.left + 6, rect.right, 20):
            surface.fill((70, 70, 80), (x, rect.top - 6, 2, 10))

    # Per-frame drawing ----------------------------------------------------------------

    def draw_lights(self, surface: pygame.Surface, tick: int) -> None:
        super().draw_lights(surface, tick)
        for zone in self.stage.trap_zones:
            if zone.look == "neon":
                rect = _to_pygame(zone.rect)
                on = (tick // 40) % 9 != 0  # it fails, now and then
                color = self.palette["neon"] if on else self.palette["neon_dim"]
                self._draw_letters(surface, rect, color)
                if on:
                    glow = tuple(c // 4 for c in self.palette["neon"])
                    blit_glow(surface, radial_glow(60, glow), rect.center)

    def _draw_letters(self, surface: pygame.Surface, rect: pygame.Rect, color) -> None:
        """A, I, R in neon tubes."""
        top, bottom = rect.top - 4, rect.top + 10
        x = rect.centerx - 30
        # A
        pygame.draw.line(surface, color, (x, bottom), (x + 7, top), 2)
        pygame.draw.line(surface, color, (x + 7, top), (x + 14, bottom), 2)
        pygame.draw.line(surface, color, (x + 3, bottom - 5), (x + 11, bottom - 5), 2)
        # I
        pygame.draw.line(surface, color, (x + 28, top), (x + 28, bottom), 2)
        # R
        r = x + 42
        pygame.draw.line(surface, color, (r, top), (r, bottom), 2)
        pygame.draw.arc(surface, color, (r - 6, top, 14, 9), -math.pi / 2, math.pi / 2, 2)
        pygame.draw.line(surface, color, (r + 2, top + 8), (r + 9, bottom), 2)

    def draw_floor_details(self, surface: pygame.Surface, arena: Arena) -> None:
        super().draw_floor_details(surface, arena)

    def draw_obstacle(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        if obstacle.broken:
            return
        shake = (1 if obstacle.flash % 2 else -1) if obstacle.flash else 0
        rect = _to_pygame(obstacle.rect).move(shake, 0)
        damaged = obstacle.hp < obstacle.max_hp / 2
        if obstacle.kind == "clock_tower":
            self._draw_clock_tower(surface, rect, damaged)
        elif obstacle.kind == "water_tower":
            self._draw_water_tower(surface, rect)
        elif obstacle.kind == "vent":
            self._draw_vent(surface, rect)
        else:
            self._draw_crate(surface, rect, damaged)

    def _draw_clock_tower(self, surface: pygame.Surface, rect: pygame.Rect, damaged: bool) -> None:
        """The clock tower seen from above at an angle: stone, the clock face, cracks."""
        body = rect.inflate(0, 10).move(0, -10)
        surface.fill(OUTLINE, body.inflate(2, 2))
        surface.fill(STONE, body)
        surface.fill(STONE_LIGHT, (body.x + 2, body.y, 4, body.h))
        surface.fill(STONE_DARK, (body.right - 4, body.y, 4, body.h))
        face = (body.centerx, body.y + 10)
        pygame.draw.circle(surface, OUTLINE, face, 8)
        pygame.draw.circle(surface, CLOCK_FACE, face, 7)
        pygame.draw.line(surface, OUTLINE, face, (face[0], face[1] - 5), 1)
        pygame.draw.line(surface, OUTLINE, face, (face[0] + 4, face[1]), 1)
        if damaged:
            for i in range(3):
                x = body.x + 5 + i * 8
                pygame.draw.line(surface, OUTLINE, (x, body.bottom - 2), (x + 4, body.centery), 1)

    def _draw_water_tower(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """A water tower on its legs: the round tank, the struts."""
        for x in (rect.left + 4, rect.right - 6):
            surface.fill(OUTLINE, (x - 1, rect.centery, 4, rect.h // 2 + 1))
            surface.fill(TANK_DARK, (x, rect.centery, 2, rect.h // 2))
        tank = rect.inflate(-2, -12).move(0, -6)
        pygame.draw.ellipse(surface, OUTLINE, tank.inflate(2, 2))
        pygame.draw.ellipse(surface, TANK, tank)
        pygame.draw.ellipse(surface, TANK_LIGHT, tank.inflate(-12, -10).move(-3, -2))

    def _draw_vent(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        surface.fill(OUTLINE, rect.inflate(2, 2))
        surface.fill(VENT, rect)
        for y in range(rect.top + 2, rect.bottom - 1, 3):
            surface.fill((90, 92, 100), (rect.left + 2, y, rect.w - 4, 1))
