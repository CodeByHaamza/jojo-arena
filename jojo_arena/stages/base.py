"""Stage definition loaded from a data file, turned into a fresh Arena for each round."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.combat.hazards import (
    DropDef,
    Hazards,
    SurfaceDef,
    TrapZoneDef,
    parse_hazards,
    parse_surfaces,
)
from jojo_arena.engine.data import load_toml, seconds_to_frames
from jojo_arena.engine.geometry import Rect, RoundedRect, Vec2
from jojo_arena.engine.i18n import localized


@dataclass(frozen=True)
class PropDef:
    kind: str
    rect: Rect
    hp: int
    throwable: bool = False
    throw_damage: int = 0
    respawn_f: int = 0


SUN_MODES = ("off", "dawn", "day")  # no sun / dawn late in the round / full daylight


@dataclass(frozen=True)
class StageOptions:
    """What the players chose for this arena before the fight: whether the sun comes
    up, and whether the arena's own events (a chandelier falling, spikes) are on."""

    sun: str = "dawn"
    events: bool = True

    def __post_init__(self) -> None:
        if self.sun not in SUN_MODES:
            raise ValueError(f"unknown sun mode '{self.sun}'")

    def to_data(self) -> dict:
        return {"sun": self.sun, "events": self.events}

    @classmethod
    def from_data(cls, data: dict | None) -> StageOptions:
        data = data or {}
        return cls(sun=data.get("sun", "dawn"), events=data.get("events", True))


@dataclass(frozen=True)
class StageDef:
    id: str
    name: str
    bounds: RoundedRect
    spawns: tuple[Vec2, Vec2]
    props: tuple[PropDef, ...]
    palette: dict
    lanterns: tuple[Vec2, ...] = ()
    sun_windows: tuple[Rect, ...] = ()  # where the sun shines in, late in the round
    sun_after_f: int = 0
    sun_spread_f: int = 0  # how long the beams take to cross the room
    sun_widen: float = 0.3  # how much wider each beam gets on the way
    part: int = 0  # the JoJo part it belongs to
    drops: tuple[DropDef, ...] = ()  # events: what falls from above
    trap_zones: tuple[TrapZoneDef, ...] = ()  # events: what springs from the floor
    surfaces: tuple[SurfaceDef, ...] = ()  # the floor itself (always there)
    outdoors: bool = False  # no roof: the sun, once up, is everywhere

    @property
    def has_sun(self) -> bool:
        return bool(self.sun_windows)

    @property
    def has_events(self) -> bool:
        return bool(self.drops or self.trap_zones)

    def build_arena(self, options: StageOptions | None = None) -> Arena:
        options = options or StageOptions()
        obstacles = [
            Obstacle(
                p.kind,
                p.rect,
                p.hp,
                throwable=p.throwable,
                throw_damage=p.throw_damage,
                respawn_f=p.respawn_f,
            )
            for p in self.props
        ]
        windows = list(self.sun_windows) if options.sun != "off" else []
        full_day = options.sun == "day"
        events = options.events
        return Arena(
            self.bounds,
            (self.spawns[0].copy(), self.spawns[1].copy()),
            obstacles,
            sun_windows=windows,
            sun_after_f=0 if full_day else self.sun_after_f,
            sun_spread_f=0 if full_day else self.sun_spread_f,
            sun_widen=self.sun_widen,
            hazards=Hazards.build(
                self.drops if events else (),
                self.trap_zones if events else (),
                self.surfaces,
            ),
        )


def load_stage_def(path: Path, stage_id: str) -> StageDef:
    data = load_toml(path)
    bounds = RoundedRect(Rect(*data["bounds"]["rect"]), data["bounds"]["corner_radius"])
    spawns = (Vec2(*data["spawns"]["p1"]), Vec2(*data["spawns"]["p2"]))
    kinds = data.get("prop_kinds", {})
    props = []
    for p in data.get("props", []):
        kind = kinds.get(p["kind"], {})
        props.append(
            PropDef(
                p["kind"],
                Rect(*p["rect"]),
                p.get("hp", kind.get("hp", 0)),
                throwable=kind.get("throwable", False),
                throw_damage=kind.get("throw_damage", 0),
                respawn_f=seconds_to_frames(kind.get("respawn_s", 0)),
            )
        )
    props = tuple(props)
    lanterns = tuple(Vec2(*lamp["pos"]) for lamp in data.get("lanterns", []))
    sun = data.get("sun", {})
    drops, trap_zones = parse_hazards(data)
    return StageDef(
        stage_id,
        localized(data, "name"),
        bounds,
        spawns,
        props,
        data.get("palette", {}),
        lanterns,
        sun_windows=tuple(Rect(*w["rect"]) for w in sun.get("windows", [])),
        sun_after_f=seconds_to_frames(sun.get("after_s", 0)),
        sun_spread_f=seconds_to_frames(sun.get("spread_s", 0)),
        sun_widen=sun.get("widen", 0.3),
        part=data.get("part", 0),
        drops=drops,
        trap_zones=trap_zones,
        surfaces=parse_surfaces(data),
        outdoors=data.get("outdoors", False),
    )
