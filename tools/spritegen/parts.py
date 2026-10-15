"""Costume parts. Each one turns a skeleton plus its settings into pixel parts.

Every part has a `material` (a palette entry). In a look file:

    [[parts]]
    type = "coat"
    material = "coat"
    length = 0.85

Drawing order (z) for costume pieces: coat body 31, belts 30.5, collar 49/51,
long-hair falls 53, hair 54, headbands 55.5, headwear 56-57, bangs and earrings 57-58.
"""

from __future__ import annotations

from collections.abc import Callable

from .look import Look
from .raster import Part, Pixel, capsule, disc, points, polygon, rect
from .skeleton import Skeleton


def _center(q: Pixel) -> tuple[float, float]:
    return q[0] + 0.5, q[1] + 0.5


# Hair --------------------------------------------------------------------------------


def hair(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """style: short | long | tower | spiky. Options: length, height, bangs (curl, fringe)."""
    mat = p["material"]
    style = p.get("style", "short")
    hx, hy = sk.head
    shine = {(round(hx) - 3, round(hy) - 6), (round(hx) - 2, round(hy) - 6)}
    volume = p.get("volume", 7.7)
    if sk.view == "down":
        top = {q for q in disc(hx, hy - 0.6, volume) if _center(q)[1] < hy - 2.5}
        sides = {
            q
            for q in disc(hx, hy, volume)
            if abs(_center(q)[0] - hx) >= 5.5 and _center(q)[1] < hy + 1.5
        }
        main = top | sides
    elif sk.view == "up":
        main = {q for q in disc(hx, hy - 0.3, volume) if _center(q)[1] < hy + 5.5}
    else:
        main = {
            q
            for q in disc(hx - 0.4, hy - 0.6, volume)
            if (_center(q)[1] < hy - 2.5 or _center(q)[0] < hx - 1.5) and _center(q)[1] < hy + 5.5
        }
    parts = [Part(mat, main, z=54, highlight=shine)]

    if style == "long":
        length = p.get("length", 10)
        if sk.view == "down":
            locks = capsule(hx - 6.5, hy - 1, hx - 6.8, hy + length, 2.1)
            locks |= capsule(hx + 6.5, hy - 1, hx + 6.8, hy + length, 2.1)
        elif sk.view == "up":
            locks = capsule(hx, hy, hx, hy + length, 6.2)
        else:
            locks = capsule(hx - 3.5, hy, hx - 5, hy + length, 3.0)
        parts.append(Part(mat, locks, z=53))
    elif style == "tower":
        h = p.get("height", 6)
        if sk.view == "right":
            block = polygon(
                [
                    (hx - 6, hy - 2),
                    (hx + 3.5, hy - 3),
                    (hx + 3.5, hy - 6 - h),
                    (hx - 6.5, hy - 6 - h),
                ]
            )
        else:
            block = polygon(
                [
                    (hx - 5.5, hy - 3),
                    (hx + 5.5, hy - 3),
                    (hx + 5.8, hy - 6 - h),
                    (hx - 5.8, hy - 6 - h),
                ]
            )
        top_left = (round(hx) - 4, round(hy - 5 - h))
        parts.append(Part(mat, block, z=55, highlight={top_left, (top_left[0] + 1, top_left[1])}))
    elif style == "spiky":
        spikes: set[Pixel] = set()
        for i in range(-2, 3):
            x = hx + i * 3 - (1.5 if sk.view == "right" else 0)
            spikes |= polygon([(x - 2.2, hy - 5), (x + 2.2, hy - 5), (x + i * 0.8, hy - 11)])
        parts.append(Part(mat, spikes, z=53.5))

    bangs = p.get("bangs")
    side = 1 if p.get("bangs_side", "right") == "right" else -1
    if bangs == "curl" and sk.view != "up":
        if sk.view == "down":
            strand = capsule(hx + side * 2.5, hy - 5, hx + side * 3.5, hy + 3, 1.1)
            strand |= disc(hx + side * 3, hy + 4.5, 1.6)
        else:
            strand = capsule(hx + 4.5, hy - 5, hx + 6.2, hy + 3, 1.1) | disc(
                hx + 5.8, hy + 4.5, 1.5
            )
        parts.append(Part(mat, strand, z=57))
    elif bangs == "fringe" and sk.view != "up":
        if sk.view == "down":
            fringe = {
                (x, y)
                for x in range(round(hx) - 5, round(hx) + 5)
                for y in range(round(hy) - 5, round(hy) - 2 + (x % 2))
            }
        else:
            fringe = rect(hx + 2, hy - 5, hx + 5, hy - 3)
        parts.append(Part(mat, fringe, z=55))
    return parts


# Headwear ----------------------------------------------------------------------------


def cap(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Peaked cap. Options: brim (default true), ragged_back (frayed into the hair), badge."""
    mat = p["material"]
    hx, hy = sk.head
    shift = -0.5 if sk.view == "right" else 0.0
    crown = {q for q in disc(hx + shift, hy - 1.6, 8.1) if _center(q)[1] < hy - 2.2}
    if p.get("ragged_back"):
        crown |= _ragged_back(sk.view, hx, hy)
    parts = [Part(mat, crown, z=56, highlight={(round(hx) - 4, round(hy) - 8)})]
    if p.get("brim", True):
        if sk.view == "down":
            parts.append(Part(mat, rect(hx - 6, hy - 3, hx + 5, hy - 2), z=57))
        elif sk.view == "right":
            parts.append(Part(mat, rect(hx + 3, hy - 3, hx + 9, hy - 2), z=57))
    badge = p.get("badge")
    if badge and sk.view == "down":
        parts.append(Part(badge, rect(hx - 1, hy - 6, hx, hy - 5), z=58, tone=2))
    elif badge and sk.view == "right":
        parts.append(Part(badge, rect(hx + 4, hy - 6, hx + 4, hy - 5), z=58, tone=2))
    return parts


def _ragged_back(view: str, hx: float, hy: float) -> set[Pixel]:
    """Jagged locks under the back of a cap, as if cap and hair were one piece."""
    if view == "up":
        outline = [(hx - 8, hy - 3)]
        x, i = hx - 8, 0
        while x <= hx + 8:
            outline.append((x, hy + (4.5 if i % 2 else 0.5)))
            x += 2.6
            i += 1
        outline.append((hx + 8, hy - 3))
        return polygon(outline)
    if view == "right":
        return polygon(
            [
                (hx - 1, hy - 4),
                (hx - 8.5, hy - 4),
                (hx - 10, hy - 1),
                (hx - 8, hy + 0.5),
                (hx - 9.5, hy + 3),
                (hx - 6.5, hy + 2.5),
                (hx - 6.5, hy + 5.5),
                (hx - 4, hy + 2.5),
                (hx - 2, hy),
            ]
        )
    left = polygon(
        [
            (hx - 6.5, hy - 3),
            (hx - 9, hy - 1),
            (hx - 7.5, hy + 1),
            (hx - 8.5, hy + 3.5),
            (hx - 6, hy + 2),
        ]
    )
    right = {(round(2 * hx) - 1 - x, y) for x, y in left}
    return left | right


def headband(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    hx, hy = sk.head
    band = {q for q in disc(hx, hy, 7.4) if hy - 5.5 <= _center(q)[1] <= hy - 3.5}
    return [Part(p["material"], band, z=55.5)]


# Clothes -----------------------------------------------------------------------------


def coat(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Coat over the torso with a skirt down the legs.

    Options: length (0 = hips, 1 = feet), open (shows the torso color down the front),
    collar (high collar, default true).
    """
    mat = p["material"]
    length = p.get("length", 0.8)
    opened = p.get("open", False)
    (ta, tb, tr) = sk.torso
    cx = sk.center_x
    body = capsule(*ta, *tb, tr + 0.6)
    if opened and sk.view == "down":
        body = {q for q in body if abs(_center(q)[0] - cx) > 1.1}
    elif opened and sk.view == "right":
        front = max(q[0] for q in body)
        body = {q for q in body if q[0] < front - 1}
    parts = [Part(mat, body, z=31)]

    feet_y = max(f[1] for f in sk.feet)
    top = sk.hip_y - 3
    bottom = sk.hip_y + length * (feet_y + 1 - sk.hip_y)
    if length > 0:
        if sk.view == "right":
            back = min(f[0] for f in sk.feet) - 3.5 - max(0.0, sk.lean)
            ahead = max(f[0] for f in sk.feet) + 2.5
            skirt = polygon([(cx - 6, top), (cx + 5, top), (ahead, bottom), (back, bottom)])
            parts.append(Part(mat, skirt, z=37))
        else:
            left = min(f[0] for f in sk.feet) - 3.5
            right = max(f[0] for f in sk.feet) + 3.5
            skirt = polygon([(cx - 6.5, top), (cx + 6.5, top), (right, bottom), (left, bottom)])
            span = max(1.0, bottom - top)
            if sk.view == "down" and opened:
                # Open coat: the flaps part a little more toward the hem.
                skirt = {
                    q
                    for q in skirt
                    if abs(_center(q)[0] - cx) > 0.6 + 1.6 * (_center(q)[1] - top) / span
                }
            else:
                skirt = {
                    q for q in skirt if not (abs(_center(q)[0] - cx) < 0.6 and q[1] > bottom - 4)
                }
            parts.append(Part(mat, skirt, z=12))

    if p.get("collar", True):
        hx, hy = sk.head
        if sk.view == "down":
            collar = polygon(
                [(hx - 7.5, hy + 3.5), (hx - 3.5, hy + 6), (hx - 4, hy + 9), (hx - 7, hy + 8)]
            )
            collar |= {(round(2 * hx) - 1 - x, y) for x, y in collar}
            parts.append(Part(mat, collar, z=49))
        elif sk.view == "up":
            parts.append(Part(mat, rect(hx - 6, hy + 5, hx + 5, hy + 8), z=51))
        else:
            parts.append(
                Part(
                    mat,
                    polygon(
                        [(hx - 6.5, hy + 3), (hx - 3, hy + 4), (hx - 3, hy + 9), (hx - 7, hy + 8)]
                    ),
                    z=51,
                )
            )
    return parts


def belt(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """Belt at the waist; count = 2 adds a second, slanted one. Option: buckle (color)."""
    mat = p["material"]
    (ta, tb, tr) = sk.torso
    torso = capsule(*ta, *tb, tr)
    y = round(sk.hip_y) - 2
    parts = [Part(mat, {q for q in torso if y <= q[1] <= y + 1}, z=30.5)]
    cx = sk.center_x
    if p.get("count", 1) >= 2 and sk.view != "right":
        slant = capsule(cx - 6, y - 3, cx + 6, y + 1, 0.6)
        parts.append(Part(mat, slant & capsule(*ta, *tb, tr + 1), z=30.6, tone=1))
    if p.get("buckle") and sk.view == "down":
        parts.append(Part(p["buckle"], rect(cx - 1, y, cx, y + 1), z=30.7, tone=2))
    return parts


# Accessories -------------------------------------------------------------------------


def chain(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A short chain hanging from the collar (on the wearer's left)."""
    hx, hy = sk.head
    if sk.view == "down":
        links = points(
            [
                (hx + 4, hy + 7),
                (hx + 4, hy + 8),
                (hx + 3, hy + 9),
                (hx + 3, hy + 10),
                (hx + 2, hy + 11),
            ]
        )
    elif sk.view == "right":
        links = points([(hx + 2, hy + 8), (hx + 3, hy + 9), (hx + 3, hy + 10)])
    else:
        return []
    return [Part(p["material"], links, z=34, tone=2)]


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
    hx, hy = round(sk.head[0]), round(sk.head[1])
    if sk.view == "right":
        pixels = {(hx - 1, hy + 3), (hx - 1, hy + 4)}
    else:
        pixels = {(hx - 7, hy + 2), (hx - 7, hy + 3), (hx + 6, hy + 2), (hx + 6, hy + 3)}
    return [Part(p["material"], pixels, z=58, tone=2)]


def seam(sk: Skeleton, p: dict, look: Look) -> list[Part]:
    """A line down the back of the head, so a featureless head reads as seen from behind."""
    if sk.view != "up":
        return []
    hx, hy = round(sk.head[0]), round(sk.head[1])
    return [Part(p["material"], {(hx - 1, y) for y in range(hy - 3, hy + 5)}, z=51)]


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
