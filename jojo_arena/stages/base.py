"""Stage definition loaded from a data file, turned into a fresh Arena for each round."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jojo_arena.combat.arena import Arena, Obstacle
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
    part: int = 0  # the JoJo part it belongs to

    def build_arena(self) -> Arena:
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
        return Arena(
            self.bounds,
            (self.spawns[0].copy(), self.spawns[1].copy()),
            obstacles,
            sun_windows=list(self.sun_windows),
            sun_after_f=self.sun_after_f,
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
        part=data.get("part", 0),
    )
