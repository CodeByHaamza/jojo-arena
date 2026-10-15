"""Sprite sheets, animation timing, and a geometric placeholder when art is missing.

A sheet is a PNG cut in equal cells plus a TOML spec. Each animation owns one row per
drawn direction ("down", "up", "right"); "left" is "right" mirrored. Swapping a
placeholder for real art only means dropping new files with the same names.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

from .data import load_toml

OUTLINE = (23, 18, 31)
Color = tuple[int, int, int]


def parse_color(value: str | list[int] | tuple[int, ...]) -> Color:
    if isinstance(value, str):
        text = value.lstrip("#")
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    r, g, b = value[:3]
    return int(r), int(g), int(b)


def shade(color: Color, amount: int) -> Color:
    return tuple(max(0, min(255, c + amount)) for c in color)


@dataclass(frozen=True)
class AnimSpec:
    name: str
    frames: int
    fps: int = 10
    loop: bool = True
    # Frames given to the startup / active / recovery phases of an attack, if the
    # animation follows the move's timing instead of a fixed frame rate.
    phases: tuple[int, ...] | None = None


def frame_index(
    spec: AnimSpec, elapsed: int, phase: tuple[int, int, int] | None = None, hz: int = 60
) -> int:
    """Which frame to show after `elapsed` logic steps.

    `phase` is (phase number, steps spent in that phase, length of that phase) and
    only matters when the animation has `phases`.
    """
    if spec.phases and phase is not None:
        number, spent, length = phase
        number = min(number, len(spec.phases) - 1)
        first = sum(spec.phases[:number])
        count = spec.phases[number]
        return min(spec.frames - 1, first + min(count - 1, spent * count // max(1, length)))
    index = elapsed * spec.fps // hz
    return index % spec.frames if spec.loop else min(index, spec.frames - 1)


def sprite_direction(fx: float, fy: float) -> tuple[str, bool]:
    """Pick the drawn view for a facing vector: (direction, mirror horizontally).

    Diagonals use the side view; only clearly vertical facings use up/down.
    """
    if abs(fy) > abs(fx) * 1.5:
        return ("down" if fy > 0 else "up"), False
    return "right", fx < 0


class SpriteSet:
    anchor: tuple[int, int] = (24, 44)

    def spec(self, anim: str) -> AnimSpec | None:
        raise NotImplementedError

    def frame(self, anim: str, direction: str, flip: bool, index: int) -> pygame.Surface:
        raise NotImplementedError


class SheetSprites(SpriteSet):
    def __init__(self, sheet: pygame.Surface, spec_data: dict) -> None:
        self.cell = tuple(spec_data["frame_size"])
        self.anchor = tuple(spec_data["anchor"])
        self.directions = list(spec_data["directions"])
        self.specs: dict[str, AnimSpec] = {}
        self._frames: dict[tuple[str, str], list[pygame.Surface]] = {}
        self._flipped: dict[tuple[str, str, int], pygame.Surface] = {}
        width, height = self.cell
        for name, anim in spec_data["anims"].items():
            phases = tuple(anim["phases"]) if "phases" in anim else None
            spec = AnimSpec(
                name, anim["frames"], anim.get("fps", 10), anim.get("loop", True), phases
            )
            self.specs[name] = spec
            for d, direction in enumerate(self.directions):
                y = (anim["row"] + d) * height
                self._frames[(name, direction)] = [
                    sheet.subsurface((i * width, y, width, height)) for i in range(spec.frames)
                ]

    @classmethod
    def load(
        cls, png_path: Path, spec_path: Path, palette: dict[str, list[Color]] | None = None
    ) -> SheetSprites | None:
        """Load a sheet, recolored with `palette`. Returns None when the files are missing."""
        if not png_path.exists() or not spec_path.exists():
            return None
        spec_data = load_toml(spec_path)
        sheet = pygame.image.load(str(png_path))
        if palette:
            sheet = recolor(sheet, spec_data.get("recolor", {}), palette)
        if pygame.display.get_init() and pygame.display.get_surface() is not None:
            sheet = sheet.convert_alpha()
        return cls(sheet, spec_data)

    def spec(self, anim: str) -> AnimSpec | None:
        return self.specs.get(anim)

    def frame(self, anim: str, direction: str, flip: bool, index: int) -> pygame.Surface:
        frames = self._frames.get((anim, direction)) or self._frames[(anim, self.directions[0])]
        index = min(index, len(frames) - 1)
        if not flip:
            return frames[index]
        key = (anim, direction, index)
        if key not in self._flipped:
            self._flipped[key] = pygame.transform.flip(frames[index], True, False)
        return self._flipped[key]


def recolor(
    sheet: pygame.Surface, keys: dict[str, list], palette: dict[str, list[Color]]
) -> pygame.Surface:
    """Replace each key color with the matching tone of the palette slot."""
    result = sheet.copy()
    pixels = pygame.PixelArray(result)
    for slot, key_colors in keys.items():
        tones = palette.get(slot)
        if not tones:
            continue
        for i, key in enumerate(key_colors):
            pixels.replace(parse_color(key), tones[min(i, len(tones) - 1)])
    pixels.close()
    return result


class PlaceholderSprites(SpriteSet):
    """Simple shapes in the character's color, standing in for missing art."""

    ANIMS = {
        "idle": AnimSpec("idle", 2, 3),
        "walk": AnimSpec("walk", 2, 8),
        "ko": AnimSpec("ko", 2, 6, loop=False),
    }

    def __init__(self, color: Color, size: int = 48, anchor: tuple[int, int] = (24, 44)) -> None:
        self.color = color
        self.size = size
        self.anchor = anchor
        self._cache: dict[tuple[str, str, bool, int], pygame.Surface] = {}

    def spec(self, anim: str) -> AnimSpec | None:
        return self.ANIMS.get(anim, AnimSpec(anim, 1, 1))

    def frame(self, anim: str, direction: str, flip: bool, index: int) -> pygame.Surface:
        key = (anim, direction, flip, index)
        if key not in self._cache:
            self._cache[key] = self._draw(anim, direction, flip, index)
        return self._cache[key]

    def _draw(self, anim: str, direction: str, flip: bool, index: int) -> pygame.Surface:
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        ax, ay = self.anchor
        base, dark, light = self.color, shade(self.color, -50), shade(self.color, 50)
        if anim == "ko" and index > 0:
            body = pygame.Rect(ax - 16, ay - 9, 32, 10)
            pygame.draw.ellipse(surface, OUTLINE, body.inflate(2, 2))
            pygame.draw.ellipse(surface, dark, body)
            return surface
        bob = 1 if anim in ("idle", "walk") and index % 2 else 0
        squash = 4 if anim == "dash" else 0
        tilt = -3 if anim in ("hurt", "ko") else 0
        body = pygame.Rect(ax - 8 - squash // 2 + tilt, ay - 24 + bob, 16 + squash, 24 - bob)
        pygame.draw.rect(surface, OUTLINE, body.inflate(2, 2), border_radius=7)
        pygame.draw.rect(surface, dark, body, border_radius=6)
        pygame.draw.rect(surface, base, body.inflate(-4, -3).move(-1, -1), border_radius=5)
        head = (ax + tilt, ay - 30 + bob)
        pygame.draw.circle(surface, OUTLINE, head, 8)
        pygame.draw.circle(surface, base, head, 7)
        surface.set_at((head[0] - 3, head[1] - 3), light)
        # Facing marker: where this body is looking or striking.
        dx, dy = {"down": (0, 1), "up": (0, -1), "right": (1, 0)}.get(direction, (0, 1))
        if flip:
            dx = -dx
        reach = 13 if anim in ("light", "heavy", "special") else 6
        if direction == "down" and reach == 6:
            surface.fill(OUTLINE, (head[0] - 3, head[1], 2, 2))
            surface.fill(OUTLINE, (head[0] + 2, head[1], 2, 2))
        elif reach > 6:
            fist = (ax + dx * reach, ay - 16 + dy * reach // 2)
            pygame.draw.circle(surface, OUTLINE, fist, 4)
            pygame.draw.circle(surface, light, fist, 3)
        if anim == "guard":
            bar = pygame.Rect(0, 0, 4, 14) if dx else pygame.Rect(0, 0, 14, 4)
            bar.center = (ax + dx * 10, ay - 14 + dy * 6)
            surface.fill(OUTLINE, bar.inflate(2, 2))
            surface.fill(light, bar)
        if anim == "pose":
            for side in (-1, 1):
                pygame.draw.circle(surface, OUTLINE, (ax + side * 9, ay - 34), 3)
                pygame.draw.circle(surface, light, (ax + side * 9, ay - 34), 2)
        return surface
