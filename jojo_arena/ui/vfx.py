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
    elif look == "ray":
        _draw_ray(surface, pos, d)
    elif look == "critter":
        _draw_critter(surface, pos, d)
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


def _draw_ray(surface, pos: Vec2, d: Vec2) -> None:
    """Sunlight focused through a bubble: a long thin ray, white at the core, gold at
    the edges, with the light it spills on the floor."""
    blit_glow(surface, radial_glow(9, (96, 84, 20)), (pos.x, pos.y))
    head, tail = pos + d * 7, pos - d * 9
    pygame.draw.line(surface, (240, 208, 60), _ints(head), _ints(tail), 3)
    pygame.draw.line(surface, (255, 255, 255), _ints(head), _ints(pos - d * 5), 1)
    surface.set_at(_ints(head), (255, 255, 255))


def _draw_critter(surface, pos: Vec2, d: Vec2) -> None:
    """A small animal running at you: a body, two ears, and a tail curled over its back.

    Kars turns a hand into a flesh-eating squirrel; this is what the squirrel looks like
    from above, at six pixels."""
    side = _side(d)
    head = pos + d * 2.5
    body = [pos - d * 2 + side * 2, head + side * 1.4, head - side * 1.4, pos - d * 2 - side * 2]
    pygame.draw.polygon(surface, OUTLINE, [_ints(p + d * 0.6) for p in body])
    pygame.draw.polygon(surface, (142, 86, 46), [_ints(p) for p in body])
    for way in (1, -1):
        ear = head + side * way * 1.6 + d * 0.6
        surface.fill(OUTLINE, (round(ear.x), round(ear.y) - 1, 1, 1))
    surface.set_at(_ints(head + d * 0.5), (240, 220, 160))  # the teeth
    # The tail, curled back over the body.
    tail = [
        pos - d * 3,
        pos - d * 5 + side * 1.5,
        pos - d * 4.5 + side * 3.5,
        pos - d * 2 + side * 4,
    ]
    pygame.draw.lines(surface, OUTLINE, False, [_ints(p) for p in tail], 3)
    pygame.draw.lines(surface, (190, 134, 80), False, [_ints(p) for p in tail], 1)


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


def _swirl(surface: pygame.Surface, center: Vec2, radius: float, turn: float, color, pale) -> None:
    """One vortex seen from above: three arms of air winding into an eye, flattened a
    little because the camera is not straight overhead."""
    for arm in range(3):
        points = []
        for step in range(7):
            far = 0.25 + 0.75 * step / 6
            angle = turn + arm * math.tau / 3 + far * 2.6
            points.append(
                _ints(
                    center
                    + Vec2(math.cos(angle) * radius * far, math.sin(angle) * radius * far * 0.55)
                )
            )
        pygame.draw.lines(surface, OUTLINE, False, points, 3)
        pygame.draw.lines(surface, pale, False, points, 1)
    box = pygame.Rect(0, 0, round(radius * 2), max(2, round(radius * 1.1)))
    box.center = _ints(center)
    pygame.draw.ellipse(surface, color, box, 1)
    pygame.draw.circle(surface, OUTLINE, _ints(center), 2)
    pygame.draw.circle(surface, (255, 255, 255), _ints(center), 1)


