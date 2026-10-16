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
    (a fin on top of a helmet; crest_color) | mane (wild curved tufts flaring up and out).

    Options (head units): volume, length (long), height (tower, crest), back_length (locks over
    the nape; a mane flows down behind the shoulders), flare (mane: how far its tufts reach),
    fill (mane: 0 = separate spikes, 1 = one full mass);
    bangs = curl | fringe, bangs_side = left | right (seen from the front), bangs_length,
    bangs_width and bangs_spread (curl: distance from the face).
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
    elif style == "mane":
        flare = p.get("flare", 1.0)
        if sk.view == "right":
            tufts = [
                ((2.5, -7), (1, -12)),
                ((0, -7.5), (-4, -12.5)),
                ((-3, -6.5), (-9, -10.5)),
                ((-5.5, -4), (-11.5, -6)),
                ((-6, -1), (-11, 0.5)),
            ]
        else:
            tufts = [
                ((-6.5, -4), (-11.5, -7)),
                ((-4.5, -6.5), (-8, -12)),
                ((-1.5, -7.5), (-2.5, -13.5)),
                ((1.5, -7.5), (2.5, -13.5)),
                ((4.5, -6.5), (8, -12)),
                ((6.5, -4), (11.5, -7)),
            ]
        mane: set[Pixel] = set()
        fill = p.get("fill", 0.0)
        if fill:
            # A mass under the tufts, so they read as one wild mane rather than spikes.
            middle = at(-3, -5.5) if sk.view == "right" else at(0, -6)
            mane |= {q for q in disc(*middle, 6.5 * k * fill) if rel(q)[1] < -2}
        for (bx, by), (tx, ty) in tufts:
            tip = (bx + (tx - bx) * flare, by + (ty - by) * flare)
            mane |= _tuft(sk, (bx, by), tip, 3.6)
        parts.append(Part(mat, mane, z=53.5, highlight=points([at(-1.5, -10)]) & mane))
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
    if back_length and style == "mane":
        # The mane flows down behind the shoulders: wide from behind, swept back in profile.
        if sk.view == "down":
            flow = capsule(*at(-6.5, 0), *at(-9, back_length), 2.4 * k)
            flow |= capsule(*at(6.5, 0), *at(9, back_length), 2.4 * k)
            parts.append(Part(mat, flow, z=4))
        elif sk.view == "up":
            flow = capsule(*at(-3, 1), *at(-4.5, back_length), 4 * k)
            flow |= capsule(*at(3, 1), *at(4.5, back_length), 4 * k)
            parts.append(Part(mat, flow, z=53))
        else:
            parts.append(Part(mat, capsule(*at(-5, 0), *at(-8.5, back_length), 3 * k), z=4))
    elif back_length and style != "long":
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


