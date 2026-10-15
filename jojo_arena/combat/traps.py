"""Traps laid on the ground: they fire on their own when the opponent comes close."""

from __future__ import annotations

from dataclasses import dataclass

from jojo_arena.combat.kit import TrapDef
from jojo_arena.engine.geometry import Vec2


@dataclass
class Trap:
    owner: int
    pos: Vec2
    defn: TrapDef
    life: int

    def touched_by(self, pos: Vec2, radius: float) -> bool:
        return self.pos.distance_to(pos) < self.defn.radius + radius
