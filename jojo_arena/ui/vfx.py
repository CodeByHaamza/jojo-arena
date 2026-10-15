"""Procedural effects drawn over the fight: projectile shapes, stretching limbs and blades.

Everything is drawn with a few pixels of pygame primitives, in the style A palette
(dark outline, two or three tones, a highlight), oriented along its direction of travel.
"""

from __future__ import annotations

import pygame

from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.sprites import shade

OUTLINE = (23, 18, 31)
STEEL = (214, 220, 234)
STEEL_DARK = (128, 136, 158)
GOLD = (232, 188, 74)
LEATHER = (110, 66, 42)
EMERALD = (38, 168, 92)
EMERALD_LIGHT = (126, 236, 160)
EMERALD_DARK = (18, 96, 58)


def _ints(v: Vec2) -> tuple[int, int]:
    return round(v.x), round(v.y)


def _side(d: Vec2) -> Vec2:
    return Vec2(-d.y, d.x)


def draw_projectile(
    surface: pygame.Surface, look: str, pos: Vec2, direction: Vec2, radius: float, aura
) -> None:
    """One projectile at `pos` (already lifted to chest height), pointing along `direction`."""
    d = direction.normalized() if direction.length_sq() else Vec2(1, 0)
    if look == "knife":
        _draw_knife(surface, pos, d)
    elif look == "gem":
        _draw_gem(surface, pos, d)
    elif look == "blade":
        _draw_blade(surface, pos, d)
    else:
        _draw_orb(surface, pos, radius, aura)


def _draw_orb(surface, pos: Vec2, radius: float, aura) -> None:
    r = round(radius)
    blit_glow(surface, radial_glow(r * 3, tuple(c // 2 for c in aura)), (pos.x, pos.y))
    center = _ints(pos)
    pygame.draw.circle(surface, OUTLINE, center, r + 1)
    pygame.draw.circle(surface, shade(aura, 40), center, r)
    pygame.draw.circle(surface, (255, 255, 255), center, max(1, r - 2))


def _draw_knife(surface, pos: Vec2, d: Vec2) -> None:
    """A throwing knife: steel blade, small gold guard, leather grip."""
    tip, guard, end = pos + d * 6, pos - d * 1, pos - d * 5
    side = _side(d)
    pygame.draw.line(surface, OUTLINE, _ints(tip + d), _ints(end - d), 4)
    pygame.draw.line(surface, OUTLINE, _ints(guard + side * 3), _ints(guard - side * 3), 3)
    pygame.draw.line(surface, STEEL_DARK, _ints(tip), _ints(guard), 2)
    pygame.draw.line(surface, STEEL, _ints(tip - side * 0.5), _ints(guard - side * 0.5), 1)
    pygame.draw.line(surface, LEATHER, _ints(guard), _ints(end), 2)
    pygame.draw.line(surface, GOLD, _ints(guard + side * 2), _ints(guard - side * 2), 1)
    surface.set_at(_ints(tip - d), (255, 255, 255))


def _draw_gem(surface, pos: Vec2, d: Vec2) -> None:
    """An emerald: a cut gem, long along its flight, with a bright facet and a glint."""
    blit_glow(surface, radial_glow(7, (16, 70, 34)), (pos.x, pos.y))
    side = _side(d)
    front, back = pos + d * 4.5, pos - d * 3.5
    left, right = pos + side * 2.6, pos - side * 2.6
    outline = [front + d, left + side, back - d, right - side]
    pygame.draw.polygon(surface, OUTLINE, [_ints(p) for p in outline])
    pygame.draw.polygon(surface, EMERALD, [_ints(p) for p in (front, left, back, right)])
    pygame.draw.polygon(surface, EMERALD_DARK, [_ints(p) for p in (pos, right, back)])
    pygame.draw.polygon(surface, EMERALD_LIGHT, [_ints(p) for p in (front, left, pos)])
    surface.set_at(_ints(pos + d * 2 + side), (235, 255, 240))


def _draw_blade(surface, pos: Vec2, d: Vec2) -> None:
    """A rapier blade flying point first, with a silver glow."""
    blit_glow(surface, radial_glow(8, (60, 64, 80)), (pos.x, pos.y))
    tip, base = pos + d * 8, pos - d * 7
    pygame.draw.line(surface, OUTLINE, _ints(tip + d), _ints(base - d), 3)
    pygame.draw.line(surface, STEEL, _ints(tip), _ints(base), 1)
    surface.set_at(_ints(tip), (255, 255, 255))


def draw_reach(
    surface: pygame.Surface, start: Vec2, tip: Vec2, color, kind: str = "limb", width: int = 2
) -> None:
    """Something stretching from `start` to `tip`: a finger, a tentacle, a rapier.

    `kind` is "limb" (rounded, the user's color), "tentacle" (wavy) or "blade" (steel).
    """
    if (tip - start).length_sq() < 1:
        return
    if kind == "blade":
        pygame.draw.line(surface, OUTLINE, _ints(start), _ints(tip), 3)
        pygame.draw.line(surface, STEEL, _ints(start), _ints(tip), 1)
        surface.set_at(_ints(tip), (255, 255, 255))
        return
    points = [start]
    steps = max(2, round((tip - start).length() / 4))
    side = _side((tip - start).normalized())
    for i in range(1, steps):
        t = i / steps
        wave = side * (1.6 if kind == "tentacle" and i % 2 else 0)
        points.append(start + (tip - start) * t + wave)
    points.append(tip)
    ints = [_ints(p) for p in points]
    pygame.draw.lines(surface, OUTLINE, False, ints, width + 2)
    pygame.draw.lines(surface, color, False, ints, width)
    pygame.draw.lines(surface, shade(color, 50), False, ints[:-1], 1)
    pygame.draw.circle(surface, OUTLINE, _ints(tip), width + 1)
    pygame.draw.circle(surface, shade(color, 30), _ints(tip), width)