def _tuft(sk: Skeleton, base: Point, tip: Point, width: float) -> set[Pixel]:
    """A tapering lock of hair from base to tip (head units), bowed like a flame."""
    (bx, by), (tx, ty) = base, tip
    dx, dy = tx - bx, ty - by
    n = math.hypot(dx, dy) or 1.0
    px, py = -dy / n, dx / n  # perpendicular
    bow = 0.9 if tx >= bx else -0.9
    mx, my = bx + dx * 0.55 + px * bow, by + dy * 0.55 + py * bow
    half = width / 2
    corners = [
        (bx - px * half, by - py * half),
        (mx - px * half * 0.55, my - py * half * 0.55),
        (tx, ty),
        (mx + px * half * 0.55, my + py * half * 0.55),
        (bx + px * half, by + py * half),
    ]
    return polygon([sk.at(*c) for c in corners])


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
    band (color of a band around the crown), badge (color), badges (1 or 2) and plate
    (true: the second badge is a wide plate).
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
            for n, (x, _) in enumerate(spots):
                wide = 1 if p.get("plate") and n == 1 else 0
                parts.append(
                    Part(
                        badge,
                        rect(x, y - 1, x + 1 + wide, y),
                        z=58,
                        highlight={(round(x), round(y - 1))},
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
    """Band around the forehead. Options: gem (color of a stone at the front),
    gem_shape (oval | heart), triangles (color of a row of triangles along the band),
    feather (color of a feather sticking up from the side)."""
    band = {q for q in disc(*sk.at(0, 0), 7.4 * sk.k) if -5.5 <= _rel(sk, q)[1] <= -3.5}
    parts = [Part(p["material"], band, z=55.5)]
    triangles = p.get("triangles")
    if triangles and band:
        top = min(y for _, y in band)
        # Teeth pointing down: wide on the band's top row, a point on the bottom one.
        teeth = {(x, y) for x, y in band if (x % 4) < 3 - (y - top)}
        parts.append(Part(triangles, teeth, z=55.55, tone=1))
    feather = p.get("feather")
    if feather and sk.view != "up":
        side = 1 if sk.view == "down" else -1
        fx, fy = sk.at(side * 6.2, -5.5)
        quill = {(round(fx + side * (i // 3)), round(fy) - i) for i in range(7)}
        quill |= {(x + side, y) for x, y in quill if y < fy - 2}
        parts.append(Part(feather, quill, z=55.7))
    gem = p.get("gem")
    if gem and sk.view == "down":
        if p.get("gem_shape", "oval") == "heart":
            cx, cy = (round(v) for v in sk.at(0, -4.5))
            pattern = [".#.#.", "#####", ".###.", "..#.."]
            stone = {
                (cx - 2 + dx, cy - 2 + dy)
                for dy, row in enumerate(pattern)
                for dx, cell in enumerate(row)
                if cell == "#"
            }
        else:
            corners = [sk.at(-1.3, -6.6), sk.at(1.3, -6.6), sk.at(1.3, -2.5), sk.at(-1.3, -2.5)]
            stone = polygon(corners)
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
    parts = [Part(p["material"], area, z=51)]
    grill = p.get("grill")
    if grill:
        # Vertical bars over the mouth, like a knight's visor.
        bars = {q for q in area if _rel(sk, q)[1] > 2.2 and q[0] % 2 == 0}
        parts.append(Part(grill, bars, z=51.2, tone=2))
    return parts


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

    Options: buckle (color), buckle_shape (heart), studs (color of rivets along the belt),
    second (color of the second belt), pouches (color of two pouches hanging on the sides),
    below (color of the trousers' waist under the belt, when the torso is bare skin).
    """
    mat = p["material"]
    (ta, tb, tr) = sk.torso
    torso = capsule(*ta, *tb, tr)
    y = round(sk.hip_y) - 2
    band = {q for q in torso if y <= q[1] <= y + 1}
    parts = [Part(mat, band, z=30.5)]
    below = p.get("below")
    if below:
        parts.append(Part(below, {q for q in torso if q[1] > y + 1}, z=30.3))
    cx = sk.center_x
    if p.get("count", 1) >= 2 and sk.view != "right":
        slant = capsule(cx - tr, y - 3, cx + tr, y + 1, 0.6)
        second = p.get("second", mat)
        parts.append(Part(second, slant & capsule(*ta, *tb, tr + 1), z=30.6, tone=1))
    studs = p.get("studs")
    if studs and sk.view != "up":
        dots = {q for q in band if q[1] == y and q[0] % 2 == 0}
        parts.append(Part(studs, dots, z=30.65, tone=2))
    if p.get("buckle") and sk.view == "down":
        if p.get("buckle_shape") == "heart":
            heart = {
                (round(cx) - 2 + dx, y - 1 + dy)
                for dy, row in enumerate(SHAPES["heart"])
                for dx, cell in enumerate(row)
                if cell == "#"
            }
            parts.append(Part(p["buckle"], heart, z=30.7, tone=2))
        else:
            parts.append(Part(p["buckle"], rect(cx - 1, y, cx, y + 1), z=30.7, tone=2))
    pouches = p.get("pouches")
    if pouches:
        if sk.view == "right":
            bags = rect(cx + tr - 3, y, cx + tr - 1, y + 3)
        else:
            bags = rect(cx - tr + 0.5, y, cx - tr + 2.5, y + 3)
            bags |= {(round(2 * cx) - 1 - x, yy) for x, yy in bags}
        parts.append(Part(pouches, bags, z=30.75))
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
    "ball": [".##.", "####", "####", ".##."],
    "bow": ["#.#", "###", "#.#"],
    "tie": [".#.", ".#.", "###", "###", ".#."],
}


def emblem(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A small 3x3 motif. on: knees | elbows | chest | belt (one on each side) | chin.
    shape: heart | circle | diamond | ball (a round guard, 4 by 4) | bow (a bow tie) |
    tie (a necktie)."""
    shape = SHAPES[p.get("shape", "heart")]
    spots: list[tuple[float, float, float]] = []  # x, y, z
    where = p.get("on", "chest")
    side = sk.view == "right"
    limbs = [1] if side else [0, 1]
    if where == "knees" and sk.view != "up":
        for i in limbs:
            (px, py), (fx, fy) = sk.hips[i], sk.feet[i]
            spots.append(((px + fx) / 2, (py + fy) / 2, 36.7 if side else 11.7))
    elif where == "elbows":
        for i in limbs:
            (sx, sy), (hx, hy) = sk.shoulders[i], sk.hands[i]
            spots.append(((sx + hx) / 2, (sy + hy) / 2, 60.7 if side else 20.7))
    elif where == "chest" and sk.view == "down":
        spots.append((sk.center_x, sk.torso[0][1] + 1, 34))
    elif where == "belt" and sk.view != "up":
        tr = sk.torso[2]
        xs = [sk.center_x + tr - 1.5] if side else [sk.center_x - tr + 2, sk.center_x + tr - 2]
        spots += [(x, sk.hip_y - 1, 30.8) for x in xs]
    elif where == "chin" and sk.view != "up":
        x, y = sk.at(2.5 if side else 0, 0)
        spots.append((x, y + sk.head_r + 1.5, 49.7))
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
    """style: stud (small drop) | cherry (a little ball hanging from a wire) |
    heart (a hanging heart, cracked in the middle)."""
    mat = p["material"]
    at = sk.at
    ears = [at(-1, 3)] if sk.view == "right" else [at(-7, 2), at(6.5, 2)]
    parts = []
    for x, y in ears:
        x, y = round(x), round(y)
        style = p.get("style", "stud")
        if style == "heart":
            left = x < sk.head[0]
            ox = x - 2 if left else x
            heart = {
                (ox + dx, y + 1 + dy)
                for dy, row in enumerate(SHAPES["heart"])
                for dx, cell in enumerate(row)
                if cell == "#"
            }
            parts.append(Part(mat, heart, z=58, highlight={min(heart)}))
            parts.append(Part(mat, {(ox + 1, y + 2)}, z=58.1, tone=0))  # the crack
        elif style == "cherry":
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
    tail flies behind. Options: stripes (color of diagonal stripes), tail (extra px of
    the tail flying behind, in profile)."""
    parts = _scarf_shape(sk, p)
    stripes = p.get("stripes")
    if stripes:
        lines = {(x, y) for x, y in parts[0].pixels if (x + y) % 4 < 2}
        parts.append(Part(stripes, lines, z=parts[0].z + 0.01, tone=1))
    return parts


def _scarf_shape(sk: Skeleton, p: dict) -> list[Part]:
    mat = p["material"]
    tail = p.get("tail", 0)
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
            (hx - r - 6 - tail, shoulder - 1 + tail / 3),
            (hx - r - 5 - tail, shoulder + 2.5 + tail / 3),
            (hx - 0.8 * r, shoulder + 1),
        ]
    )
    return [Part(mat, wrap, z=51.2)]


def pauldrons(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Rounded shoulder pads. Options: size (px), rim (color of their lower edge),
    spikes (how many points stick out of each), ring (color of a ring boss on each),
    spiral (color of a spiral groove on each)."""
    mat = p["material"]
    size = p.get("size", 4.2)
    rim = p.get("rim")
    spike_count = p.get("spikes", 0)
    ring = p.get("ring")
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
        spiral = p.get("spiral")
        if spiral:
            pattern = [".###.", "#...#", "#.#.#", "#..##"]
            if x < sk.center_x:
                pattern = [row[::-1] for row in pattern]
            sx, sy = round(x) - 2, round(y - size * 0.45) - 1
            groove = {
                (sx + dx, sy + dy)
                for dy, row in enumerate(pattern)
                for dx, cell in enumerate(row)
                if cell == "#"
            }
            parts.append(Part(spiral, groove & dome, z=z + 0.08, tone=0))
        if ring:
            boss = disc(x, y - size * 0.15, size * 0.55) - disc(x, y - size * 0.15, size * 0.25)
            parts.append(Part(ring, boss & dome, z=z + 0.07, tone=1))
        if spike_count:
            outward = -1 if x < sk.center_x else 1
            spikes: set[Pixel] = set()
            for i in range(spike_count):
                # Fanned over the top and the outer side of the pad.
                angle = math.radians(-90 + outward * (25 + 110 * i / max(1, spike_count - 1)))
                ux, uy = math.cos(angle), math.sin(angle)
                base = (x + ux * (size - 0.5), y + uy * (size - 0.5))
                tip = (x + ux * (size + 3.2), y + uy * (size + 3.2))
                side = (-uy * 1.1, ux * 1.1)
                spikes |= polygon(
                    [
                        (base[0] + side[0], base[1] + side[1]),
                        tip,
                        (base[0] - side[0], base[1] - side[1]),
                    ]
                )
            parts.append(Part(mat, spikes, z=z - 0.1))
    return parts


def _band(pixels: set[Pixel], start: Point, end: Point, width: float) -> set[Pixel]:
    """The pixels within `width` of `start`, measured along the line toward `end`."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    out = set()
    for q in pixels:
        cx, cy = _center(q)
        t = (cx - start[0]) * ux + (cy - start[1]) * uy
        if 0 <= t <= width:
            out.add(q)
    return out


def gloves(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Long gloves up the forearms (give the hands the glove color in [body]).

    Options: length (share of the arm covered, from the hand), studs (knuckle studs color),
    ribbed (true: dark rings across, like segmented tubes), cuff (color of a band at the top).
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
        sleeve = capsule(*start, *hand, r * 1.15)
        parts.append(Part(mat, sleeve, z=z))
        if p.get("ribbed"):
            parts.append(Part(mat, _rings(sleeve, start, hand), z=z + 0.01, tone=0))
        if p.get("cuff"):
            band = _band(sleeve, start, hand, 1.5)
            parts.append(Part(p["cuff"], band, z=z + 0.02))
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
    """A net of thin lines over the torso and arms (the material's dark tone).
    Options: density (torso lines), legs (true: over the legs too)."""
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
    if p.get("legs"):
        for i in arms:
            hip, foot = sk.hips[i], sk.feet[i]
            leg = capsule(*hip, *foot, sk.build.leg_r)
            z = 35.2 if sk.view == "right" else 10.2
            wave = _wavy(hip, _lerp(hip, foot, 0.85), amp=0.6, period=3)
            parts.append(Part(mat, wave & leg, z=z, tone=0))
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
    cup = p.get("cup")
    if cup:
        # A cup hilt: a round bell of metal in front of the fist.
        r = sk.build.hand_r
        room = r + 3.5  # the bell and its outline stay inside the cell
        bx = min(max(hand[0] + ux * 1.5, room), look.cell - room)
        by = min(max(hand[1] + uy * 1.5, room), look.cell - room)
        bell = disc(bx, by, r + 1.4)
        parts.append(Part(cup, bell, z=z + 0.6, highlight={min(bell)}))
    basket = p.get("basket")
    if basket:
        # A basket hilt: a cage of metal around the fist.
        r = sk.build.hand_r
        cage = disc(*hand, r + 1.3) - disc(*hand, r + 0.2)
        parts.append(Part(basket, cage, z=z + 0.6))
    return parts


def _rings(pixels: set[Pixel], a: Point, b: Point, spacing: int = 2) -> set[Pixel]:
    """Pixels of a limb piece lying on rings across its length (a ribbed tube)."""
    length = max(1e-6, math.hypot(b[0] - a[0], b[1] - a[1]))
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    rings = set()
    for q in pixels:
        x, y = _center(q)
        along = (x - a[0]) * ux + (y - a[1]) * uy
        if round(along) % spacing == 0:
            rings.add(q)
    return rings


def boots(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Covers over the feet and lower legs. Options: length (share of the leg, from the
    foot), pointed (long pointed toes), ribbed (dark rings across)."""
    mat = p["material"]
    length = p.get("length", 0.3)
    b = sk.build
    if sk.view == "right":
        legs = [
            (sk.hips[0], sk.feet[0], 8.5, b.leg_r * 0.96),
            (sk.hips[1], sk.feet[1], 36.5, b.leg_r),
        ]
    else:
        legs = [(sk.hips[i], sk.feet[i], 11.5, b.leg_r) for i in (0, 1)]
    parts = []
    for hip, foot, z, r in legs:
        start = _lerp(foot, hip, length)
        offset = 1 if sk.view == "right" else 0
        cover = capsule(*start, *foot, r * 1.12) | disc(
            foot[0] + offset, foot[1] + 1, b.foot_r * 1.08
        )
        if p.get("pointed") and sk.view == "right":
            fx, fy = foot[0] + offset, foot[1] + 1
            cover |= polygon([(fx, fy - 1.5), (fx + b.foot_r + 4.5, fy + 1.5), (fx, fy + 2)])
        parts.append(Part(mat, cover, z=z))
        if p.get("ribbed"):
            parts.append(Part(mat, _rings(cover, start, foot), z=z + 0.01, tone=0))
    return parts


def top(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A fitted top from the chest down, shoulders bare.

    Options: neckline (px below the shoulder line), strap (left | right: a single strap
    up to the wearer's shoulder on that side), length (share of the torso it covers,
    from the neckline: below 1, a cropped top), torn (true: a ragged lower edge).
    """
    mat = p["material"]
    (ta, tb, tr) = sk.torso
    neck = sk.shoulder_y + p.get("neckline", 3)
    torso = capsule(*ta, *tb, tr)
    bottom = max(q[1] for q in torso)
    hem = neck + (bottom - neck) * p.get("length", 1.0)
    cover = {q for q in torso if neck <= q[1] <= hem}
    if p.get("torn") and cover:
        # Rips along the hem: every other column stops a pixel or two short.
        last = max(q[1] for q in cover)
        cover = {(x, y) for x, y in cover if not (y >= last - (x % 3 == 0) and x % 2)}
    strap = p.get("strap")
    if strap and sk.view != "right":
        # The wearer's left is the screen's right from the front, the screen's left from behind.
        wearer_left = (strap == "left") == (sk.view == "down")
        i = 1 if wearer_left else 0
        sx, sy = sk.shoulders[i]
        sign = 1 if i == 1 else -1
        cover |= capsule(sk.center_x + sign * 1.5, neck + 1, sx - sign * 1.5, sy, 1.1)
    return [Part(mat, cover, z=30.45)]


def horns(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Two horns curving up and out from the sides of the head (a helmet's, or a
    demon's). Options: size (head units), tip (color of the tips)."""
    mat = p["material"]
    size = p.get("size", 1.0)
    if sk.view == "right":
        pairs = [((1.5, -5), (6 * size + 1.5, -12 * size - 3), 60.6)]
    else:
        pairs = [
            ((-5, -4), (-10 * size - 2, -11 * size - 3), 56.8),
            ((5, -4), (10 * size + 2, -11 * size - 3), 56.8),
        ]
    parts = []
    for base, tip, z in pairs:
        horn = _tuft(sk, base, tip, 3.4)
        parts.append(Part(mat, horn, z=z))
        if p.get("tip"):
            point = _tuft(sk, ((base[0] + 2 * tip[0]) / 3, (base[1] + 2 * tip[1]) / 3), tip, 2.0)
            parts.append(Part(p["tip"], point & horn, z=z + 0.1))
    return parts


def top_hat(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A tall top hat with a wide brim. Options: height (crown, head units), band (color of
    a band around the crown), checker (second color: harlequin diamonds on the band),
    bowler (true: a low, rounded crown, a bowler hat)."""
    mat = p["material"]
    at = sk.at
    h = p.get("height", 9.0)
    shift = -0.6 if sk.view == "right" else 0.0
    base = -4.4
    if p.get("bowler"):
        dome = disc(*at(shift, base), 6.2 * sk.k)
        crown = {q for q in dome if _rel(sk, q)[1] < base}
    else:
        crown = polygon(
            [
                at(-5.6 + shift, base),
                at(5.6 + shift, base),
                at(6.1 + shift, base - h),
                at(-6.1 + shift, base - h),
            ]
        )
    brim = polygon([at(-9, base - 0.3), at(9, base - 0.3), at(9, base + 1.2), at(-9, base + 1.2)])
    shine = points([at(-4 + shift, base - h + 1.5), at(-4 + shift, base - h + 2.5)]) & crown
    parts = [Part(mat, crown, z=56, highlight=shine), Part(mat, brim, z=57)]
    band = p.get("band")
    if band:
        top_of_band = base - (2.2 if p.get("bowler") else 4.2)
        rows = {q for q in crown if top_of_band <= _rel(sk, q)[1] < base - 0.6}
        parts.append(Part(band, rows, z=56.4))
        checker = p.get("checker")
        if checker:
            top = min(q[1] for q in rows)
            # Diamonds: lit where the distance to the nearest diamond center is small.
            diamonds = {(x, y) for x, y in rows if (abs((x % 4) - 1.5) + abs(y - top - 1)) <= 1.6}
            parts.append(Part(checker, diamonds, z=56.5, tone=2))
    return parts


def helmet(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A helmet over the top of the head with a V point coming down over the forehead
    (leaning forward in profile). Option: tube (color of a hose linking the ears behind
    the head)."""
    mat = p["material"]
    at = sk.at
    k = sk.k

    def rel(q: Pixel) -> Point:
        return _rel(sk, q)

    if p.get("style") == "pyramid":
        # A tall faceted point: a wide brim over the face, rising to a peak.
        if sk.view == "down":
            shell = polygon([at(0, -14), at(-9, -3.5), at(0, 1.2), at(9, -3.5)])
            facet = polygon([at(0, -14), at(0, 1.2), at(9, -3.5)])
        elif sk.view == "up":
            shell = polygon([at(0, -14), at(-9, -3.5), at(-6, 2), at(6, 2), at(9, -3.5)])
            facet = polygon([at(0, -14), at(6, 2), at(9, -3.5)])
        else:
            shell = polygon([at(-7, -2), at(-2, -14), at(11, -3), at(5, 0.5), at(-6, 2.5)])
            facet = polygon([at(-2, -14), at(11, -3), at(5, 0.5), at(1, -4)])
        parts = [
            Part(mat, shell, z=56, highlight=points([at(-2, -9)]) & shell),
            Part(mat, facet & shell, z=56.1, tone=0),
        ]
    elif sk.view == "down":
        shell = {q for q in disc(*at(0, -0.8), 8.0 * k) if rel(q)[1] < -2.0}
        shell |= polygon([at(-6.5, -2.6), at(6.5, -2.6), at(0, 1.2)])
    elif sk.view == "up":
        shell = {q for q in disc(*at(0, -0.5), 8.0 * k) if rel(q)[1] < 3.0}
    else:
        shell = {
            q
            for q in disc(*at(-0.5, -0.8), 8.0 * k)
            if rel(q)[1] < -2.0 or (rel(q)[0] < -2.5 and rel(q)[1] < 3.0)
        }
        shell |= polygon([at(1.5, -6.5), at(9.5, -2.8), at(5, -1.4), at(1.5, -2.2)])
    if p.get("style") != "pyramid":
        parts = [Part(mat, shell, z=56, highlight=points([at(-4, -7)]) & shell)]
    tube = p.get("tube")
    if tube:
        if sk.view == "up":
            path = [at(-7 + 14 * t / 8, 1 + 3.5 * math.sin(math.pi * t / 8)) for t in range(9)]
            hose: set[Pixel] = set()
            for a, b in zip(path, path[1:], strict=False):
                hose |= capsule(*a, *b, 0.9 * k)
        elif sk.view == "down":
            ends = rect(*at(-8.2, 0.5), *at(-6.8, 2.5))
            hose = ends | _mirror(sk, ends)
        else:
            hose = disc(*at(-0.5, 1.5), 1.8 * k) - disc(*at(-0.5, 1.5), 0.7 * k)
        parts.append(Part(tube, hose, z=56.5))
    return parts


def tanks(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Two cylinders strapped on the back (air tanks). Options: straps (color), above (px
    they stand up over the shoulders: then they show from the front too)."""
    mat = p["material"]
    shoulder, cx, tr = sk.shoulder_y, sk.center_x, sk.torso[2]
    above = p.get("above", 0)
    top_y, bottom_y = shoulder + 1 - above, shoulder + 0.55 * sk.build.torso
    parts = []
    if above and sk.view == "down":
        for sign in (-1, 1):
            x = cx + sign * (sk.build.shoulders - 2.2)
            cylinder = capsule(x, top_y, x, shoulder + 2, 2.4)
            parts.append(Part(mat, cylinder, z=5, highlight={min(cylinder)}))
    if sk.view == "up":
        for sign in (-1, 1):
            x = cx + sign * (2.6 + (1.4 if above else 0))
            cylinder = capsule(x, top_y, x, bottom_y, 2.4 if above else 2.1)
            parts.append(Part(mat, cylinder, z=31.5, highlight={min(cylinder)}))
    elif sk.view == "right":
        x = cx - tr - 1.2
        radius = 2.4 if above else 2.1
        parts.append(Part(mat, capsule(x, top_y, x, bottom_y, radius), z=29))
    straps = p.get("straps")
    if straps and sk.view != "right":
        bands = set()
        for sign in (-1, 1):
            bands |= capsule(cx + sign * 3.5, shoulder - 1, cx + sign * 3, shoulder + 6, 0.6)
        parts.append(Part(straps, bands, z=31.6 if sk.view == "up" else 30.6, tone=1))
    return parts


def cheek_guards(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Pointed guards over the cheeks and jaw (helmets)."""
    at = sk.at
    if sk.view == "up":
        return []
    if sk.view == "down":
        left = polygon([at(-7, 0.5), at(-4.6, 2), at(-6.6, 5.5)])
        guards = left | _mirror(sk, left)
    else:
        guards = polygon([at(3, 3), at(9, 4.8), at(3.5, 6.2)])
    return [Part(p["material"], guards, z=53)]


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
    "boots": boots,
    "top": top,
    "helmet": helmet,
    "top_hat": top_hat,
    "horns": horns,
    "tanks": tanks,
    "cheek_guards": cheek_guards,
}
