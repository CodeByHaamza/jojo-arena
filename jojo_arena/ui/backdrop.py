"""Shared menu background for the whole saga: manga screentone, slanted bands in the
colors of a JoJo part (taking turns through the nine unless one is chosen), and menacing
ゴ drifting up both sides."""

from __future__ import annotations

import math

import pygame

from jojo_arena.characters import load_parts
from jojo_arena.engine import font
from jojo_arena.engine.sprites import Color

BASE = (16, 12, 30)
MENACE = (70, 54, 104)
NEUTRAL = ((90, 74, 150), (60, 50, 104))  # when no part data is around
CYCLE_F = 420  # each part's colors stay this long
FADE_F = 60  # then fade into the next part's
MENACE_ROWS = 5


def mix(a: Color, b: Color, t: float) -> Color:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))


class MenuBackdrop:
    def __init__(self, part: int | None = None) -> None:
        self.parts = {p.number: p for p in load_parts()}
        self.part = part  # a part number fixes the colors; None: they take turns
        self._tone: pygame.Surface | None = None
        self._vignette: pygame.Surface | None = None

    def colors(self, tick: int) -> tuple[Color, Color]:
        if not self.parts:
            return NEUTRAL
        if self.part in self.parts:
            return self.parts[self.part].colors
        numbers = sorted(self.parts)
        turn = tick // CYCLE_F
        now = self.parts[numbers[turn % len(numbers)]].colors
        then = self.parts[numbers[(turn + 1) % len(numbers)]].colors
        t = max(0, tick % CYCLE_F - (CYCLE_F - FADE_F)) / FADE_F
        return mix(now[0], then[0], t), mix(now[1], then[1], t)

    def draw(self, surface: pygame.Surface, tick: int) -> None:
        width, height = surface.get_size()
        surface.fill(BASE)
        main, second = self.colors(tick)
        # Slanted bands, like the cut of a manga panel, sliding slowly.
        layer = pygame.Surface((width, height), pygame.SRCALPHA)
        s = (tick * 0.12) % 80
        bands = [
            (main, 44, 250, 120),
            (second, 34, 392, 24),
            (second, 26, -60, 70),
        ]
        for color, alpha, x, band in bands:
            x += s
            corners = [(x, 0), (x + band, 0), (x + band - 130, height), (x - 130, height)]
            pygame.draw.polygon(layer, (*color, alpha), corners)
        surface.blit(layer, (0, 0))
        surface.blit(self._screentone((width, height)), (0, 0))
        self._draw_menace(surface, tick)
        surface.blit(self._dark_edges((width, height)), (0, 0))

    def _draw_menace(self, surface: pygame.Surface, tick: int) -> None:
        """ゴゴゴ rising along both edges, wavering a little."""
        width, height = surface.get_size()
        glyph = font.render("ゴ", MENACE, 2, outline=None)
        span = height + 60
        for i in range(MENACE_ROWS):
            y = (i * span / MENACE_ROWS - tick * 0.35) % span - 40
            sway = math.sin(tick * 0.15 + i) * 1.2
            surface.blit(glyph, (round(8 + sway), round(y)))
            surface.blit(glyph, (round(width - 8 - glyph.get_width() - sway), round(y + 30)))

    def _screentone(self, size: tuple[int, int]) -> pygame.Surface:
        """Dots that grow toward two corners, like printed manga shading."""
        if self._tone is None or self._tone.get_size() != size:
            width, height = size
            tone = pygame.Surface(size, pygame.SRCALPHA)
            reach = math.hypot(width, height) * 0.45
            for y in range(3, height, 6):
                for x in range(3 + (y // 6 % 2) * 3, width, 6):
                    near = min(math.hypot(x, y), math.hypot(width - x, height - y))
                    strength = 1 - near / reach
                    if strength > 0:
                        radius = 0.6 + 1.6 * strength
                        pygame.draw.circle(tone, (255, 255, 255, 16), (x, y), radius)
            self._tone = tone
        return self._tone

    def _dark_edges(self, size: tuple[int, int]) -> pygame.Surface:
        if self._vignette is None or self._vignette.get_size() != size:
            width, height = size
            vignette = pygame.Surface(size, pygame.SRCALPHA)
            for i in range(24):
                alpha = round(90 * (1 - i / 24) ** 2)
                pygame.draw.rect(
                    vignette, (6, 4, 14, alpha), (i, i, width - 2 * i, height - 2 * i), 1
                )
            self._vignette = vignette
        return self._vignette
