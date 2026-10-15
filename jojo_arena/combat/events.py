"""Things that happened during a step, for the presentation layer (effects, sounds, HUD)."""

from __future__ import annotations

from dataclasses import dataclass

from jojo_arena.engine.geometry import Vec2


@dataclass(frozen=True)
class Event:
    kind: str
    pos: Vec2 | None = None
    fighter: int | None = None  # index of the fighter concerned
    value: float = 0.0
