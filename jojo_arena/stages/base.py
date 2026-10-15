"""Stage definition loaded from a data file, turned into a fresh Arena for each round."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.data import load_toml
from jojo_arena.engine.geometry import Rect, RoundedRect, Vec2


@dataclass(frozen=True)
class PropDef:
    kind: str
    rect: Rect
    hp: int


@dataclass(frozen=True)
class StageDef:
    id: str
    name: str
    bounds: RoundedRect
    spawns: tuple[Vec2, Vec2]
    props: tuple[PropDef, ...]
    palette: dict

    def build_arena(self) -> Arena:
        obstacles = [Obstacle(p.kind, p.rect, p.hp) for p in self.props]
        return Arena(self.bounds, (self.spawns[0].copy(), self.spawns[1].copy()), obstacles)


def load_stage_def(path: Path, stage_id: str) -> StageDef:
    data = load_toml(path)
    bounds = RoundedRect(Rect(*data["bounds"]["rect"]), data["bounds"]["corner_radius"])
    spawns = (Vec2(*data["spawns"]["p1"]), Vec2(*data["spawns"]["p2"]))
    kinds = data.get("prop_kinds", {})
    props = tuple(
        PropDef(p["kind"], Rect(*p["rect"]), p.get("hp", kinds.get(p["kind"], {}).get("hp", 0)))
        for p in data.get("props", [])
    )
    return StageDef(stage_id, data["name"], bounds, spawns, props, data.get("palette", {}))
