"""Sprite sheets, animation timing, and a geometric placeholder when art is missing.

A sheet is a PNG cut in equal cells plus a TOML spec. Each animation owns one row per
drawn direction ("down", "up", "right"); "left" is "right" mirrored. Swapping a
placeholder for real art only means dropping new files with the same names.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from .data import load_toml

OUTLINE = (23, 18, 31)
Color = tuple[int, int, int]
STAND_IN_ALPHA = 254  # recolor: the alpha of its stand-in colours (see there)


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


@dataclass(frozen=True)
class PoseInfo:
    """A named pose a sheet can play (animation `pose_<id>`), and where it comes from."""

    id: str
    label: str
    label_en: str
    source: str
    stand: bool  # struck with the Stand out, the Stand posing too
    stand_offset: tuple[float, float]  # where the Stand stands then: ahead, aside (px)


@dataclass(frozen=True)
class ColorInfo:
    """A colour a sheet can be repainted in when it is loaded, and where it comes from."""

    id: str
    label: str
    label_en: str
    source: str
    stand: str = ""  # the colour of the same name its Stand's sheet goes with ("": its own)
    # Material -> its tones in this colour. Empty: the sheet as it is drawn.
    palette: dict[str, list[Color]] = field(default_factory=dict)


NO_POSES: dict[str, PoseInfo] = {}
NO_COLORS: dict[str, ColorInfo] = {}

# Sheets already decoded (see SheetSprites.load). A sheet as it is drawn stays for good;
# a repainted one weighs as much and is asked for far less often (a colour tried on the
# select screen), so only the last few are kept.
_LOADED: dict[tuple, SheetSprites] = {}
_REPAINTED: OrderedDict[tuple, SheetSprites] = OrderedDict()
REPAINTED_KEPT = 8


class SpriteSet:
    anchor: tuple[int, int] = (24, 44)
    chest: int = 16  # pixels above the feet where hits and effects should appear
    height: int = 38  # pixels above the feet to the top of the head
    poses: dict[str, PoseInfo] = NO_POSES  # in the order of the look file; read only
    colors: dict[str, ColorInfo] = NO_COLORS  # the first one is the sheet as it is drawn
    costume: tuple[str, str, str] = ("", "", "")  # its name in both languages, its source

    def spec(self, anim: str) -> AnimSpec | None:
        raise NotImplementedError

    def frame(self, anim: str, direction: str, flip: bool, index: int) -> pygame.Surface:
        raise NotImplementedError


class SheetSprites(SpriteSet):
    def __init__(self, sheet: pygame.Surface, spec_data: dict) -> None:
        self.cell = tuple(spec_data["frame_size"])
        self.anchor = tuple(spec_data["anchor"])
        self.chest = spec_data.get("chest", SpriteSet.chest)
        self.height = spec_data.get("height", SpriteSet.height)
        self.directions = list(spec_data["directions"])
        self.poses = {
            pose_id: PoseInfo(
                pose_id,
                info.get("label", ""),
                info.get("label_en", ""),
                info.get("source", ""),
                bool(info.get("stand", False)),
                (float(info["stand_offset"][0]), float(info["stand_offset"][1]))
                if "stand_offset" in info
                else (-14.0, -8.0),
            )
            for pose_id, info in spec_data.get("poses", {}).items()
        }
        self.colors = {
            color_id: ColorInfo(
                color_id,
                info.get("label", ""),
                info.get("label_en", ""),
                info.get("source", ""),
                info.get("stand", ""),
                {
                    slot: [parse_color(tone) for tone in tones]
                    for slot, tones in info.get("palette", {}).items()
                },
            )
            for color_id, info in spec_data.get("colors", {}).items()
        }
        outfit = spec_data.get("costume", {})
        self.costume = (
            outfit.get("label", ""),
            outfit.get("label_en", ""),
            outfit.get("source", ""),
        )
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
        cls,
        png_path: Path,
        spec_path: Path,
        palette: dict[str, list[Color]] | None = None,
        color: str = "",
    ) -> SheetSprites | None:
        """Load a sheet, recolored with `palette` and then in the sheet's own colour named
        `color` (a colour it does not have is the sheet as it is). Returns None when the
        files are missing.

        A sheet is decoded once and shared: every menu and every fight asks for the same
        ones, and a sheet is only ever read once built. A file changed on disk, another
        palette or colour, or a display opened since, is another sheet."""
        if not png_path.exists() or not spec_path.exists():
            return None
        converting = pygame.display.get_init() and pygame.display.get_surface() is not None
        stamp = (
            str(png_path),
            str(spec_path),
            png_path.stat().st_mtime_ns,
            spec_path.stat().st_mtime_ns,
            tuple(
                sorted((slot, tuple(map(tuple, tones))) for slot, tones in (palette or {}).items())
            ),
            converting,
        )
        plain = _LOADED.get(stamp)
        if plain is not None and not plain.colors.get(color, ColorInfo("", "", "", "")).palette:
            return plain  # no such colour, or the one the sheet is drawn in
        key = (*stamp, color)
        if key in _REPAINTED:
            _REPAINTED.move_to_end(key)
            return _REPAINTED[key]
        spec_data = load_toml(spec_path)
        painted = dict(palette or {})
        painted.update(
            {
                slot: [parse_color(tone) for tone in tones]
                for slot, tones in spec_data.get("colors", {})
                .get(color, {})
                .get("palette", {})
                .items()
            }
        )
        repainted = painted != (palette or {})
        if not repainted and plain is not None:
            return plain
        sheet = pygame.image.load(str(png_path))
        if painted:
            sheet = recolor(sheet, spec_data.get("recolor", {}), painted)
        if converting:
            sheet = sheet.convert_alpha()
        loaded = cls(sheet, spec_data)
        if not repainted:
            _LOADED[stamp] = loaded
            return loaded
        _REPAINTED[key] = loaded
        while len(_REPAINTED) > REPAINTED_KEPT:
            _REPAINTED.popitem(last=False)
        return loaded

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
    """Replace each key color with the matching tone of the palette slot, all at once:
    a tone a material was just painted with is never taken for another material's key (a
    white shirt turned the grey the trousers had stays that grey)."""
    # An exact copy that always has an alpha channel (the stand-ins below rely on it).
    result = pygame.Surface(sheet.get_size(), pygame.SRCALPHA)
    result.blit(sheet, (0, 0), special_flags=pygame.BLEND_RGBA_MAX)
    swaps: list[tuple[Color, Color]] = []
    for slot, key_colors in keys.items():
        tones = palette.get(slot)
        if not tones:
            continue
        for i, key in enumerate(key_colors):
            swaps.append((parse_color(key), tuple(tones[min(i, len(tones) - 1)])[:3]))
    pixels = pygame.PixelArray(result)
    # Two rounds. Every key goes to a stand-in no drawn pixel can be (a sprite's pixels
    # are fully opaque or fully clear: these are neither), then every stand-in to its
    # tone. No tone is ever on the image while keys are still being looked for.
    for n, (key, _) in enumerate(swaps):
        pixels.replace((*key, 255), (n % 256, n // 256, 0, STAND_IN_ALPHA))
    for n, (_, tone) in enumerate(swaps):
        pixels.replace((n % 256, n // 256, 0, STAND_IN_ALPHA), (*tone, 255))
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
