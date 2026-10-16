"""Procedural effects drawn over the fight: projectile shapes, stretching limbs and blades.

Everything is drawn with a few pixels of pygame primitives, in the style A palette
(dark outline, two or three tones, a highlight), oriented along its direction of travel.
"""

from __future__ import annotations

import math
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
HAIR = (40, 30, 52)
HAIR_SHEEN = (150, 120, 190)
CHAIN = (170, 170, 184)
CHAIN_DARK = (100, 100, 112)
HAMON_EDGE = (255, 220, 110)
SCARF = (168, 40, 58)
SCARF_LIGHT = (226, 96, 104)


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
    elif look == "hat":
        _draw_hat(surface, pos, d)
    elif look == "clacker":
        _draw_clacker(surface, pos, d)
    elif look == "grenade":
        _draw_grenade(surface, pos)
    elif look == "bubble":
        _draw_bubble(surface, pos, radius)
    elif look == "bullet":
        _draw_bullet(surface, pos, d)
    elif look == "spark":
        _draw_spark(surface, pos, d)
    elif look == "jet":
        _draw_jet(surface, pos, d, aura)
    elif look == "wave":
        _draw_wave(surface, pos, d)
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


def draw_chain(surface: pygame.Surface, start: Vec2, end: Vec2, sag: float = 0.0) -> None:
    """A chain of iron links from `start` to `end`, sagging a little in the middle."""
    length = (end - start).length()
    if length < 1:
        return
    count = max(2, round(length / 4))
    for i in range(count + 1):
        t = i / count
        point = start + (end - start) * t + Vec2(0, math.sin(t * math.pi) * sag)
        x, y = _ints(point)
        if i % 2:
            pygame.draw.rect(surface, OUTLINE, (x - 2, y - 1, 4, 3))
            surface.fill(CHAIN_DARK, (x - 1, y, 2, 1))
        else:
            pygame.draw.rect(surface, OUTLINE, (x - 1, y - 2, 3, 4))
            surface.fill(CHAIN, (x, y - 1, 1, 2))


def _draw_hat(surface, pos: Vec2, d: Vec2) -> None:
    """Speedwagon's bowler, spinning flat, the blades in its brim catching the light."""
    spin = (pos.x + pos.y) * 0.35
    center = _ints(pos)
    pygame.draw.ellipse(surface, OUTLINE, (center[0] - 7, center[1] - 4, 15, 9))
    pygame.draw.ellipse(surface, (30, 28, 40), (center[0] - 6, center[1] - 3, 13, 7))
    pygame.draw.ellipse(surface, (60, 52, 90), (center[0] - 3, center[1] - 3, 7, 5))
    for k in range(3):
        angle = spin + k * math.tau / 3
        tip = pos + Vec2(math.cos(angle) * 7, math.sin(angle) * 4)
        surface.set_at(_ints(tip), (240, 240, 255))


def _draw_clacker(surface, pos: Vec2, d: Vec2) -> None:
    """Hamon clackers: two steel balls on a cord, whirling around their middle."""
    spin = (pos.x + pos.y) * 0.4
    arm = Vec2(math.cos(spin), math.sin(spin) * 0.6) * 5
    a, b = pos + arm, pos - arm
    blit_glow(surface, radial_glow(8, (80, 64, 12)), (pos.x, pos.y))
    pygame.draw.line(surface, OUTLINE, _ints(a), _ints(b), 3)
    pygame.draw.line(surface, HAMON_EDGE, _ints(a), _ints(b), 1)
    for ball in (a, b):
        pygame.draw.circle(surface, OUTLINE, _ints(ball), 3)
        pygame.draw.circle(surface, STEEL_DARK, _ints(ball), 2)
        surface.set_at(_ints(ball + Vec2(-1, -1)), STEEL)


GRENADE = (70, 96, 52)
GRENADE_DARK = (40, 58, 32)


