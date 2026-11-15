"""A look: body shape, palette, body materials, face and costume parts, from a TOML file.

A look may be a costume of another (`base = "<id>"`: it says only what changes) and may
carry colours (`[colors.<id>]`: other palettes the game repaints its sheet with)."""

from __future__ import annotations

import colorsys
import tomllib
from dataclasses import dataclass, field, fields, replace
from pathlib import Path

from .raster import Color
from .skeleton import DIRECTIONS, POINT_FIELDS, POSE_FIELDS, POSE_NAMES, Build, KeyAnim, Pose

BODY_SLOTS = ("head", "torso", "arms", "hands", "legs", "feet")
DEFAULT_CELL = 64
ANIM_SETTINGS = ("fps", "loop", "phases", "tween")
# What a pose says besides its key poses: its name in both languages, where it comes from,
# whether the Stand strikes it too, and where the Stand stands then (ahead, aside), in px.
POSE_SETTINGS = ("label", "label_en", "source", "stand", "stand_offset")
DEFAULT_STAND_OFFSET = (-14.0, -8.0)  # just behind and beside, as when it is out
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


@dataclass(frozen=True)
class PoseDef:
    """A JoJo pose: its key poses and what the select screen and the sheet say of it."""

    anim: KeyAnim
    label: str = ""
    label_en: str = ""
    source: str = ""
    stand: bool = False  # struck with the Stand out, the Stand posing beside its user
    stand_offset: tuple[float, float] = DEFAULT_STAND_OFFSET


@dataclass(frozen=True)
class CostumeDef:
    """What the select screen says of this outfit, and where it comes from."""

    label: str
    label_en: str
    source: str


@dataclass(frozen=True)
class ColorDef:
    """A colour of the look: its name, its source, and the materials it paints anew."""

    label: str
    label_en: str
    source: str
    stand: str = ""  # the colour of its Stand's look that goes with it
    palette: dict[str, list[Color]] = field(default_factory=dict)  # empty: the look itself


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
    poses: dict[str, PoseDef] = field(default_factory=dict)  # JoJo poses, in order
    base: str = ""  # the look this one is a costume of
    costume: CostumeDef | None = None
    colors: dict[str, ColorDef] = field(default_factory=dict)  # in order; the first is itself


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


def parse_poses(data: dict, where: str) -> dict[str, PoseDef]:
    """[poses.<id>]: a JoJo pose, played as the animation `pose_<id>`. A fighter's pose
    names itself and its source; a Stand's pose of the same id gives only its frames."""
    poses = {}
    for pose_id, spec in data.items():
        place = f"{where}: poses.{pose_id}"
        allowed = set(POSE_SETTINGS) | set(ANIM_SETTINGS) | set(DIRECTIONS)
        unknown = set(spec) - allowed
        if unknown:
            raise ValueError(f"{place}: unknown settings {', '.join(sorted(unknown))}")
        named = [key for key in ("label", "label_en", "source") if spec.get(key)]
        if named and len(named) < 3:
            raise ValueError(f"{place}: a pose with a label needs label, label_en and source")
        offset = spec.get("stand_offset", DEFAULT_STAND_OFFSET)
        if len(offset) != 2:
            raise ValueError(f"{place}: stand_offset needs two numbers [ahead, aside]")
        frames = {key: value for key, value in spec.items() if key not in POSE_SETTINGS}
        frames.setdefault("fps", 4)
        frames.setdefault("loop", True)
        anim = parse_anims({pose_id: frames}, f"{where}: poses")[pose_id]
        if all(len(keys) == 1 for keys in anim.views.values()):
            # One key per view: it breathes, the chest rising and falling a pixel.
            views = {
                v: (keys[0], replace(keys[0], bob=keys[0].bob + 1))
                for v, keys in anim.views.items()
            }
            anim = KeyAnim(views, anim.fps, anim.loop, anim.phases, anim.tween)
        poses[pose_id] = PoseDef(
            anim=anim,
            label=str(spec.get("label", "")),
            label_en=str(spec.get("label_en", "")),
            source=str(spec.get("source", "")),
            stand=bool(spec.get("stand", False)),
            stand_offset=(float(offset[0]), float(offset[1])),
        )
    return poses


MERGED = ("palette", "body", "build", "face")  # a costume's entries go over its base's
NAMED = ("label", "label_en", "source")


def read_look(path: Path) -> dict:
    """The data of a look file, a costume's laid over its base's."""
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    base_id = data.get("base")
    if not base_id:
        return data
    base_path = path.parent / f"{base_id}.toml"
    if not base_path.exists():
        raise ValueError(f"{path.name}: its base '{base_id}' is not there ({base_path.name})")
    if "anims" in data or "poses" in data:
        raise ValueError(
            f"{path.name}: a costume moves as its base does: no [anims] or [poses] of its own"
        )
    base = read_look(base_path)
    merged = {key: value for key, value in base.items() if key not in ("colors", "costume")}
    for key, value in data.items():
        merged[key] = {**base.get(key, {}), **value} if key in MERGED else value
    return merged


def _tones(value) -> list[Color]:
    """One color (its four tones are computed), or the tones given one by one."""
    if isinstance(value, str) or (value and isinstance(value[0], int)):
        return ramp(parse_color(value))
    return [parse_color(v) for v in value]


def parse_colors(data: dict, palette: dict, where: str) -> dict[str, ColorDef]:
    """[colors.<id>]: the first is the look as it is drawn; the others repaint materials."""
    colors = {}
    for color_id, spec in data.items():
        place = f"{where}: colors.{color_id}"
        if not all(spec.get(key) for key in NAMED):
            raise ValueError(f"{place} needs label, label_en and source")
        painted = spec.get("palette", {})
        if not colors and painted:
            raise ValueError(f"{place}: the first colour is the look itself, it takes no palette")
        if colors and not painted:
            raise ValueError(f"{place} needs a palette: what it paints anew")
        for slot in painted:
            if slot not in palette:
                raise ValueError(f"{place} uses unknown color '{slot}'")
        colors[color_id] = ColorDef(
            label=str(spec["label"]),
            label_en=str(spec["label_en"]),
            source=str(spec["source"]),
            stand=str(spec.get("stand", "")),
            palette={slot: _tones(value) for slot, value in painted.items()},
        )
    return colors


def load_look(path: Path) -> Look:
    data = read_look(path)
    palette = {name: _tones(value) for name, value in data["palette"].items()}
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
    outfit = data.get("costume")
    if outfit is not None and not all(outfit.get(key) for key in NAMED):
        raise ValueError(f"{path.name}: [costume] needs label, label_en and source")
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
        poses=parse_poses(data.get("poses", {}), path.name),
        base=str(data.get("base", "")),
        costume=CostumeDef(*(str(outfit[key]) for key in NAMED)) if outfit else None,
        colors=parse_colors(data.get("colors", {}), palette, path.name),
    )
