"""A look: body shape, palette, body materials, face and costume parts, from a TOML file."""

from __future__ import annotations

import colorsys
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

from .raster import Color
from .skeleton import DIRECTIONS, POINT_FIELDS, POSE_FIELDS, POSE_NAMES, Build, KeyAnim, Pose

BODY_SLOTS = ("head", "torso", "arms", "hands", "legs", "feet")
DEFAULT_CELL = 64
ANIM_SETTINGS = ("fps", "loop", "phases", "tween")
# A view the look does not pose copies the first of these that it does.
VIEW_STANDINS = {"down": ("up", "right"), "up": ("down", "right"), "right": ("down", "up")}


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
    anims: dict[str, KeyAnim] = field(default_factory=dict)  # key-pose animations


def parse_pose(data: dict, where: str) -> Pose:
    unknown = set(data) - set(POSE_FIELDS)
    if unknown:
        raise ValueError(f"{where}: unknown pose settings {', '.join(sorted(unknown))}")
    values = {}
    for name, value in data.items():
        if name in POINT_FIELDS:
            if len(value) != 2:
                raise ValueError(f"{where}: {name} needs two numbers [x, y]")
            values[name] = (float(value[0]), float(value[1]))
        elif name == "big_hand_r":
            values[name] = bool(value)
        else:
            values[name] = float(value)
    return Pose(**values)


def parse_anims(data: dict, where: str) -> dict[str, KeyAnim]:
    """[anims.<name>]: key poses per view, replacing the generated animation of that name
    or adding a new one (a move picks it in its kit with `anim = "<name>"`)."""
    anims = {}
    for name, spec in data.items():
        place = f"{where}: anims.{name}"
        unknown = set(spec) - set(ANIM_SETTINGS) - set(DIRECTIONS)
        if unknown:
            raise ValueError(f"{place}: unknown settings {', '.join(sorted(unknown))}")
        views = {
            view: tuple(parse_pose(key, f"{place}.{view}[{i}]") for i, key in enumerate(spec[view]))
            for view in DIRECTIONS
            if view in spec
        }
        if not views:
            raise ValueError(f"{place}: no key poses (give [[anims.{name}.down]] and so on)")
        given = dict(views)
        for view in DIRECTIONS:
            if view not in views:
                views[view] = given[next(v for v in VIEW_STANDINS[view] if v in given)]
        counts = {len(keys) for keys in views.values()}
        if len(counts) > 1 or 0 in counts:
            raise ValueError(f"{place}: every view needs the same number of key poses")
        phases = tuple(int(n) for n in spec["phases"]) if "phases" in spec else None
        if phases is not None and (sum(phases) != counts.pop() or min(phases) < 1):
            raise ValueError(f"{place}: phases must share out all the key poses, 1 or more each")
        tween = int(spec.get("tween", 0))
        if tween < 0:
            raise ValueError(f"{place}: tween cannot be negative")
        anims[name] = KeyAnim(
            views, int(spec.get("fps", 12)), bool(spec.get("loop", False)), phases, tween
        )
    return anims


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
        anims=parse_anims(data.get("anims", {}), path.name),
    )
