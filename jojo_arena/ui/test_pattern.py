"""Debug scene: a pixel grid to check that scaling stays sharp and centered."""

from __future__ import annotations

import pygame

from jojo_arena.engine.scene import Scene


class TestPatternScene(Scene):
    def __init__(self) -> None:
        super().__init__()
        self.tick = 0

    def update(self) -> None:
        self.tick += 1

    def draw(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        for y in range(0, height, 8):
            for x in range(0, width, 8):
                shade = 40 if (x // 8 + y // 8) % 2 else 52
                surface.fill((shade, shade, shade + 12), (x, y, 8, 8))
        pygame.draw.rect(surface, (230, 60, 80), surface.get_rect(), 1)
        # One-pixel cross in the middle: must stay perfectly square once scaled.
        surface.set_at((width // 2, height // 2), (255, 255, 255))
        # A dot sweeping across the screen shows that logic steps at a steady pace.
        surface.fill((80, 200, 255), (self.tick % width, height - 12, 4, 4))
