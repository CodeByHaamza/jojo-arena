"""Small pixel-art pictures from assets/icons/ (part emblems, glossary icons).

A missing icon is drawn as a small placeholder diamond, so data can name an icon before
it is drawn. The drawings live in tools/icons/ (python tools/make_icons.py).
"""

from __future__ import annotations

import pygame

from jojo_arena.paths import ASSETS_DIR

ICONS_DIR = ASSETS_DIR / "icons"
PLACEHOLDER = (150, 130, 200)
OUTLINE = (23, 18, 31)

_cache: dict[str, pygame.Surface | None] = {}


def icon(name: str) -> pygame.Surface | None:
    if name not in _cache:
        path = ICONS_DIR / f"{name}.png"
        image = pygame.image.load(str(path)) if name and path.exists() else None
        if image is not None and pygame.display.get_surface() is not None:
            image = image.convert_alpha()
        _cache[name] = image
    return _cache[name]


def placeholder(size: int, color: tuple[int, int, int] = PLACEHOLDER) -> pygame.Surface:
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    half = (size - 1) / 2
    corners = [(half, 0), (size - 1, half), (half, size - 1), (0, half)]
    pygame.draw.polygon(image, color, corners)
    pygame.draw.polygon(image, OUTLINE, corners, 1)
    return image


def draw_icon(
    surface: pygame.Surface,
    name: str,
    pos: tuple[int, int],
    scale: int = 1,
    size: int = 9,
    center: bool = False,
    alpha: int = 255,
) -> pygame.Rect:
    """Draw an icon with its top-left corner (or its center) at `pos`."""
    image = icon(name) or placeholder(size)
    if scale != 1:
        image = pygame.transform.scale_by(image, scale)
    if alpha != 255:
        image = image.copy()
        image.set_alpha(alpha)
    rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
    return surface.blit(image, rect)