def draw_shock(surface: pygame.Surface, center: Vec2, radius: float, tick: int, color) -> None:
    """A blow that lands on the floor: rings running out across the ground, cracks under
    them, and the dust they throw up."""
    pale = tuple(min(255, c + 60) for c in color)
    for ring in range(3):
        grow = radius * (0.45 + 0.28 * ring)
        box = pygame.Rect(0, 0, round(grow * 2), max(3, round(grow * 0.85)))
        box.center = _ints(center)
        pygame.draw.ellipse(surface, OUTLINE, box.inflate(2, 2), 3)
        pygame.draw.ellipse(surface, pale if ring == 0 else color, box, 1)
    for i in range(7):
        angle = math.tau * i / 7 + (tick % 7) * 0.1
        start = center + Vec2(math.cos(angle) * radius * 0.3, math.sin(angle) * radius * 0.26)
        end = center + Vec2(math.cos(angle) * radius * 0.95, math.sin(angle) * radius * 0.8)
        pygame.draw.line(surface, OUTLINE, _ints(start), _ints(end), 3)
        pygame.draw.line(surface, pale, _ints(start), _ints(end), 1)
    blit_glow(
        surface, radial_glow(round(radius * 0.7), tuple(c // 2 for c in color)), _ints(center)
    )


def draw_vortices(
    surface: pygame.Surface,
    origin: Vec2,
    aim: Vec2,
    tick: int,
    length: float,
    color,
    grow: float = 1.0,
    width: float = 12.0,
) -> None:
    """Two tornadoes, one spun up by each forearm. `grow` is how far the move has wound
    up: at 0 the forearms are whirling at his sides and there is barely a draught, at 1
    both storms are out at full length, swallowing everything between them."""
    d = aim.normalized() if aim.length_sq() else Vec2(1, 0)
    side = _side(d)
    reach = max(8.0, length * grow)
    mouth = 3.0 + (width - 3.0) * grow
    pale = tuple(min(255, c + 80) for c in color)
    deep = tuple(c // 2 for c in color)
    count = max(2, min(6, round(reach / 26)))
    for which, offset in enumerate((-7.0, 7.0)):
        base = origin + side * offset
        spin = tick * 0.32 + which * math.pi
        trail = [_ints(base)]
        for i in range(count):
            t = (i + 1) / count
            center = base + d * (reach * t) - Vec2(0, 4 + t * 10)
            radius = (3.0 + (mouth - 3.0) * t) * (0.85 + 0.15 * math.sin(tick * 0.3 + i))
            trail.append(_ints(center))
            _swirl(surface, center, radius, spin + i * 0.9, color, pale)
            if grow >= 1.0:  # grit torn off the floor, riding round the outside
                angle = spin * 1.9 + i * 1.7
                grit = center + Vec2(math.cos(angle) * radius * 1.2, math.sin(angle) * radius * 0.7)
                pygame.draw.circle(surface, (255, 255, 255), _ints(grit), 1)
        pygame.draw.lines(surface, deep, False, trail, 1)  # the draught between them
    glow = radial_glow(round(10 + reach * 0.22), (50, 70, 80))
    blit_glow(surface, glow, _ints(origin + d * (reach * 0.5)))


def _fill_shape(surface: pygame.Surface, points, color, alpha: int) -> None:
    """A see-through polygon: the body of something you can still see the floor through."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    left, top = min(xs) - 1, min(ys) - 1
    size = (max(2, max(xs) - left + 2), max(2, max(ys) - top + 2))
    layer = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.polygon(layer, (*color, alpha), [(x - left, y - top) for x, y in points])
    surface.blit(layer, (left, top))


def draw_blade_fan(
    surface: pygame.Surface, start: Vec2, aim: Vec2, length: float, spread: float, tick: int, color
) -> None:
    """A sheet of light blades thrown out at once, fanned across everything in front."""
    d = aim.normalized() if aim.length_sq() else Vec2(1, 0)
    side = _side(d)
    pale = tuple(min(255, c + 70) for c in color)
    for i in range(9):
        offset = (i - 4) / 4 * spread
        out = 0.55 + 0.45 * ((i * 3 + tick) % 7) / 6
        base = start + side * (offset * 0.35) + Vec2(0, offset * 0.12)
        tip = base + d * (length * out) + side * (offset * 0.5)
        pygame.draw.line(surface, OUTLINE, _ints(base), _ints(tip), 4)
        pygame.draw.line(surface, color, _ints(base), _ints(tip), 2)
        pygame.draw.line(surface, (255, 255, 255), _ints(base + (tip - base) * 0.6), _ints(tip), 1)
        pygame.draw.circle(surface, pale, _ints(tip), 2)
    blit_glow(
        surface,
        radial_glow(round(16 + length * 0.12), tuple(c // 2 for c in color)),
        _ints(start + d * (length * 0.4)),
    )


def draw_wind_beam(
    surface: pygame.Surface, start: Vec2, aim: Vec2, length: float, tick: int, color
) -> None:
    """The air stream out of a horn: a straight razor of compressed air with turbulence
    boiling off both sides of it, and the split it leaves in the air at the far end."""
    d = aim.normalized() if aim.length_sq() else Vec2(1, 0)
    side = _side(d)
    tip = start + d * length
    # The horn itself, out of his forehead: a drill, and the stream leaves its point.
    horn = [
        _ints(start - d * 3 + side * 4),
        _ints(start + d * 9),
        _ints(start - d * 3 - side * 4),
    ]
    pygame.draw.polygon(surface, OUTLINE, horn)
    pygame.draw.polygon(surface, (214, 198, 150), horn, 1)
    for ring in range(3):
        along = start + d * (ring * 3)
        pygame.draw.line(
            surface,
            (120, 104, 70),
            _ints(along + side * (3.4 - ring)),
            _ints(along - side * (3.4 - ring)),
            1,
        )
    start = start + d * 9
    tip = start + d * length
    pygame.draw.line(surface, OUTLINE, _ints(start), _ints(tip), 7)
    pygame.draw.line(surface, color, _ints(start), _ints(tip), 5)
    pygame.draw.line(surface, (220, 245, 255), _ints(start), _ints(tip), 3)
    pygame.draw.line(surface, (255, 255, 255), _ints(start), _ints(tip), 1)
    steps = max(4, round(length / 14))
    for step in range(steps):
        t = (step + (tick % 6) / 6) / steps
        swell = 4 + 7 * math.sin(t * 3.0)
        axis = start + d * (length * t)
        for way in (1, -1):
            curl = [
                _ints(axis + side * (swell * way) - d * 6),
                _ints(axis + side * (swell * 1.5 * way)),
                _ints(axis + side * (swell * way) + d * 7),
            ]
            pygame.draw.lines(surface, color, False, curl, 1)
    # Where it lands, the air itself is split in two.
    for way in (1, -1):
        crack = [
            _ints(tip),
            _ints(tip + d * 7 + side * (9 * way)),
            _ints(tip + d * 2 + side * (18 * way)),
        ]
        pygame.draw.lines(surface, (255, 255, 255), False, crack, 1)
    blit_glow(surface, radial_glow(14, (90, 120, 130)), _ints(start))
    blit_glow(surface, radial_glow(18, (120, 150, 160)), _ints(tip))


def draw_cables(
    surface: pygame.Surface, start: Vec2, aim: Vec2, length: float, spread: float, tick: int
) -> None:
    """Steel cables thrown out in a fan, taut, each ending in a hooked weight: the trap
    is already laid across everything in front of him."""
    d = aim.normalized() if aim.length_sq() else Vec2(1, 0)
    side = _side(d)
    for i in range(5):
        offset = (i - 2) / 2 * spread
        out = min(1.0, (tick % 7) / 7 + 0.55)  # they snap taut, then thrum
        end = start + d * (length * out) + side * offset
        sag = side * (offset * 0.15) + Vec2(0, 2 + abs(offset) * 0.1)
        mid = (start + end) * 0.5 + sag
        curve = [_ints(start), _ints(mid), _ints(end)]
        pygame.draw.lines(surface, OUTLINE, False, curve, 3)
        pygame.draw.lines(surface, (214, 206, 186), False, curve, 1)
        pygame.draw.circle(surface, OUTLINE, _ints(end), 3)
        pygame.draw.circle(surface, (150, 142, 126), _ints(end), 2)
        pygame.draw.line(surface, (240, 236, 220), _ints(end), _ints(end + d * 4), 1)
    blit_glow(surface, radial_glow(12, (80, 76, 60)), _ints(start + d * 6))


def draw_blood_jet(
    surface: pygame.Surface, start: Vec2, aim: Vec2, length: float, tick: int
) -> None:
    """Boiling blood pumped out of a vein: a thick dark jet, orange where it is hottest,
    spitting drops and steam the whole way along."""
    d = aim.normalized() if aim.length_sq() else Vec2(1, 0)
    side = _side(d)
    points, steps = [], max(4, round(length / 10))
    for step in range(steps + 1):
        t = step / steps
        wobble = math.sin(tick * 0.4 + t * 5.0) * (2 + 4 * t)
        points.append(_ints(start + d * (length * t) + side * wobble))
    pygame.draw.lines(surface, OUTLINE, False, points, 7)
    pygame.draw.lines(surface, (120, 16, 24), False, points, 5)
    pygame.draw.lines(surface, (198, 42, 30), False, points, 3)
    pygame.draw.lines(surface, (255, 166, 60), False, points, 1)
    for i, point in enumerate(points):
        if (i + tick // 2) % 3:
            continue
        drop = Vec2(*point) + side * ((i % 2 * 2 - 1) * (4 + i)) - Vec2(0, 3 + i)
        pygame.draw.circle(surface, (198, 42, 30), _ints(drop), 2)
        surface.set_at(_ints(drop - Vec2(0, 2)), (255, 196, 120))
    blit_glow(surface, radial_glow(13, (120, 50, 20)), points[0])
    blit_glow(surface, radial_glow(10, (140, 60, 20)), points[-1])


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


# Status effects: what a body looks like while something keeps working on it ------------

FLAME = ((216, 84, 28), (240, 144, 28), (255, 224, 112))
FROST = ((90, 154, 216), (154, 216, 255), (255, 255, 255))
CURRENT = ((240, 208, 32), (255, 251, 200))


def draw_burning(surface: pygame.Surface, center: Vec2, height: float, tick: int) -> None:
    """Flames standing up off a body: three tongues, each on its own rhythm, leaning the
    way a flame leans as it rises."""
    dark, mid, pale = FLAME
    # Along the body and at the feet, never over the face: the fighter has to stay
    # readable while he burns.
    for i, (side, level) in enumerate(((-1, 0.12), (1, 0.38), (-1, 0.62))):
        phase = tick * 0.34 + i * 2.1
        x = center.x + side * 5 + math.sin(phase) * 1.6
        base = center.y - height * level
        tall = 5 + round(2.5 * (1 + math.sin(phase * 1.7)))
        lean = math.sin(phase * 0.8) * 1.8
        tip = Vec2(x + lean, base - tall)
        pygame.draw.line(surface, dark, (round(x), round(base)), _ints(tip), 3)
        pygame.draw.line(surface, mid, (round(x), round(base)), _ints(tip), 1)
        surface.fill(pale, (round(tip.x), round(tip.y), 1, 1))
    glow = radial_glow(round(height * 0.5), (72, 24, 4))
    blit_glow(surface, glow, center + Vec2(0, -height * 0.4))


def draw_frozen(surface: pygame.Surface, center: Vec2, height: float, tick: int) -> None:
    """Frost on a body: little crystals that catch the light one after another."""
    cold, ice, white = FROST
    for i in range(5):
        angle = math.tau * i / 5 + tick * 0.02
        spot = center + Vec2(math.cos(angle) * 7, -height * 0.5 + math.sin(angle) * 6)
        lit = (tick // 6 + i) % 5 == 0
        color = white if lit else (ice if i % 2 else cold)
        x, y = _ints(spot)
        surface.fill(color, (x - 1, y, 3, 1))
        surface.fill(color, (x, y - 1, 1, 3))
    blit_glow(
        surface, radial_glow(round(height * 0.45), (12, 36, 64)), center + Vec2(0, -height * 0.45)
    )


def draw_current(surface: pygame.Surface, center: Vec2, height: float, tick: int) -> None:
    """A current running over a body: short arcs that jump somewhere else every frame."""
    gold, white = CURRENT
    rng = random.Random(tick // 2)
    for _ in range(3):
        top = center + Vec2(rng.uniform(-6, 6), -height * rng.uniform(0.25, 0.85))
        point = top
        for step in range(3):
            point = point + Vec2(rng.uniform(-4, 4), rng.uniform(2, 5))
            color = white if step == 0 else gold
            pygame.draw.line(surface, color, _ints(top), _ints(point), 1)
            top = point
    if (tick // 3) % 2 == 0:
        blit_glow(
            surface, radial_glow(round(height * 0.4), (56, 48, 8)), center + Vec2(0, -height * 0.4)
        )


STATUS_DRAWINGS = {"burn": draw_burning, "chill": draw_frozen, "shock": draw_current}


def draw_statuses(surface: pygame.Surface, center: Vec2, height: float, names, tick: int) -> None:
    """Whatever is burning, freezing or crackling on this body, drawn over it."""
    for name in names:
        drawing = STATUS_DRAWINGS.get(name)
        if drawing is not None:
            drawing(surface, center, height, tick)
