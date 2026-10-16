"""Procedural effects drawn over the fight: projectile shapes, stretching limbs and blades.

Everything is drawn with a few pixels of pygame primitives, in the style A palette
(dark outline, two or three tones, a highlight), oriented along its direction of travel.
"""

from __future__ import annotations

import random

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


WINE = (150, 20, 52)
HAMON_EDGE = (255, 220, 110)


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
    elif look == "wine":
        _draw_wine(surface, pos, d)
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


def _draw_wine(surface, pos: Vec2, d: Vec2) -> None:
    """A jet of wine made sharp as a blade by Hamon: a red streak with a golden edge."""
    blit_glow(surface, radial_glow(8, (90, 66, 10)), (pos.x, pos.y))
    head, tail = pos + d * 4, pos - d * 7
    pygame.draw.line(surface, OUTLINE, _ints(head + d), _ints(tail - d), 4)
    pygame.draw.line(surface, WINE, _ints(head), _ints(tail), 2)
    pygame.draw.line(surface, HAMON_EDGE, _ints(head), _ints(pos), 1)
    surface.set_at(_ints(head), (255, 255, 230))


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


# Short-lived effects ------------------------------------------------------------------


class Effect:
    """Something drawn for `life` frames, then gone."""

    def __init__(self, life: int) -> None:
        self.age = 0
        self.life = life

    @property
    def done(self) -> bool:
        return self.age >= self.life

    @property
    def fade(self) -> float:
        return 1 - self.age / self.life

    def update(self) -> None:
        self.age += 1

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError


