"""Costume parts. Each one turns a skeleton plus its settings into pixel parts.

Every part has a `material` (a palette entry). In a look file:

    [[parts]]
    type = "coat"
    material = "coat"
    length = 0.85

Head pieces (hair, headwear, earrings) are measured in "head units": a head of
radius 7, scaled to the real head size, so they fit any body shape.

Drawing order (z): belts 30.5, coat body 31, collar 49-51, nape hair 49/53,
hair 54-55, headbands 55.5, headwear 56-57, bangs and earrings 57-58.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable

from .look import Look
from .raster import OUTLINE, Part, Pixel, Point, capsule, disc, points, polygon, rect
from .skeleton import Skeleton


def _center(q: Pixel) -> Point:
    return q[0] + 0.5, q[1] + 0.5


def _rel(sk: Skeleton, q: Pixel) -> Point:
    """Pixel center relative to the head center, in head units."""
    x, y = _center(q)
    return (x - sk.head[0]) / sk.k, (y - sk.head[1]) / sk.k


def _mirror(sk: Skeleton, pixels: set[Pixel]) -> set[Pixel]:
    """Mirror pixels across the head's vertical axis."""
    axis = round(2 * sk.head[0])
    return {(axis - 1 - x, y) for x, y in pixels}


# Hair --------------------------------------------------------------------------------


