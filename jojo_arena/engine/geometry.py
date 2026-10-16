"""2D vectors and the few shapes the simulation needs. Pure Python, no pygame."""

from __future__ import annotations

import math
from dataclasses import dataclass


class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)

    @classmethod
    def from_angle(cls, radians: float, length: float = 1.0) -> Vec2:
        return cls(math.cos(radians) * length, math.sin(radians) * length)

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, k: float) -> Vec2:
        return Vec2(self.x * k, self.y * k)

    __rmul__ = __mul__

    def __neg__(self) -> Vec2:
        return Vec2(-self.x, -self.y)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Vec2) and self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __iter__(self):
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return f"Vec2({self.x:.2f}, {self.y:.2f})"

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self) -> Vec2:
        n = self.length()
        return Vec2(self.x / n, self.y / n) if n else Vec2()

    def dot(self, other: Vec2) -> float:
        return self.x * other.x + self.y * other.y

    def distance_to(self, other: Vec2) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def angle(self) -> float:
        return math.atan2(self.y, self.x)

    def reflect(self, normal: Vec2) -> Vec2:
        """Mirror this vector on a surface with the given unit normal."""
        return self - normal * (2 * self.dot(normal))

    def copy(self) -> Vec2:
        return Vec2(self.x, self.y)

    def as_ints(self) -> tuple[int, int]:
        return round(self.x), round(self.y)


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def center(self) -> Vec2:
        return Vec2(self.x + self.w / 2, self.y + self.h / 2)

    def distance_to(self, p: Vec2) -> float:
        """Distance from a point to the rectangle (0 inside it)."""
        dx = max(self.left - p.x, 0.0, p.x - self.right)
        dy = max(self.top - p.y, 0.0, p.y - self.bottom)
        return math.hypot(dx, dy)

    def inflate(self, amount: float) -> Rect:
        return Rect(self.x - amount, self.y - amount, self.w + 2 * amount, self.h + 2 * amount)

    def contains(self, p: Vec2) -> bool:
        return self.left <= p.x <= self.right and self.top <= p.y <= self.bottom

    def closest_point(self, p: Vec2) -> Vec2:
        return Vec2(min(max(p.x, self.left), self.right), min(max(p.y, self.top), self.bottom))


def circles_overlap(c1: Vec2, r1: float, c2: Vec2, r2: float) -> bool:
    return (c1 - c2).length_sq() < (r1 + r2) ** 2


def circle_overlaps_rect(c: Vec2, r: float, rect: Rect) -> bool:
    return (c - rect.closest_point(c)).length_sq() < r * r


def push_circle_out_of_rect(c: Vec2, r: float, rect: Rect) -> tuple[Vec2, Vec2] | None:
    """If the circle overlaps the rect, return (corrected center, outward unit normal)."""
    closest = rect.closest_point(c)
    offset = c - closest
    dist_sq = offset.length_sq()
    if dist_sq >= r * r:
        return None
    if dist_sq > 1e-12:
        normal = offset * (1 / math.sqrt(dist_sq))
        return closest + normal * r, normal
    # Center inside the rect: leave through the nearest side.
    exits = (
        (c.x - rect.left, Vec2(-1, 0), Vec2(rect.left - r, c.y)),
        (rect.right - c.x, Vec2(1, 0), Vec2(rect.right + r, c.y)),
        (c.y - rect.top, Vec2(0, -1), Vec2(c.x, rect.top - r)),
        (rect.bottom - c.y, Vec2(0, 1), Vec2(c.x, rect.bottom + r)),
    )
    _, normal, pos = min(exits, key=lambda e: e[0])
    return pos, normal


@dataclass(frozen=True)
class RoundedRect:
    """Closed play area: a rectangle with rounded corners that keeps circles inside."""

    rect: Rect
    radius: float

    def constrain_circle(self, c: Vec2, r: float) -> tuple[Vec2, Vec2 | None]:
        """Keep a circle fully inside. Returns (center, inward wall normal or None)."""
        inner = self.rect.inflate(-r)
        corner_r = max(0.0, self.radius - r)
        x = min(max(c.x, inner.left), inner.right)
        y = min(max(c.y, inner.top), inner.bottom)
        normal: Vec2 | None = None
        if x != c.x:
            normal = Vec2(1 if x > c.x else -1, 0)
        if y != c.y:
            normal = Vec2(0, 1 if y > c.y else -1) if normal is None else normal
        # Corner arcs: inside a corner square, stay within the arc's circle.
        cx = inner.left + corner_r if x < inner.left + corner_r else None
        if x > inner.right - corner_r:
            cx = inner.right - corner_r
        cy = inner.top + corner_r if y < inner.top + corner_r else None
        if y > inner.bottom - corner_r:
            cy = inner.bottom - corner_r
        if corner_r > 0 and cx is not None and cy is not None:
            arc_center = Vec2(cx, cy)
            offset = Vec2(x, y) - arc_center
            if offset.length() > corner_r:
                outward = offset.normalized()
                x, y = arc_center.x + outward.x * corner_r, arc_center.y + outward.y * corner_r
                normal = -outward
        return Vec2(x, y), normal