class Ring(Effect):
    """A shockwave: a ring of light sweeping out (added light, so it glows)."""

    def __init__(self, center: Vec2, color, speed: float, life: int, width: int = 2) -> None:
        super().__init__(life)
        self.center, self.color, self.speed, self.width = center, color, speed, width

    def draw(self, surface: pygame.Surface) -> None:
        radius = round(4 + self.age * self.speed)
        size = radius * 2 + 4
        layer = pygame.Surface((size, size))
        color = tuple(round(c * self.fade) for c in self.color)
        pygame.draw.circle(layer, color, (size // 2, size // 2), radius, self.width)
        x, y = _ints(self.center)
        surface.blit(layer, (x - size // 2, y - size // 2), special_flags=pygame.BLEND_ADD)


class Dust(Effect):
    """A puff of dust kicked up from the ground."""

    def __init__(
        self, pos: Vec2, velocity: Vec2, size: float, life: int = 18, color=(176, 166, 150)
    ) -> None:
        super().__init__(life)
        self.pos, self.velocity, self.size, self.color = pos, velocity, size, color

    def update(self) -> None:
        super().update()
        self.pos = self.pos + self.velocity
        self.velocity = self.velocity * 0.85

    def draw(self, surface: pygame.Surface) -> None:
        radius = max(1, round(self.size * (0.6 + self.age / self.life)))
        layer = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(
            layer, (*self.color, round(150 * self.fade)), (radius + 1, radius + 1), radius
        )
        x, y = _ints(self.pos)
        surface.blit(layer, (x - radius - 1, y - radius - 1))


class FocusLines(Effect):
    """Manga impact lines converging on a hit."""

    def __init__(self, center: Vec2, inner: float, outer: float, count: int, seed: int) -> None:
        super().__init__(6)
        self.center, self.inner, self.outer = center, inner, outer
        rng = random.Random(seed)
        self.angles = [rng.uniform(0, 6.283) for _ in range(count)]
        self.lengths = [rng.uniform(0.6, 1.0) for _ in range(count)]

    def draw(self, surface: pygame.Surface) -> None:
        grow = 1 + self.age * 0.15
        for angle, length in zip(self.angles, self.lengths, strict=True):
            d = Vec2.from_angle(angle)
            a = self.center + d * (self.inner * grow)
            b = self.center + d * (self.inner + (self.outer - self.inner) * length) * grow
            pygame.draw.line(surface, OUTLINE, _ints(a), _ints(b), 3)
            pygame.draw.line(surface, (255, 252, 236), _ints(a), _ints(b), 1)


class Flash(Effect):
    """A burst of white light on the point of impact."""

    def __init__(self, center: Vec2, radius: int, color=(255, 255, 255), life: int = 4) -> None:
        super().__init__(life)
        self.center, self.radius, self.color = center, radius, color

    def draw(self, surface: pygame.Surface) -> None:
        color = tuple(round(c * self.fade) for c in self.color)
        blit_glow(surface, radial_glow(self.radius, color, falloff=1.2), self.center)


class SpeedLines(Effect):
    """A few streaks behind something moving fast."""

    def __init__(self, pos: Vec2, direction: Vec2, color=(230, 226, 240), life: int = 8) -> None:
        super().__init__(life)
        self.pos, self.direction, self.color = pos, direction.normalized(), color

    def draw(self, surface: pygame.Surface) -> None:
        side = _side(self.direction)
        color = tuple(round(c * self.fade) for c in self.color)
        for i, (offset, length) in enumerate(((-6, 14), (-1, 20), (4, 12), (9, 16))):
            start = self.pos + side * offset - self.direction * (4 + i * 2 + self.age * 2)
            end = start - self.direction * length
            pygame.draw.line(surface, color, _ints(start), _ints(end), 1)


class EffectsLayer:
    def __init__(self) -> None:
        self.effects: list[Effect] = []
        self._seed = 0

    def add(self, effect: Effect) -> None:
        self.effects.append(effect)

    def dust(
        self, pos: Vec2, count: int, spread: float = 1.2, size: float = 3, color=None, life=18
    ) -> None:
        for i in range(count):
            angle = 6.283 * i / count + self._seed * 0.7
            self._seed += 1
            direction = Vec2.from_angle(angle, spread)
            velocity = Vec2(direction.x, direction.y * 0.45)
            self.add(Dust(pos + velocity * 2, velocity, size, life, color or (176, 166, 150)))

    def focus(self, center: Vec2, heavy: bool) -> None:
        self._seed += 1
        inner, outer, count = (10, 30, 14) if heavy else (7, 18, 9)
        self.add(FocusLines(center, inner, outer, count, self._seed))

    def update(self) -> None:
        for effect in self.effects:
            effect.update()
        self.effects = [e for e in self.effects if not e.done]

    def draw(self, surface: pygame.Surface) -> None:
        for effect in self.effects:
            effect.draw(surface)


def draw_flurry(
    surface: pygame.Surface,
    origin: Vec2,
    aim: Vec2,
    color,
    seed: int,
    length: float,
    count: int = 11,
    kind: str = "fists",
    size: int = 1,
) -> None:
    """A barrage: many ghostly arms and fists (or rapier thrusts) at once, a new random
    spread every frame, so it reads as hundreds of blows. `size` thickens everything
    (close-ups)."""
    rng = random.Random(seed)
    d = aim.normalized() if aim.length_sq() else Vec2(1, 0)
    side = _side(d)
    margin = 8 * size
    left = min(origin.x, origin.x + d.x * length) - length
    top = min(origin.y, origin.y + d.y * length) - length
    extent = round(length * 2 + 2 * margin)
    layer = pygame.Surface((extent, extent), pygame.SRCALPHA)
    offset = Vec2(left - margin, top - margin)

    def local(p: Vec2) -> tuple[int, int]:
        return _ints(p - offset)

    for _ in range(count):
        dist = rng.uniform(length * 0.35, length)
        lateral = rng.uniform(-1, 1) * dist * 0.5
        lift = rng.uniform(-7, 4) * size
        tip = origin + d * dist + side * lateral + Vec2(0, lift)
        tail = tip - d * rng.uniform(7, 13) * size
        if kind == "blade":
            pygame.draw.line(layer, (*OUTLINE, 200), local(origin), local(tip), 2 * size + 1)
            pygame.draw.line(layer, (*STEEL, 230), local(origin), local(tip), size)
            pygame.draw.circle(layer, (255, 255, 255, 255), local(tip), size)
            continue
        shoulder = origin + side * rng.choice((-3, -1, 1, 3)) * size
        pygame.draw.line(layer, (*shade(color, -60), 120), local(tail), local(tip), size)
        pygame.draw.line(layer, (*OUTLINE, 150), local(shoulder), local(tip), 4 * size)
        pygame.draw.line(layer, (*shade(color, -25), 170), local(shoulder), local(tip), 2 * size)
        radius = (3 if rng.random() < 0.4 else 2) * size
        pygame.draw.circle(layer, (*OUTLINE, 255), local(tip), radius + size)
        pygame.draw.circle(layer, (*color, 255), local(tip), radius)
        x, y = local(tip)
        pygame.draw.circle(layer, (*shade(color, 60), 255), (x - size, y - size), size)
    surface.blit(layer, _ints(offset))


def draw_thread(surface: pygame.Surface, a: Vec2, b: Vec2, color, tick: int) -> None:
    """A fine thread stretched between two points, with a glint running along it."""
    pygame.draw.line(surface, shade(color, -70), _ints(a), _ints(b), 1)
    t = ((tick * 0.03) + (a.x + b.y) * 0.01) % 1.0
    blit_glow(surface, radial_glow(3, shade(color, -20)), a + (b - a) * t)