def hair(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """style: short | long | tower | spiky | swept (volume swept up and back) | crest
    (a fin on top of a helmet; crest_color).

    Options (head units): volume, length (long), height (tower, crest), back_length (locks over
    the nape); bangs = curl | fringe, bangs_side = left | right (seen from the front),
    bangs_length, bangs_width and bangs_spread (curl: distance from the face).
    """
    mat = p["material"]
    style = p.get("style", "short")
    k = sk.k
    at = sk.at
    shine = points([at(-3, -6), at(-2, -6)])
    volume = p.get("volume", 7.7) * k

    def rel(q: Pixel) -> Point:
        return _rel(sk, q)

    if sk.view == "down":
        top = {q for q in disc(*at(0, -0.6), volume) if rel(q)[1] < -2.5}
        sides = {q for q in disc(*at(0, 0), volume) if abs(rel(q)[0]) >= 5.5 and rel(q)[1] < 1.5}
        main = top | sides
    elif sk.view == "up":
        main = {q for q in disc(*at(0, -0.3), volume) if rel(q)[1] < 5.5}
    else:
        # Profile: top, back, and the side of the head down to the ear (temple and
        # sideburn), so only the face stays bare.
        def covered(x: float, y: float) -> bool:
            return y < -2.5 or (x < 1.8 and y < 1.0) or (0 <= x < 2.2 and y < 3.5) or x < -1.5

        main = {q for q in disc(*at(-0.4, -0.6), volume) if covered(*rel(q)) and rel(q)[1] < 5.5}
    parts = [Part(mat, main, z=54, highlight=shine)]

    if style == "long":
        length = p.get("length", 10)
        if sk.view == "down":
            locks = capsule(*at(-6.5, -1), *at(-6.8, length), 2.1 * k)
            locks |= capsule(*at(6.5, -1), *at(6.8, length), 2.1 * k)
        elif sk.view == "up":
            locks = capsule(*at(0, 0), *at(0, length), 6.2 * k)
        else:
            locks = capsule(*at(-3.5, 0), *at(-5, length), 3.0 * k)
        parts.append(Part(mat, locks, z=53))
    elif style == "tower":
        h = p.get("height", 6)
        if sk.view == "right":
            corners = [(-6, -2), (3.5, -3), (3.5, -6 - h), (-6.5, -6 - h)]
        else:
            corners = [(-5.5, -3), (5.5, -3), (5.8, -6 - h), (-5.8, -6 - h)]
        block = polygon([at(*c) for c in corners])
        corner = points([at(-4, -5 - h), at(-3, -5 - h)])
        parts.append(Part(mat, block, z=55, highlight=corner))
    elif style == "spiky":
        spikes: set[Pixel] = set()
        for i in range(-2, 3):
            x = i * 3 - (1.5 if sk.view == "right" else 0)
            spikes |= polygon([at(x - 2.2, -5), at(x + 2.2, -5), at(x + i * 0.8, -11)])
        parts.append(Part(mat, spikes, z=53.5))
    elif style == "swept":
        if sk.view == "right":
            outline = [(4, -5), (1, -10), (-4, -11), (-8, -8.5), (-10, -5), (-8.5, -2), (-5, -4)]
            crest = polygon([at(*c) for c in outline])
            crest |= disc(*at(-6, -1.5), 3.2 * k)  # the rolled-up back
        else:
            # Wide volume on top, flicking up and out to one side.
            crest = {q for q in disc(*at(0.5, -4.2), 7.6 * k) if rel(q)[1] < -3}
            crest |= polygon([at(-2, -8), at(4, -12.5), at(9.5, -11), at(7, -6)])
            crest |= polygon([at(-6.5, -6), at(-4, -11), at(0, -9)])
        parts.append(Part(mat, crest, z=54.5, highlight=points([at(-2, -10)])))
    elif style == "crest":
        # A fin or plume along the top of the head (helmets). crest_color sets its color.
        h = p.get("height", 4)
        if sk.view == "right":
            fin = polygon(
                [at(2.5, -6.5), at(-5, -6), at(-6.5, -8.5 - h * 0.5), at(0, -10 - h * 0.7)]
            )
        else:
            fin = polygon([at(-1.3, -5), at(1.3, -5), at(0.9, -11 - h), at(-0.9, -11 - h)])
        parts.append(Part(p.get("crest_color", mat), fin, z=55))

    back_length = p.get("back_length", 0)
    if back_length and style != "long":
        if sk.view == "down":
            nape = capsule(*at(-5.2, 1), *at(-5.6, back_length), 1.8 * k)
            nape |= capsule(*at(5.2, 1), *at(5.6, back_length), 1.8 * k)
            parts.append(Part(mat, nape, z=49))
        elif sk.view == "up":
            parts.append(Part(mat, capsule(*at(0, 2), *at(0, back_length), 4.5 * k), z=53))
        else:
            parts.append(Part(mat, capsule(*at(-4, 1), *at(-4.6, back_length), 2.4 * k), z=53))

    bangs = p.get("bangs")
    side = 1 if p.get("bangs_side", "right") == "right" else -1
    if bangs == "curl":
        parts.append(_curl(sk, p, mat, side))
    elif bangs == "fringe" and sk.view != "up":
        if sk.view == "down":
            band = polygon([at(-5, -5), at(5, -5), at(5, -2), at(-5, -2)])
            bottom = max(q[1] for q in band)
            fringe = {q for q in band if not (q[1] == bottom and q[0] % 2)}
        else:
            fringe = polygon([at(2, -5), at(5.5, -5), at(5.5, -2.5), at(2, -2.5)])
        parts.append(Part(mat, fringe, z=55))
    return parts


def _curl(sk: Skeleton, p: dict, mat: str, side: int) -> Part:
    """A long lock leaving the forehead, hanging in an S away from the face, ending in a
    ringlet. bangs_spread pushes it further from the cheek (head units)."""
    at = sk.at
    k = sk.k
    length = p.get("bangs_length", 8)
    width = p.get("bangs_width", 1.1)
    spread = p.get("bangs_spread", 0.0)
    if sk.view == "down":
        path = [
            (2.5, -6),
            (4 + 0.6 * spread, -3.5),
            (5 + spread, 0),
            (3 + spread, 3.5),
            (5.6 + spread, length - 3.5),
        ]
        ring = (4.4 + spread, length - 1)
        path = [(side * x, y) for x, y in path]
        ring = (side * ring[0], ring[1])
        z = 57
    elif sk.view == "right":
        s = 0.6 * spread
        path = [(3.5, -6), (6 + 0.7 * s, -3), (7 + s, 1), (6.2 + s, 4), (7.2 + s, length - 3)]
        ring = (6.4 + s, length - 0.8)
        z = 57
    else:
        # From behind, the lock only shows beside the head, on the other side.
        s = 0.6 * spread
        path = [(-side * (6.8 + s), 0), (-side * (7.6 + s), length - 3)]
        ring = (-side * (7 + s), length - 0.8)
        z = 49
    strand: set[Pixel] = set()
    for i, (a, b) in enumerate(zip(path, path[1:], strict=False)):
        taper = 1 - 0.3 * i / max(1, len(path) - 2)  # thinner toward the tip
        strand |= capsule(*at(*a), *at(*b), width * taper * k)
    # The ringlet: a small loop of hair with a hole in the middle.
    strand |= disc(*at(*ring), 2.4 * k) - disc(*at(*ring), 1.0 * k)
    return Part(mat, strand, z=z)


# Headwear ----------------------------------------------------------------------------


def cap(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Peaked cap. Options: height (taller crown, head units), brim (default true),
    ragged_back (frayed locks under the back), ragged_color (their color, e.g. the hair),
    band (color of a band around the crown), badge (color) and badges (1 or 2).
    """
    mat = p["material"]
    k = sk.k
    at = sk.at
    shift = -0.5 if sk.view == "right" else 0.0
    lift = p.get("height", 0.0)
    crown = {q for q in disc(*at(shift, -1.6), 8.1 * k) if _rel(sk, q)[1] < -2.2}
    if lift:
        crown |= {q for q in disc(*at(shift, -1.6 - lift), 7.6 * k) if _rel(sk, q)[1] < -2.2}
    top = min(q[1] for q in crown)
    parts = [Part(mat, crown, z=56, highlight=points([at(-4, -8 - lift)]) & crown)]
    if p.get("ragged_back"):
        # Frayed locks under the cap, in the hair color if given (ragged_color).
        ragged = _ragged_back(sk) - crown
        parts.append(Part(p.get("ragged_color", mat), ragged, z=55.8))
    band = p.get("band")
    if band:
        ring = {q for q in crown if -3.9 <= _rel(sk, q)[1] < -2.2 and abs(_rel(sk, q)[0]) < 8}
        if sk.view == "up":
            ring = {q for q in ring if _rel(sk, q)[1] < -2.6}
        parts.append(Part(band, ring, z=56.5, tone=2))
    if p.get("brim", True):
        if sk.view == "down":
            parts.append(Part(mat, rect(*at(-6.5, -3), *at(5.5, -2)), z=57))
        elif sk.view == "right":
            parts.append(
                Part(mat, polygon([at(3, -3.6), at(10, -2.6), at(10, -1.6), at(3, -1.6)]), z=57)
            )
    badge = p.get("badge")
    if badge and sk.view != "up":
        y = (top + round(at(0, -3.9)[1])) / 2
        if sk.view == "down":
            spots = [at(-1.5, 0)] if p.get("badges", 1) == 1 else [at(-3, 0), at(1.5, 0)]
            for x, _ in spots:
                parts.append(
                    Part(
                        badge, rect(x, y - 1, x + 1, y), z=58, highlight={(round(x), round(y - 1))}
                    )
                )
        else:
            x = at(4, 0)[0]
            parts.append(Part(badge, rect(x, y - 1, x, y), z=58, tone=2))
    return parts


def _ragged_back(sk: Skeleton) -> set[Pixel]:
    """Jagged locks under the back of a cap, as if cap and hair were one piece."""
    at = sk.at
    if sk.view == "up":
        outline = [at(-8, -3)]
        x, i = -8.0, 0
        while x <= 8:
            outline.append(at(x, 4.5 if i % 2 else 0.5))
            x += 2.6
            i += 1
        outline.append(at(8, -3))
        return polygon(outline)
    if sk.view == "right":
        jag = [
            (-1, -4),
            (-8.5, -4),
            (-10, -1),
            (-8, 0.5),
            (-9.5, 3),
            (-6.5, 2.5),
            (-6.5, 5.5),
            (-4, 2.5),
            (-2, 0),
        ]
        return polygon([at(*c) for c in jag])
    left = polygon([at(-6.5, -3), at(-9, -1), at(-7.5, 1), at(-8.5, 3.5), at(-6, 2)])
    return left | _mirror(sk, left)


def headband(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Band around the forehead. Option: gem (color of an oval stone at the front)."""
    band = {q for q in disc(*sk.at(0, 0), 7.4 * sk.k) if -5.5 <= _rel(sk, q)[1] <= -3.5}
    parts = [Part(p["material"], band, z=55.5)]
    gem = p.get("gem")
    if gem and sk.view == "down":
        stone = polygon([sk.at(-1.3, -6.6), sk.at(1.3, -6.6), sk.at(1.3, -2.5), sk.at(-1.3, -2.5)])
        parts.append(Part(gem, stone, z=55.6, highlight={min(stone)}))
    elif gem and sk.view == "right":
        parts.append(Part(gem, points([sk.at(6.6, -5), sk.at(6.6, -4)]), z=55.6, tone=2))
    return parts


def mask(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """The face in another color than the head (helmet, mask). Option: top (head units)."""
    if sk.view == "up":
        return []
    top = p.get("top", -2.5)
    head = disc(*sk.at(0, 0), sk.head_r)
    if sk.view == "down":
        area = {q for q in head if _rel(sk, q)[1] > top and abs(_rel(sk, q)[0]) < 5.2}
    else:
        area = {q for q in head if _rel(sk, q)[1] > top and _rel(sk, q)[0] > 0.5}
    return [Part(p["material"], area, z=51)]


# Clothes -----------------------------------------------------------------------------


def coat(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Coat over the torso with a skirt down the legs.

    Options: length (0 = hips, 1 = feet), open (shows the torso color down the front),
    opening (width of that gap, px), flare (extra hem width, px), trail (extra flare
    behind, in profile), collar (high collar, default true), pins (collar pins color),
    buttons (color), lining (color of the inside of the flaps, seen when open),
    cuffs (color of the sleeve buttons).
    """
    mat = p["material"]
    length = p.get("length", 0.8)
    opened = p.get("open", False)
    gap = p.get("opening", 2.2) / 2
    flare = p.get("flare", 3.5)
    trail = p.get("trail", 1.5)
    (ta, tb, tr) = sk.torso
    cx = sk.center_x
    body = capsule(*ta, *tb, tr + 0.6)
    if opened and sk.view == "down":
        body = {q for q in body if abs(_center(q)[0] - cx) > gap}
    elif opened and sk.view == "right":
        front = max(q[0] for q in body)
        body = {q for q in body if q[0] < front - 1}
    parts = [Part(mat, body, z=31, merge=True)]

    feet_y = max(f[1] for f in sk.feet)
    top = sk.hip_y - 3
    bottom = sk.hip_y + length * (feet_y + 1 - sk.hip_y)
    span = max(1.0, bottom - top)
    lining = p.get("lining")
    if length > 0:
        if sk.view == "right":
            back = min(f[0] for f in sk.feet) - flare - trail - max(0.0, sk.lean)
            ahead = max(f[0] for f in sk.feet) + flare - 1
            skirt = polygon([(cx - tr - 0.6, top), (cx + tr, top), (ahead, bottom), (back, bottom)])
            parts.append(Part(mat, skirt, z=37, merge=True))
        else:
            left = min(f[0] for f in sk.feet) - flare
            right = max(f[0] for f in sk.feet) + flare
            skirt = polygon(
                [(cx - tr - 0.9, top), (cx + tr + 0.9, top), (right, bottom), (left, bottom)]
            )

            def split(q: Pixel) -> float:
                """Half-width of the front opening at this pixel's height: an upside-down V."""
                t = max(0.0, (_center(q)[1] - top) / span)
                return gap * 0.5 + (gap + 2) * t**1.2

            if sk.view == "down" and opened:
                inner = {q for q in skirt if abs(_center(q)[0] - cx) <= split(q) + 1.6}
                skirt = {q for q in skirt if abs(_center(q)[0] - cx) > split(q)}
                if lining:
                    # The flaps turn out toward the hem, showing the lining.
                    shown = {q for q in skirt & inner if _center(q)[1] > top + span * 0.45}
                    parts.append(Part(lining, shown, z=12.5))
            else:
                skirt = {
                    q for q in skirt if not (abs(_center(q)[0] - cx) < 0.6 and q[1] > bottom - 4)
                }
            parts.append(Part(mat, skirt, z=12, merge=True))

    hx = sk.head[0]
    r = sk.head_r
    shoulder = sk.shoulder_y
    if p.get("collar", True):
        if sk.view == "down":
            collar = polygon(
                [
                    (hx - r - 0.5, shoulder - 4),
                    (hx - 0.45 * r, shoulder - 1.5),
                    (hx - 0.55 * r, shoulder + 1.5),
                    (hx - r - 1, shoulder + 1),
                ]
            )
            parts.append(Part(mat, collar | _mirror(sk, collar), z=49))
        elif sk.view == "up":
            parts.append(Part(mat, rect(hx - 0.85 * r, shoulder - 3, hx + 0.7 * r, shoulder), z=51))
        else:
            collar = polygon(
                [
                    (hx - 0.93 * r, shoulder - 5),
                    (hx - 0.43 * r, shoulder - 4),
                    (hx - 0.43 * r, shoulder + 1),
                    (hx - r, shoulder),
                ]
            )
            parts.append(Part(mat, collar, z=51))
    pins = p.get("pins")
    if pins and sk.view == "down":
        pin = points([(hx - 0.8 * r, shoulder - 0.5)])
        parts.append(Part(pins, pin | _mirror(sk, pin), z=49.5, tone=2))
    elif pins and sk.view == "right":
        parts.append(Part(pins, points([(hx - 0.7 * r, shoulder - 1.5)]), z=51.5, tone=2))

    buttons = p.get("buttons")
    if buttons and sk.view != "up":
        rows = range(round(shoulder + 3), round(sk.hip_y - 2), 3)
        if sk.view == "right":
            front = max(q[0] for q in body)
            dots = {(front, y) for y in rows}
        elif opened:
            dots = {(round(cx - gap - 1.2), y) for y in rows} | {
                (round(cx + gap + 0.2), y) for y in rows
            }
        else:
            dots = {(round(cx - 0.5), y) for y in rows}
        parts.append(Part(buttons, dots & body, z=31.5, tone=2))

    cuffs = p.get("cuffs")
    if cuffs and sk.view != "right":  # in profile the dot reads as a sparkle on the hand
        dots = set()
        for (hx2, hy2), (sx, sy) in zip(sk.hands, sk.shoulders, strict=True):
            dx, dy = sx - hx2, sy - hy2
            norm = max(1e-6, (dx * dx + dy * dy) ** 0.5)
            reach = sk.build.hand_r + 1.2
            dots |= points([(hx2 + dx / norm * reach, hy2 + dy / norm * reach)])
        parts.append(Part(cuffs, dots, z=21, tone=2))
    return parts


def belt(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Belt at the waist; count = 2 adds a second, slanted one.

    Options: buckle (color), studs (color of rivets along the belt).
    """
    mat = p["material"]
    (ta, tb, tr) = sk.torso
    torso = capsule(*ta, *tb, tr)
    y = round(sk.hip_y) - 2
    band = {q for q in torso if y <= q[1] <= y + 1}
    parts = [Part(mat, band, z=30.5)]
    cx = sk.center_x
    if p.get("count", 1) >= 2 and sk.view != "right":
        slant = capsule(cx - tr, y - 3, cx + tr, y + 1, 0.6)
        parts.append(Part(mat, slant & capsule(*ta, *tb, tr + 1), z=30.6, tone=1))
    studs = p.get("studs")
    if studs and sk.view != "up":
        dots = {q for q in band if q[1] == y and q[0] % 2 == 0}
        parts.append(Part(studs, dots, z=30.65, tone=2))
    if p.get("buckle") and sk.view == "down":
        parts.append(Part(p["buckle"], rect(cx - 1, y, cx, y + 1), z=30.7, tone=2))
    return parts


# Accessories -------------------------------------------------------------------------


def chain(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A chain hanging from the collar on the wearer's left. Option: length (links)."""
    length = p.get("length", 5)
    hx, r, shoulder = sk.head[0], sk.head_r, sk.shoulder_y
    if sk.view == "down":
        links = [(hx + 0.6 * r - i * 0.3, shoulder - 1 + i) for i in range(length)]
    elif sk.view == "right":
        links = [(hx + 0.3 * r + i * 0.2, shoulder + i) for i in range(length // 2 + 1)]
    else:
        return []
    mat = p["material"]
    # Alternate light and dark links so it reads as a chain, not a line.
    return [
        Part(mat, points(links[0::2]), z=34, tone=2),
        Part(mat, points(links[1::2]), z=34, tone=0),
    ]


SHAPES = {
    "heart": ["#.#", "###", ".#."],
    "circle": [".#.", "###", ".#."],
    "diamond": [".#.", "#.#", ".#."],
}


def emblem(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A small 3x3 motif. on: knees | chest. shape: heart | circle | diamond."""
    shape = SHAPES[p.get("shape", "heart")]
    spots: list[tuple[float, float, float]] = []  # x, y, z
    where = p.get("on", "chest")
    if where == "knees" and sk.view != "up":
        legs = [1] if sk.view == "right" else [0, 1]
        for i in legs:
            (px, py), (fx, fy) = sk.hips[i], sk.feet[i]
            spots.append(((px + fx) / 2, (py + fy) / 2, 35.5 if sk.view == "right" else 10.5))
    elif where == "chest" and sk.view == "down":
        spots.append((sk.center_x, sk.torso[0][1] + 1, 34))
    parts = []
    for x, y, z in spots:
        pixels = {
            (round(x) - 1 + dx, round(y) - 1 + dy)
            for dy, row in enumerate(shape)
            for dx, cell in enumerate(row)
            if cell == "#"
        }
        parts.append(Part(p["material"], pixels, z=z, tone=2))
    return parts


def earring(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """style: stud (small drop) | cherry (a little ball hanging from a wire)."""
    mat = p["material"]
    at = sk.at
    ears = [at(-1, 3)] if sk.view == "right" else [at(-7, 2), at(6.5, 2)]
    parts = []
    for x, y in ears:
        x, y = round(x), round(y)
        if p.get("style", "stud") == "cherry":
            parts.append(Part("", {(x, y), (x, y + 1)}, z=58, flat=OUTLINE))
            ball = rect(x - 1, y + 2, x, y + 3) if x < sk.head[0] else rect(x, y + 2, x + 1, y + 3)
            corner = min(ball)
            parts.append(Part(mat, ball, z=58, highlight={corner}))
        else:
            parts.append(Part(mat, {(x, y), (x, y + 1)}, z=58, tone=2))
    return parts


def seam(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A line down the back of the head, so a featureless head reads as seen from behind."""
    if sk.view != "up":
        return []
    x = round(sk.head[0]) - 1
    top, bottom = sk.at(0, -3)[1], sk.at(0, 4.5)[1]
    return [Part(p["material"], {(x, y) for y in range(round(top), round(bottom))}, z=51)]


# Body gear ---------------------------------------------------------------------------


def _lerp(a: Point, b: Point, t: float) -> Point:
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def _wavy(a: Point, b: Point, amp: float = 0.8, period: float = 4.0) -> set[Pixel]:
    """A one-pixel line from a to b, waving sideways."""
    length = max(1e-6, math.hypot(b[0] - a[0], b[1] - a[1]))
    nx, ny = -(b[1] - a[1]) / length, (b[0] - a[0]) / length
    steps = max(2, int(length * 2))
    line = []
    for i in range(steps + 1):
        t = i / steps
        off = amp * math.sin(t * length / period * 2 * math.pi)
        x, y = _lerp(a, b, t)
        line.append((x + nx * off, y + ny * off))
    return points(line)


def scarf(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Short scarf wrapped around the neck, hanging in a point on the chest; in profile a
    tail flies behind."""
    mat = p["material"]
    hx, r, shoulder, cx = sk.head[0], sk.head_r, sk.shoulder_y, sk.center_x
    if sk.view == "down":
        wrap = polygon(
            [
                (hx - 1.15 * r, shoulder - 3.5),
                (hx + 1.15 * r, shoulder - 3.5),
                (hx + 1.25 * r, shoulder + 0.5),
                (cx + 2.5, shoulder + 3.5),
                (cx, shoulder + 5.5),
                (cx - 2.5, shoulder + 3.5),
                (hx - 1.25 * r, shoulder + 0.5),
            ]
        )
        return [Part(mat, wrap, z=49.6)]
    if sk.view == "up":
        wrap = polygon(
            [
                (hx - 1.15 * r, shoulder - 3.5),
                (hx + 1.15 * r, shoulder - 3.5),
                (hx + 1.2 * r, shoulder + 0.5),
                (hx - 1.2 * r, shoulder + 0.5),
            ]
        )
        wrap |= polygon(
            [
                (cx - 2.5, shoulder),
                (cx + 2.5, shoulder),
                (cx + 1, shoulder + 5),
                (cx - 1, shoulder + 5),
            ]
        )
        return [Part(mat, wrap, z=51.2)]
    wrap = polygon(
        [
            (hx - 0.95 * r, shoulder - 4),
            (hx + 0.55 * r, shoulder - 3),
            (hx + 0.7 * r, shoulder + 1.5),
            (hx - 0.9 * r, shoulder + 1.5),
        ]
    )
    wrap |= polygon(
        [
            (hx - 0.8 * r, shoulder - 3),
            (hx - r - 6, shoulder - 1),
            (hx - r - 5, shoulder + 2.5),
            (hx - 0.8 * r, shoulder + 1),
        ]
    )
    return [Part(mat, wrap, z=51.2)]


def pauldrons(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Rounded shoulder pads. Options: size (px), rim (color of their lower edge)."""
    mat = p["material"]
    size = p.get("size", 4.2)
    rim = p.get("rim")
    shoulder = sk.shoulder_y
    if sk.view == "right":
        far, near = sk.shoulders
        pads = [((far[0] - 0.5, shoulder + 1), 5.5), ((near[0], shoulder + 1), 60.2)]
    else:
        (lx, _), (rx, _) = sk.shoulders
        pads = [((lx - 0.8, shoulder + 0.5), 33.0), ((rx + 0.8, shoulder + 0.5), 33.0)]
    parts = []
    for (x, y), z in pads:
        dome = {q for q in disc(x, y, size) if _center(q)[1] < y + size * 0.55}
        shine = points([(x - size * 0.4, y - size * 0.5)]) & dome
        parts.append(Part(mat, dome, z=z, highlight=shine))
        if rim:
            lowest: dict[int, int] = {}
            for qx, qy in dome:
                lowest[qx] = max(lowest.get(qx, qy), qy)
            edge = {(qx, qy) for qx, qy in dome if qy >= lowest[qx] - 1}
            parts.append(Part(rim, edge, z=z + 0.05, tone=2))
            parts.append(Part(rim, points([(x, y - 0.5)]), z=z + 0.06, tone=1))  # spiral boss
    return parts


def gloves(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Long gloves up the forearms (give the hands the glove color in [body]).

    Options: length (share of the arm covered, from the hand), studs (knuckle studs color).
    """
    mat = p["material"]
    length = p.get("length", 0.5)
    b = sk.build
    if sk.view == "right":
        arms = [
            (sk.shoulders[0], sk.hands[0], 5.5, b.arm_r * 0.95),
            (sk.shoulders[1], sk.hands[1], 60.5, b.arm_r * 1.05),
        ]
    else:
        arms = [(sk.shoulders[i], sk.hands[i], 20.5, b.arm_r) for i in (0, 1)]
    parts = []
    for shoulder, hand, z, r in arms:
        start = _lerp(hand, shoulder, length)
        parts.append(Part(mat, capsule(*start, *hand, r * 1.15), z=z))
    studs = p.get("studs")
    if studs and sk.view != "up":
        knuckles: set[Pixel] = set()
        if sk.view == "down":
            for x, y in sk.hands:
                knuckles |= points([(x - 1, y + 1), (x, y + 1), (x + 1, y + 1)])
        else:
            x, y = sk.hands[1]
            knuckles |= points([(x + 1, y - 1), (x + 1, y), (x + 1, y + 1)])
        parts.append(Part(studs, knuckles, z=62, tone=2))
    return parts


def loincloth(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Cloth flaps hanging from the waist, front and back. Option: length (share of legs)."""
    mat = p["material"]
    length = p.get("length", 0.5) * sk.build.legs
    top = sk.hip_y - 2.5
    cx, tr = sk.center_x, sk.torso[2]
    if sk.view == "right":
        w = tr * 0.95
        front = polygon(
            [(cx + 0.5, top), (cx + w, top), (cx + w + 1.5, top + length), (cx + 1, top + length)]
        )
        back = polygon(
            [(cx - w, top), (cx - 0.5, top), (cx - 1, top + length), (cx - w - 1.5, top + length)]
        )
        return [Part(mat, front | back, z=37.5)]
    half = tr * 0.75
    flap = polygon(
        [
            (cx - half, top),
            (cx + half, top),
            (cx + half - 1, top + length),
            (cx - half + 1, top + length),
        ]
    )
    fold = {q for q in flap if q[0] == round(cx - 0.5) and q[1] > top + 2}
    return [Part(mat, flap, z=30.4), Part(mat, fold, z=30.45, tone=0)]


def body_lines(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Wavy lines from the shoulders over the chest and down the arms and legs.

    Options: amp (how far the line waves, px), period (length of one wave, px).
    """
    mat = p["material"]
    amp, period = p.get("amp", 0.8), p.get("period", 4.0)

    def line(a: Point, b: Point) -> set[Pixel]:
        return _wavy(a, b, amp=amp, period=period)

    cx, shoulder, hip = sk.center_x, sk.shoulder_y, sk.hip_y
    if sk.view == "right":
        (ta, tb, tr) = sk.torso
        near_sh, near_hand = sk.shoulders[1], sk.hands[1]
        near_hip, near_foot = sk.hips[1], sk.feet[1]
        torso_line = line((ta[0] + tr - 1.5, shoulder + 2), (tb[0] + tr - 1.5, hip - 1))
        leg_line = line((near_hip[0] + 1, near_hip[1] + 1), (near_foot[0] + 1, near_foot[1] - 2))
        return [
            Part(mat, torso_line, z=30.3, tone=2),
            Part(mat, line(near_sh, _lerp(near_sh, near_hand, 0.6)), z=60.3, tone=2),
            Part(mat, leg_line, z=35.3, tone=2),
        ]
    parts = []
    for i, sign in ((0, -1), (1, 1)):
        sh, hand = sk.shoulders[i], sk.hands[i]
        if sk.view == "down":
            chest = (cx + sign * 2, shoulder + 6)
            torso_line = line((sh[0] - sign * 3.5, shoulder + 1), chest)
            torso_line |= line(chest, (cx + sign * 1.5, hip - 2))
            parts.append(Part(mat, torso_line, z=30.3, tone=2))
        parts.append(Part(mat, line(sh, _lerp(sh, hand, 0.6)), z=20.3, tone=2))
        leg_top, foot = sk.hips[i], sk.feet[i]
        leg_line = line((leg_top[0] + sign, leg_top[1] + 1), (foot[0] + sign, foot[1] - 2))
        parts.append(Part(mat, leg_line, z=10.3, tone=2))
    return parts


def veins(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A net of thin dark lines over the torso and arms. Option: density (torso lines)."""
    mat = p["material"]
    rng = random.Random(7)  # same pattern every frame, placed relative to the body
    (ta, tb, tr) = sk.torso
    torso = capsule(*ta, *tb, tr)
    lines: set[Pixel] = set()
    for _ in range(p.get("density", 6)):
        t = rng.uniform(0.05, 0.85)
        start = (_lerp(ta, tb, t)[0] + rng.uniform(-0.8, 0.8) * tr, _lerp(ta, tb, t)[1])
        end = (
            start[0] + rng.uniform(-0.7, 0.7) * tr,
            start[1] + rng.uniform(0.15, 0.35) * (tb[1] - ta[1]),
        )
        lines |= _wavy(start, end, amp=0.7, period=3)
    parts = [Part(mat, lines & torso, z=30.2, tone=0)]
    arms = [1] if sk.view == "right" else [0, 1]
    for i in arms:
        sh, hand = sk.shoulders[i], sk.hands[i]
        arm = capsule(*sh, *hand, sk.build.arm_r)
        z = 60.2 if sk.view == "right" else 20.2
        parts.append(
            Part(mat, _wavy(sh, _lerp(sh, hand, 0.8), amp=0.6, period=3) & arm, z=z, tone=0)
        )
    return parts


def tendrils(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Thin strands unravelling from the lower legs. Options: count (per leg), length (px)."""
    count = p.get("count", 2)
    length = p.get("length", 7)
    strands: set[Pixel] = set()
    legs = [1] if sk.view == "right" else [0, 1]
    for i in legs:
        hip, foot = sk.hips[i], sk.feet[i]
        outward = -1 if (sk.view == "right" or i == 0) else 1
        for j in range(count):
            start = _lerp(hip, foot, 0.55 + 0.2 * j)
            end = (start[0] + outward * (length - j * 1.5), start[1] + 2 + j * 1.5)
            strands |= _wavy(start, end, amp=0.8, period=3)
    return [Part(p["material"], strands, z=34 if sk.view == "right" else 9.5, tone=1)]


def sword(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A thin blade held in the screen-right (profile: near) hand, along the forearm.

    Options: length (px), guard (color of the hand guard). The tip is kept inside the
    sprite cell, so the blade looks shorter when the arm is stretched far out.
    """
    shoulder, hand = sk.shoulders[1], sk.hands[1]
    dx, dy = hand[0] - shoulder[0], hand[1] - shoulder[1]
    norm = max(1e-6, math.hypot(dx, dy))
    ux, uy = dx / norm, dy / norm
    length = p.get("length", 14)
    low, high = 2, look.cell - 3  # leave room for the outline around the tip
    for axis_pos, axis_dir in ((hand[0], ux), (hand[1], uy)):
        if axis_dir > 0:
            length = min(length, (high - axis_pos) / axis_dir)
        elif axis_dir < 0:
            length = min(length, (axis_pos - low) / -axis_dir)
    length = max(0.0, length)
    tip = (hand[0] + ux * length, hand[1] + uy * length)
    steps = max(1, round(length * 2))
    blade = points([_lerp(hand, tip, i / steps) for i in range(steps + 1)])
    z = {"down": 59.5, "up": 14.5, "right": 61.5}[sk.view]
    parts = [Part(p["material"], blade, z=z, tone=2)]
    guard = p.get("guard")
    if guard:
        bar = points(
            [(hand[0] + uy * s + ux * 2, hand[1] - ux * s + uy * 2) for s in (-1.5, 0, 1.5)]
        )
        parts.append(Part(guard, bar, z=z + 0.1, tone=1))
    return parts


PART_TYPES: dict[str, Callable[[Skeleton, dict, Look], list[Part]]] = {
    "hair": hair,
    "cap": cap,
    "headband": headband,
    "mask": mask,
    "coat": coat,
    "belt": belt,
    "chain": chain,
    "emblem": emblem,
    "earring": earring,
    "seam": seam,
    "scarf": scarf,
    "pauldrons": pauldrons,
    "gloves": gloves,
    "loincloth": loincloth,
    "body_lines": body_lines,
    "veins": veins,
    "tendrils": tendrils,
    "sword": sword,
}
