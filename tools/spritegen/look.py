"""A look: body shape, palette, body materials, face and costume parts, from a TOML file."""

from __future__ import annotations

import colorsys
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

from .raster import Color
from .skeleton import POSE_NAMES, Build

BODY_SLOTS = ("head", "torso", "arms", "hands", "legs", "feet")
DEFAULT_CELL = 64


def parse_color(value: str | list[int]) -> Color:
    if isinstance(value, str):
        text = value.lstrip("#")
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    r, g, b = value[:3]
    return int(r), int(g), int(b)


def ramp(base: Color) -> list[Color]:
    """Four tones from one color: dark, base, light, highlight.

    Shadows lean slightly toward blue and lights toward warm, like hand-shaded pixel art.
    """
    r, g, b = (c / 255 for c in base)
    h, light, s = colorsys.rgb_to_hls(r, g, b)

    def tone(dl: float, ds: float, dh: float) -> Color:
        hue = (h + dh) % 1.0
        lum = max(0.03, min(0.96, light + dl))
        rgb = colorsys.hls_to_rgb(hue, lum, max(0.0, min(1.0, s + ds)))
        return tuple(round(c * 255) for c in rgb)

    return [tone(-0.11, 0.05, 0.015), base, tone(0.11, -0.03, -0.01), tone(0.26, -0.12, -0.02)]


@dataclass
class Look:
    id: str
    name: str
    palette: dict[str, list[Color]]
    body: dict[str, str]
    build: Build = field(default_factory=Build)
    cell: int = DEFAULT_CELL
    face: dict = field(default_factory=dict)
    parts: list[dict] = field(default_factory=list)
    recolor: list[str] = field(default_factory=list)  # palette entries the game may swap
    pose: str = "raise"  # signature pose (see skeleton.POSE_NAMES)


def load_look(path: Path) -> Look:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    palette: dict[str, list[Color]] = {}
    for name, value in data["palette"].items():
        if isinstance(value, str) or (value and isinstance(value[0], int)):
            palette[name] = ramp(parse_color(value))
        else:
            palette[name] = [parse_color(v) for v in value]
    body = data.get("body", {})
    missing = [slot for slot in BODY_SLOTS if slot not in body]
    if missing:
        raise ValueError(f"{path.name}: [body] is missing {', '.join(missing)}")
    for slot, material in body.items():
        if material not in palette:
            raise ValueError(f"{path.name}: body.{slot} uses unknown color '{material}'")
    build_data = dict(data.get("build", {}))
    cell = int(build_data.pop("cell", DEFAULT_CELL))
    known = {f.name for f in fields(Build)}
    unknown = set(build_data) - known
    if unknown:
        raise ValueError(f"{path.name}: unknown [build] settings {', '.join(sorted(unknown))}")
    pose = data.get("pose", "raise")
    if pose not in POSE_NAMES:
        raise ValueError(f"{path.name}: unknown pose '{pose}' (one of {', '.join(POSE_NAMES)})")
    return Look(
        id=path.stem,
        name=data.get("name", path.stem),
        palette=palette,
        body=dict(body),
        build=Build(**build_data),
        cell=cell,
        face=data.get("face", {}),
        parts=list(data.get("parts", [])),
        recolor=list(data.get("recolor", [])),
        pose=pose,
    )
