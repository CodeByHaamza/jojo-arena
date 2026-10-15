"""Shared menu background: the arena at night, dimmed, with its lanterns flickering."""

from __future__ import annotations

import pygame

from jojo_arena.stages import load_stage, stage_renderer


class MenuBackdrop:
    def __init__(self, stage_id: str = "cairo_night") -> None:
        self.renderer = stage_renderer(load_stage(stage_id))
        self._veil: pygame.Surface | None = None

    def draw(self, surface: pygame.Surface, tick: int) -> None:
        self.renderer.draw_background(surface)
        self.renderer.draw_lights(surface, tick)
        if self._veil is None or self._veil.get_size() != surface.get_size():
            self._veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self._veil.fill((10, 8, 24, 150))
        surface.blit(self._veil, (0, 0))
