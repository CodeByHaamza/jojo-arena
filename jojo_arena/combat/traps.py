"""Traps laid on the ground: they fire on their own when the opponent comes close."""

from __future__ import annotations

from dataclasses import dataclass

from jojo_arena.combat.kit import TrapDef, WebDef
from jojo_arena.engine.geometry import Rect, Vec2


@dataclass
class Trap:
    owner: int
    pos: Vec2
    defn: TrapDef
    life: int

    def touched_by(self, pos: Vec2, radius: float) -> bool:
        return self.pos.distance_to(pos) < self.defn.radius + radius


def distance_to_segment(p: Vec2, a: Vec2, b: Vec2) -> float:
    ab = b - a
    length_sq = ab.length_sq()
    if length_sq == 0:
        return p.distance_to(a)
    t = max(0.0, min(1.0, (p - a).dot(ab) / length_sq))
    return p.distance_to(a + ab * t)


def web_layout(area: Rect, defn: WebDef) -> tuple[list[Vec2], list[tuple[int, int]]]:
    """Anchor points spread over the arena, and the threads between them. Always the same
    for the same arena (the view draws the web being laid before the simulation lays it)."""
    left, top = area.left + defn.margin, area.top + defn.margin
    width, height = area.w - 2 * defn.margin, area.h - 2 * defn.margin
    nodes: list[Vec2] = []
    for row in range(defn.rows):
        for col in range(defn.columns):
            fx = col / max(1, defn.columns - 1)
            fy = row / max(1, defn.rows - 1)
            # A slight, fixed irregularity so it reads as a web, not a grid.
            jx = ((col * 7 + row * 3) % 5 - 2) * 3
            jy = ((col * 3 + row * 5) % 5 - 2) * 3
            nodes.append(Vec2(left + fx * width + jx, top + fy * height + jy))
    edges: list[tuple[int, int]] = []
    for row in range(defn.rows):
        for col in range(defn.columns):
            i = row * defn.columns + col
            if col + 1 < defn.columns:
                edges.append((i, i + 1))
            if row + 1 < defn.rows:
                edges.append((i, i + defn.columns))
            if col + 1 < defn.columns and row + 1 < defn.rows and (col + row) % 2 == 0:
                edges.append((i, i + defn.columns + 1))
    return nodes, edges


@dataclass
class Web:
    owner: int
    nodes: list[Vec2]
    edges: list[tuple[int, int]]
    defn: WebDef
    life: int
    rearm: int = 0

    def touched_by(self, pos: Vec2, radius: float) -> bool:
        reach = self.defn.touch_radius + radius
        return any(
            distance_to_segment(pos, self.nodes[a], self.nodes[b]) < reach for a, b in self.edges
        )

    def nearest_nodes(self, pos: Vec2, count: int) -> list[Vec2]:
        return sorted(self.nodes, key=pos.distance_to)[:count]
