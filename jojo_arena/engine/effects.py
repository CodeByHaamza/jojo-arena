"""Pre-rendered light and shadow shapes.

Glows are radial gradients on black, blitted with BLEND_ADD: black adds nothing, so
only the light shows, and overlapping lights brighten each other.
"""

from __future__ import annotations

from functools import lru_cache

import pygame

Color = tuple[int, int, int]


@lru_cache(maxsize=128)
def radial_glow(radius: int, color: Color, falloff: float = 2.0) -> pygame.Surface:
    size = radius * 2 + 1
    surface = pygame.Surface((size, size))
    surface.fill((0, 0, 0))
    for r in range(radius, 0, -1):
        k = (1 - r / (radius + 1)) ** falloff
        pygame.draw.circle(surface, tuple(round(c * k) for c in color), (radius, radius), r)
    return surface


def blit_glow(target: pygame.Surface, glow: pygame.Surface, center: tuple[float, float]) -> None:
    half = glow.get_width() // 2
    target.blit(
        glow, (round(center[0]) - half, round(center[1]) - half), special_flags=pygame.BLEND_ADD
    )


@lru_cache(maxsize=32)
def ellipse_shadow(width: int, height: int, alpha: int = 110) -> pygame.Surface:
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (0, 0, 0, alpha), surface.get_rect())
    return surface


def blit_shadow(target: pygame.Surface, feet: tuple[float, float], width: int, height: int) -> None:
    shadow = ellipse_shadow(width, height)
    target.blit(shadow, (round(feet[0]) - width // 2, round(feet[1]) - height // 2))
