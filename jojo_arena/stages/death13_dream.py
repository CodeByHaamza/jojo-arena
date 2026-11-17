"""Death 13's dream: a fairy-tale amusement park at night, a checkered floor in candy
colours, a Ferris wheel and a carousel beyond the edge, teacups, carousel horses and
balloons. Drawn in code (no image files needed)."""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.stages.base import StageDef
from jojo_arena.stages.cairo_night import OUTLINE, CairoNightRenderer, _to_pygame

CUP_COLORS = [((230, 120, 170), (250, 200, 220)), ((120, 190, 230), (210, 236, 250))]
HORSE = (240, 236, 228)
POLE = (230, 200, 90)
BALLOONS = [(240, 80, 90), (90, 170, 240), (250, 210, 80), (130, 220, 130)]


class Death13DreamRenderer(CairoNightRenderer):
    def __init__(self, stage: StageDef, size: tuple[int, int] = (480, 270)) -> None:
        super().__init__(stage, size)

    # Static layers --------------------------------------------------------------------

    def _draw_cobbles(self, surface: pygame.Surface) -> None:
        """A checkered floor in faded candy colours."""
        pal = self.palette
        size = 20
        for y in range(0, self.size[1], size):
            for x in range(0, self.size[0], size):
                tone = pal["tile_a"] if (x // size + y // size) % 2 == 0 else pal["tile_b"]
                surface.fill(tone, (x, y, size, size))
        for y in range(0, self.size[1], size):
            surface.fill(pal["tile_line"], (0, y, self.size[0], 1))

    def _draw_markings(self, surface: pygame.Surface) -> None:
        pass

    def _build_frame(self) -> pygame.Surface:
        """Beyond the edge: the night sky of a dream, a Ferris wheel and a carousel."""
        pal = self.palette
        rng = random.Random(13)
        frame = pygame.Surface(self.size)
        frame.fill(pal["frame"])
        for _ in range(60):
            frame.set_at((rng.randrange(self.size[0]), rng.randrange(40)), pal["sky_star"])
        # The Ferris wheel, top left, half hidden.
        center = (70, 30)
        pygame.draw.circle(frame, pal["frame_dark"], center, 34, 3)
        for i in range(10):
            angle = math.tau * i / 10
            end = (round(center[0] + math.cos(angle) * 34), round(center[1] + math.sin(angle) * 34))
            pygame.draw.line(frame, pal["frame_dark"], center, end, 1)
            pygame.draw.circle(frame, BALLOONS[i % 4], end, 3)
        # The carousel roof, top right.
        top = [(360, 34), (420, 6), (480, 34)]
        pygame.draw.polygon(frame, (200, 90, 130), top)
        pygame.draw.polygon(frame, OUTLINE, top, 1)
        for x in range(368, 476, 12):
            frame.fill((250, 220, 120), (x, 32, 4, 3))
        frame.set_colorkey((255, 0, 255))
        bounds = self.stage.bounds
        pygame.draw.rect(
            frame, (255, 0, 255), _to_pygame(bounds.rect), border_radius=int(bounds.radius)
        )
        return frame

    # Per-frame drawing ----------------------------------------------------------------

    def draw_floor_details(self, surface: pygame.Surface, arena: Arena) -> None:
        super().draw_floor_details(surface, arena)

    def draw_obstacle(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        if obstacle.broken:
            return
        shake = (1 if obstacle.flash % 2 else -1) if obstacle.flash else 0
        rect = _to_pygame(obstacle.rect).move(shake, 0)
        index = self.stage_index(obstacle)
        if obstacle.kind == "teacup":
            self._draw_teacup(surface, rect, index)
        elif obstacle.kind == "horse":
            self._draw_horse(surface, rect)
        else:
            self._draw_balloon(surface, rect, index)

    def _draw_teacup(self, surface: pygame.Surface, rect: pygame.Rect, index: int) -> None:
        """A spinning teacup ride: the round cup, its rim, the saucer under it."""
        body, rim = CUP_COLORS[index % len(CUP_COLORS)]
        saucer = rect.inflate(6, -6).move(0, 4)
        pygame.draw.ellipse(surface, OUTLINE, saucer.inflate(2, 2))
        pygame.draw.ellipse(surface, (220, 220, 230), saucer)
        pygame.draw.ellipse(surface, OUTLINE, rect.inflate(2, 2))
        pygame.draw.ellipse(surface, body, rect)
        pygame.draw.ellipse(surface, rim, rect.inflate(-4, -8).move(0, -3))
        pygame.draw.ellipse(surface, OUTLINE, rect.inflate(-4, -8).move(0, -3), 1)

    def _draw_horse(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """A carousel horse on its golden pole."""
        surface.fill(OUTLINE, (rect.centerx - 1, rect.top - 4, 3, rect.h + 4))
        surface.fill(POLE, (rect.centerx, rect.top - 4, 1, rect.h + 4))
        body = pygame.Rect(0, 0, rect.w, 8)
        body.center = (rect.centerx, rect.centery)
        pygame.draw.ellipse(surface, OUTLINE, body.inflate(2, 2))
        pygame.draw.ellipse(surface, HORSE, body)
        head = pygame.Rect(body.right - 4, body.top - 5, 5, 7)
        surface.fill(OUTLINE, head.inflate(2, 2))
        surface.fill(HORSE, head)
        surface.fill((210, 80, 120), (body.x + 3, body.top - 1, 5, 2))  # the saddle

    def _draw_balloon(self, surface: pygame.Surface, rect: pygame.Rect, index: int) -> None:
        color = BALLOONS[index % len(BALLOONS)]
        pygame.draw.line(surface, OUTLINE, rect.midbottom, (rect.centerx, rect.bottom + 6), 1)
        pygame.draw.ellipse(surface, OUTLINE, rect.inflate(2, 2))
        pygame.draw.ellipse(surface, color, rect)
        surface.set_at((rect.x + 2, rect.y + 2), (255, 255, 255))
