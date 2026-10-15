"""Small drawing helpers shared by the menu screens: boxes, veils, hints, toasts."""

from __future__ import annotations

from functools import lru_cache

import pygame

from jojo_arena.engine import font

WHITE = (255, 255, 255)
GOLD = (255, 214, 90)
DIM = (150, 144, 170)
FAINT = (88, 82, 108)
BOX = (14, 11, 28, 220)
BORDER = (92, 78, 132)
OUTLINE = (23, 18, 31)
P1_COLOR = (255, 214, 90)
P2_COLOR = (110, 190, 255)


@lru_cache(maxsize=16)
def veil(size: tuple[int, int], rgba: tuple[int, int, int, int]) -> pygame.Surface:
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill(rgba)
    return surface


def draw_box(
    surface: pygame.Surface,
    rect: pygame.Rect | tuple[int, int, int, int],
    fill: tuple[int, int, int, int] = BOX,
    border: tuple[int, int, int] | None = BORDER,
) -> pygame.Rect:
    rect = pygame.Rect(rect)
    surface.blit(veil(rect.size, fill), rect.topleft)
    if border is not None:
        pygame.draw.rect(surface, border, rect, 1)
    return rect


def draw_cap(surface: pygame.Surface, label: str, pos: tuple[int, int]) -> int:
    """A key cap with a label in it. Returns its width."""
    x, y = pos
    width = font.text_width(label) + 6
    pygame.draw.rect(surface, (44, 38, 64), (x, y, width, 12))
    pygame.draw.rect(surface, (120, 108, 158), (x, y, width, 12), 1)
    surface.fill((70, 62, 96), (x + 1, y + 10, width - 2, 1))
    font.draw(surface, label, (x + 3, y + 1), WHITE, outline=None)
    return width


def draw_caps(surface: pygame.Surface, labels: tuple[str, ...], pos: tuple[int, int]) -> int:
    """Several key caps joined by "+". Returns the total width."""
    x, y = pos
    for i, label in enumerate(labels):
        if i:
            font.draw(surface, "+", (x + 2, y + 1), DIM, outline=None)
            x += 9
        x += draw_cap(surface, label, (x, y))
    return x - pos[0]


def hints_width(hints: list[tuple[str, str]]) -> int:
    width = 0
    for key, label in hints:
        width += font.text_width(key) + 6 + 4 + font.text_width(label) + 14
    return width - 14 if hints else 0


def draw_hints(surface: pygame.Surface, hints: list[tuple[str, str]], center: tuple[int, int]):
    """A row of "[KEY] action" hints, centered."""
    x = center[0] - hints_width(hints) // 2
    y = center[1]
    for key, label in hints:
        x += draw_cap(surface, key, (x, y)) + 4
        font.draw(surface, label, (x, y + 1), DIM)
        x += font.text_width(label) + 14


def draw_toast(surface: pygame.Surface, message: str, life: int, y: int = 222) -> None:
    """A short message popping up, e.g. when picking something not available yet."""
    if life <= 0:
        return
    width = font.text_width(message) + 24
    rect = pygame.Rect(0, 0, width, 20)
    rect.center = (surface.get_width() // 2, y)
    draw_box(surface, rect, (40, 26, 70, 235), GOLD)
    font.draw(surface, message, (rect.centerx, rect.y + 6), GOLD, align="center")


def draw_wrapped(
    surface: pygame.Surface,
    text: str,
    pos: tuple[int, int],
    width: int,
    color: tuple[int, int, int] = DIM,
    line_h: int = 10,
    align: str = "left",
) -> int:
    """Draw text wrapped to `width` pixels. Returns the y below the last line."""
    x, y = pos
    for line in font.wrap(text, width):
        font.draw(surface, line, (x, y), color, align=align)
        y += line_h
    return y
