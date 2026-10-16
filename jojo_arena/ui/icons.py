"""Small pixel-art pictures from assets/icons/ (part emblems, glossary icons).

A missing icon is drawn as a small placeholder diamond, so data can name an icon before
it is drawn. The drawings live in tools/icons/ (python tools/make_icons.py).
"""

from __future__ import annotations

import pygame

from jojo_arena.engine.sprites import shade
from jojo_arena.paths import ASSETS_DIR

ICONS_DIR = ASSETS_DIR / "icons"
PLACEHOLDER = (150, 130, 200)
OUTLINE = (23, 18, 31)
TAB_W, TAB_H, TAB_GAP = 15, 13, 2

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


def draw_part_tabs(
    surface: pygame.Surface,
    parts: dict,
    numbers: list[int],
    current: int,
    filled: set[int],
    y: int,
) -> None:
    """A row of tabs, one per part (PartDef by number), each with its emblem; the current
    one in its color, the parts in `filled` lit, the others dim."""
    count = len(numbers)
    x = surface.get_width() // 2 - (count * TAB_W + (count - 1) * TAB_GAP) // 2
    for number in numbers:
        rect = pygame.Rect(x, y, TAB_W, TAB_H)
        part = parts.get(number)
        if number == current and part is not None:
            surface.fill(shade(part.colors[0], -40), rect)
            pygame.draw.rect(surface, shade(part.colors[0], 70), rect, 1)
        else:
            surface.fill((20, 16, 34), rect)
            pygame.draw.rect(surface, (60, 52, 84), rect, 1)
        if part is not None:
            alpha = 255 if number in filled or number == current else 90
            draw_icon(surface, part.emblem, rect.center, center=True, alpha=alpha)
        x += TAB_W + TAB_GAP
