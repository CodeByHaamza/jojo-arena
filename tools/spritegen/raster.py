"""Pixel shapes and the style-A renderer: shading from the top-left, dark outline."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field

import pygame

CELL = 48
OUTLINE = (23, 18, 31)

Pixel = tuple[int, int]
Point = tuple[float, float]
Color = tuple[int, int, int]


def disc(cx: float, cy: float, r: float) -> set[Pixel]:
    return {
        (x, y)
        for x in range(math.floor(cx - r) - 1, math.ceil(cx + r) + 1)
        for y in range(math.floor(cy - r) - 1, math.ceil(cy + r) + 1)
        if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r
    }


def capsule(x1: float, y1: float, x2: float, y2: float, r: float) -> set[Pixel]:
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx * dx + dy * dy or 1e-9
    pixels = set()
    for x in range(math.floor(min(x1, x2) - r) - 1, math.ceil(max(x1, x2) + r) + 1):
        for y in range(math.floor(min(y1, y2) - r) - 1, math.ceil(max(y1, y2) + r) + 1):
            px, py = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length_sq))
            if (px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2 <= r * r:
                pixels.add((x, y))
    return pixels


def polygon(points: list[Point]) -> set[Pixel]:
    """Pixels whose center lies inside the polygon (even-odd rule)."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    pixels = set()
    for y in range(math.floor(min(ys)), math.ceil(max(ys)) + 1):
        for x in range(math.floor(min(xs)), math.ceil(max(xs)) + 1):
            px, py = x + 0.5, y + 0.5
            inside = False
            for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1], strict=True):
                crosses = (y1 > py) != (y2 > py)
                if crosses and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
            if inside:
                pixels.add((x, y))
    return pixels


def rect(x0: float, y0: float, x1: float, y1: float) -> set[Pixel]:
    """Every pixel from (x0, y0) to (x1, y1), both included."""
    return {
        (x, y)
        for x in range(round(min(x0, x1)), round(max(x0, x1)) + 1)
        for y in range(round(min(y0, y1)), round(max(y0, y1)) + 1)
    }


def points(coords: Iterable[Point]) -> set[Pixel]:
    return {(round(x), round(y)) for x, y in coords}


@dataclass
class Part:
    material: str
    pixels: set[Pixel]
    z: float = 0.0  # drawing order: higher is in front
    highlight: set[Pixel] = field(default_factory=set)
    tone: int | None = None  # fixed tone (thin details that shading would turn dark)
    flat: Color | None = None  # exact color, ignoring the palette


def render(
    parts: list[Part], palette: dict[str, list[Color]], outline: Color = OUTLINE
) -> pygame.Surface:
    """Draw parts back to front, shade each one from the top-left, then outline."""
    ordered = [part for _, part in sorted(enumerate(parts), key=lambda e: (e[1].z, e[0]))]
    owner: dict[Pixel, int] = {}
    for rank, part in enumerate(ordered):
        for p in part.pixels:
            if 0 <= p[0] < CELL and 0 <= p[1] < CELL:
                owner[p] = rank
    surface = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    for (x, y), rank in owner.items():
        part = ordered[rank]
        if part.flat is not None:
            surface.set_at((x, y), part.flat)
            continue
        tones = palette[part.material]
        if part.tone is not None:
            surface.set_at((x, y), tones[min(part.tone, len(tones) - 1)])
            continue
        shape = part.pixels
        neighbors = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        # A part drawn over another gets a dark rim there, so overlaps stay readable.
        over_other = any(owner.get(n, rank) < rank for n in neighbors)
        if over_other or (x + 1, y) not in shape or (x, y + 1) not in shape:
            tone = 0
        elif (x - 1, y) not in shape or (x, y - 1) not in shape:
            tone = 2
        else:
            tone = 1
        if (x, y) in part.highlight:
            tone = 3
        surface.set_at((x, y), tones[min(tone, len(tones) - 1)])
    for y in range(CELL):
        for x in range(CELL):
            if (x, y) not in owner and any(
                n in owner for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
            ):
                surface.set_at((x, y), outline)
    return surface