def _draw_grenade(surface, pos: Vec2) -> None:
    """A pineapple grenade, pin pulled, rolling on the ground."""
    x, y = _ints(pos)
    pygame.draw.ellipse(surface, OUTLINE, (x - 4, y - 5, 9, 10))
    pygame.draw.ellipse(surface, GRENADE, (x - 3, y - 4, 7, 8))
    for row in (-2, 1):
        surface.fill(GRENADE_DARK, (x - 2, y + row, 5, 1))
    surface.fill(OUTLINE, (x - 1, y - 7, 3, 2))
    surface.fill(STEEL_DARK, (x, y - 7, 1, 1))
    surface.set_at((x - 1, y - 3), (150, 180, 120))


def _draw_bubble(surface, pos: Vec2, radius: float) -> None:
    """A soap bubble charged with Hamon: a thin iridescent ring with a bright glint."""
    r = max(3, round(radius))
    center = _ints(pos)
    blit_glow(surface, radial_glow(r + 4, (40, 34, 10)), (pos.x, pos.y))
    pygame.draw.circle(surface, (120, 200, 230), center, r, 1)
    hue = int(pos.x + pos.y) % 3
    tint = ((240, 150, 220), (150, 240, 200), (250, 230, 140))[hue]
    pygame.draw.arc(surface, tint, (center[0] - r, center[1] - r, 2 * r, 2 * r), 3.6, 5.6, 1)
    surface.set_at((center[0] - r // 2, center[1] - r // 2), (255, 255, 255))


def _draw_bullet(surface, pos: Vec2, d: Vec2) -> None:
    """A tommy gun bullet: a short bright streak."""
    head, tail = pos + d * 2, pos - d * 5
    pygame.draw.line(surface, (120, 90, 30), _ints(head), _ints(tail), 2)
    pygame.draw.line(surface, (255, 236, 160), _ints(head), _ints(pos), 1)


def _draw_spark(surface, pos: Vec2, d: Vec2) -> None:
    """A Hamon spark running along a thread: a short zigzag of light."""
    blit_glow(surface, radial_glow(7, (90, 70, 10)), (pos.x, pos.y))
    side = _side(d)
    points = [pos - d * 5, pos - d * 2 + side * 2, pos + d * 1 - side * 2, pos + d * 4]
    pygame.draw.lines(surface, (255, 236, 120), False, [_ints(p) for p in points], 1)
    surface.set_at(_ints(pos + d * 4), (255, 255, 255))


def _draw_jet(surface, pos: Vec2, d: Vec2, aura) -> None:
    """A pressurized jet from the eyes: a long thin streak, white-hot in the core."""
    head, tail = pos + d * 5, pos - d * 10
    pygame.draw.line(surface, shade(aura, -40), _ints(head), _ints(tail), 2)
    pygame.draw.line(surface, (255, 255, 255), _ints(head), _ints(pos - d * 4), 1)


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


def _draw_wave(surface: pygame.Surface, pos: Vec2, d: Vec2) -> None:
    """A crest of burning Hamon sweeping the floor: an arc bowed the way it travels,
    with two fainter ones trailing behind it so it reads as moving."""
    side = _side(d)

    def arc(center: Vec2, span: float, bow: float, color, width: int) -> None:
        points = []
        for step in range(-4, 5):
            t = step / 4
            points.append(_ints(center + side * (span * t) + d * (bow * (1 - t * t))))
        pygame.draw.lines(surface, OUTLINE, False, points, width + 2)
        pygame.draw.lines(surface, color, False, points, width)

    arc(pos - d * 7, 8.0, 3.0, (190, 70, 20), 1)  # the tail of the flame
    arc(pos - d * 3, 11.0, 4.0, (255, 140, 40), 2)
    arc(pos, 13.0, 5.0, HAMON_EDGE, 2)  # the crest itself
    blit_glow(surface, radial_glow(20, (130, 80, 16)), _ints(pos))


def draw_stone_mask(surface: pygame.Surface, center: Vec2, scale: float, stone=None) -> None:
    """A stone mask seen face on, the Red Stone set in its brow: the thing that turns a
    Pillar Man into the other thing. `scale` 0 to 1 grows it into place."""
    if scale <= 0:
        return
    stone = stone or (210, 204, 186)
    w, h = round(9 * scale), round(12 * scale)
    if w < 2 or h < 3:
        return
    cx, cy = round(center.x), round(center.y)
    face = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    pygame.draw.ellipse(surface, OUTLINE, face.inflate(2, 2))
    pygame.draw.ellipse(surface, stone, face)
    if h >= 8:
        # The eye holes, and the Red Stone of Aja above them.
        for dx in (-w // 4, w // 4):
            surface.fill(OUTLINE, (cx + dx - 1, cy - h // 6, 2, 2))
        surface.fill((23, 18, 31), (cx - 1, face.y + 1, 3, 3))
        surface.fill((226, 60, 70), (cx, face.y + 2, 1, 1))
    blit_glow(surface, radial_glow(round(16 * scale), (120, 96, 40)), (cx, cy))


def draw_reach(
    surface: pygame.Surface, start: Vec2, tip: Vec2, color, kind: str = "limb", width: int = 2
) -> None:
    """Something stretching from `start` to `tip`: a finger, a tentacle, a rapier.

    `kind` is "limb" (rounded, the user's color), "tentacle" (wavy) or "blade" (steel).
    """
    if (tip - start).length_sq() < 1:
        return
    if kind == "blade_hair":
        # Hair riding along the blade: two strands fanned either side of the steel, in
        # the violet sheen so they read against a dark floor, then the blade over them.
        d = (tip - start).normalized()
        side = _side(d)
        length = (tip - start).length()
        steps = max(3, round(length / 3))
        for strand in (-3.4, 3.4):
            points = []
            for i in range(steps + 1):
                t = i / steps
                wave = math.sin(t * 7 + strand) * 2.2 * (1 - t * 0.4)
                spread = strand * (1 - t * 0.55) + wave
                points.append(_ints(start + (tip - start) * t + side * spread))
            pygame.draw.lines(surface, OUTLINE, False, points, 3)
            pygame.draw.lines(surface, HAIR_SHEEN, False, points, 1)
        draw_reach(surface, start, tip, color, "blade", width)
        return
    if kind == "hair":
        # A lock of hair: three thin wavy strands, black with a violet sheen.
        d = (tip - start).normalized()
        side = _side(d)
        length = (tip - start).length()
        for strand in (-1.5, 0.0, 1.5):
            points = []
            steps = max(3, round(length / 3))
            for i in range(steps + 1):
                t = i / steps
                wave = math.sin(t * 9 + strand * 2) * 1.6 * (1 - t * 0.5)
                points.append(_ints(start + (tip - start) * t + side * (strand + wave)))
            pygame.draw.lines(surface, OUTLINE, False, points, 3)
            pygame.draw.lines(surface, HAIR, False, points, 1)
        surface.set_at(_ints(tip), HAIR_SHEEN)
        return
    if kind == "chain":
        draw_chain(surface, start, tip)
        return
    if kind == "lens":
        # A bubble held up as a lens: sunlight focused through it into one hot ray.
        d = (tip - start).normalized()
        lens = start + d * 6
        pygame.draw.line(surface, (255, 200, 80), _ints(lens), _ints(tip), width + 1)
        pygame.draw.line(surface, (255, 255, 230), _ints(lens), _ints(tip), 1)
        _draw_bubble(surface, lens, 4)
        blit_glow(surface, radial_glow(8 + 2 * width, (120, 90, 20)), _ints(tip))
        return
    if kind in ("scarf", "scarf_spear"):
        # Lisa Lisa's scarf: a red ribbon rippling with Hamon, or held stiff as a spear.
        d = (tip - start).normalized()
        side = _side(d)
        length = (tip - start).length()
        steps = max(3, round(length / 3))
        points = []
        for i in range(steps + 1):
            t = i / steps
            wave = 0.0 if kind == "scarf_spear" else math.sin(t * 10 - length * 0.2) * 2.2 * t
            points.append(_ints(start + (tip - start) * t + side * wave))
        pygame.draw.lines(surface, OUTLINE, False, points, width + 2)
        pygame.draw.lines(surface, SCARF, False, points, width)
        pygame.draw.lines(surface, SCARF_LIGHT, False, points[: len(points) * 2 // 3], 1)
        if kind == "scarf_spear":
            head = [tip + d * 4, tip + side * 3, tip - side * 3]
            pygame.draw.polygon(surface, OUTLINE, [_ints(q) for q in head])
            pygame.draw.polygon(
                surface,
                HAMON_EDGE,
                [_ints(q) for q in (tip + d * 3, tip + side * 2, tip - side * 2)],
            )
        blit_glow(surface, radial_glow(7, (90, 70, 10)), _ints(tip))
        return
    if kind == "beam":
        # Two jets, one from each eye, white hot in the core.
        d = (tip - start).normalized()
        side = _side(d) * 1.5
        for offset in (side, side * -1):
            a, b = start + offset, tip + offset
            pygame.draw.line(surface, shade(color, -40), _ints(a), _ints(b), width + 1)
            pygame.draw.line(surface, (255, 255, 255), _ints(a), _ints(b), 1)
        blit_glow(surface, radial_glow(6 + 2 * width, tuple(c // 2 for c in color)), _ints(tip))
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


def draw_vortices(
    surface: pygame.Surface, origin: Vec2, aim: Vec2, tick: int, length: float, color
) -> None:
    """Two tornadoes turning in front of a fighter, one per forearm: the air between
    his arms, not his fists. They lean along `aim` and spin with `tick`."""
    d = aim.normalized() if aim.length_sq() else Vec2(1, 0)
    side = _side(d)
    for which, offset in enumerate((-5.0, 5.0)):
        base = origin + side * offset
        spin = tick * 0.55 + which * math.pi
        points = []
        for step in range(11):
            t = step / 10
            radius = 2.5 + 7.5 * t
            along = d * (length * t)
            swirl = side * (math.sin(spin + t * 7.0) * radius)
            points.append(_ints(base + along + swirl - Vec2(0, t * 4)))
        pygame.draw.lines(surface, OUTLINE, False, points, 4)
        pygame.draw.lines(surface, color, False, points, 2)
        pygame.draw.lines(surface, (255, 255, 255), False, points[-4:], 1)
    blit_glow(surface, radial_glow(round(14 + length * 0.3), (60, 80, 90)), _ints(origin + d * 6))


def draw_gun(surface: pygame.Surface, start: Vec2, aim: Vec2, tick: int) -> None:
    """A submachine gun held out at the hip: body, drum, barrel, and the muzzle lit."""
    d = aim.normalized() if aim.length_sq() else Vec2(1, 0)
    side = _side(d)
    body_a, body_b = start + d * 2, start + d * 11
    pygame.draw.line(surface, OUTLINE, _ints(body_a - side), _ints(body_b - side), 5)
    pygame.draw.line(surface, (70, 66, 78), _ints(body_a), _ints(body_b), 3)
    pygame.draw.line(surface, (120, 112, 126), _ints(body_a), _ints(body_b), 1)
    drum = start + d * 6 + side * 3
    pygame.draw.circle(surface, OUTLINE, _ints(drum), 4)
    pygame.draw.circle(surface, (96, 88, 104), _ints(drum), 3)
    muzzle = start + d * 18
    pygame.draw.line(surface, OUTLINE, _ints(body_b), _ints(muzzle), 4)
    pygame.draw.line(surface, (150, 142, 158), _ints(body_b), _ints(muzzle), 2)
    pygame.draw.line(surface, (90, 62, 40), _ints(start - d * 2), _ints(start + d * 3), 3)  # stock
    if tick % 4 < 2:  # the muzzle flash, every other pair of frames
        blit_glow(surface, radial_glow(10, (150, 110, 30)), _ints(muzzle))
        pygame.draw.circle(surface, (255, 236, 170), _ints(muzzle + d * 2), 2)


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
