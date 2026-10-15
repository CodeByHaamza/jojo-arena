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
    """style: short | long | tower | spiky | swept (volume swept up and back).

    Options (head units): volume, length (long), height (tower), back_length (locks over
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
    band = {q for q in disc(*sk.at(0, 0), 7.4 * sk.k) if -5.5 <= _rel(sk, q)[1] <= -3.5}
    return [Part(p["material"], band, z=55.5)]


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


PART_TYPES: dict[str, Callable[[Skeleton, dict, Look], list[Part]]] = {
    "hair": hair,
    "cap": cap,
    "headband": headband,
    "coat": coat,
    "belt": belt,
    "chain": chain,
    "emblem": emblem,
    "earring": earring,
    "seam": seam,
}
