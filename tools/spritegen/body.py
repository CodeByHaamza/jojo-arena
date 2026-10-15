"""The base body (head, torso, limbs) and the face, posed by a skeleton.

Drawing order (z) per view. Costume parts slot in between these values:
  legs 10, feet 11, arms 20, torso 30, head 50, face 52, hands 60 (front/back views);
  far limbs 5-8, torso 30, near leg 35-36, head 50, face 52, near arm 60-61 (profile).
"""

from __future__ import annotations

from .look import Look
from .raster import OUTLINE, Part, capsule, disc
from .skeleton import Skeleton


def body_parts(sk: Skeleton, look: Look) -> list[Part]:
    m = look.body
    hx, hy = sk.head
    head_highlight = {(round(hx) - 4, round(hy) - 4), (round(hx) - 3, round(hy) - 4)}
    (ta, tb, tr) = sk.torso
    head = Part(m["head"], disc(hx, hy, sk.head_r), z=50, highlight=head_highlight)
    if sk.view == "right":
        (far_sh, near_sh), (far_hand, near_hand) = sk.shoulders, sk.hands
        (far_hip, near_hip), (far_foot, near_foot) = sk.hips, sk.feet
        parts = [
            Part(m["arms"], capsule(*far_sh, *far_hand, 2.0), z=5),
            Part(m["hands"], disc(*far_hand, 2.2), z=6),
            Part(m["legs"], capsule(*far_hip, *far_foot, 2.5), z=7),
            Part(m["feet"], disc(far_foot[0] + 1, far_foot[1] + 1, 2.4), z=8),
            Part(m["torso"], capsule(*ta, *tb, tr), z=30),
            Part(m["legs"], capsule(*near_hip, *near_foot, 2.6), z=35),
            Part(m["feet"], disc(near_foot[0] + 1, near_foot[1] + 1, 2.5), z=36),
            head,
            Part(m["arms"], capsule(*near_sh, *near_hand, 2.2), z=60),
            Part(m["hands"], disc(*near_hand, 2.4), z=61),
        ]
    else:
        (sl, sr), (hl, hr) = sk.shoulders, sk.hands
        (pl, pr), (fl, fr) = sk.hips, sk.feet
        torso_highlight = {(round(ta[0]) - 4, round(ta[1]) - 3)}
        # Hands go in front of the body, except raised hands seen from the back.
        hands_z = 60 if sk.view == "down" or sk.big_hand or hr[1] > 27 else 15
        parts = [
            Part(m["legs"], capsule(*pl, *fl, 2.6), z=10),
            Part(m["legs"], capsule(*pr, *fr, 2.6), z=10),
            Part(m["feet"], disc(fl[0], fl[1] + 1, 2.4), z=11),
            Part(m["feet"], disc(fr[0], fr[1] + 1, 2.4), z=11),
            Part(m["arms"], capsule(*sl, *hl, 2.1), z=20),
            Part(m["arms"], capsule(*sr, *hr, 2.1), z=20),
            Part(m["torso"], capsule(*ta, *tb, tr), z=30, highlight=torso_highlight),
            head,
            Part(m["hands"], disc(*hl, 2.3), z=hands_z),
            Part(m["hands"], disc(*hr, 3.0 if sk.big_hand else 2.3), z=hands_z),
        ]
    return parts + face_parts(sk, look)


def face_parts(sk: Skeleton, look: Look) -> list[Part]:
    """Eyes (and optional brows and mouth). Nothing from the back."""
    if sk.view == "up":
        return []
    face = look.face
    eye_color = face.get("eyes", "outline")
    tall = face.get("tall_eyes", True)
    hx, hy = round(sk.head[0]), round(sk.head[1])
    if sk.view == "down":
        eyes = {(hx - 3, hy + 1), (hx + 2, hy + 1)}
        if tall:
            eyes = {(hx - 3, hy), (hx - 3, hy + 1), (hx + 2, hy), (hx + 2, hy + 1)}
        brows = {(hx - 4, hy - 1), (hx - 3, hy - 1), (hx + 2, hy - 1), (hx + 3, hy - 1)}
        mouth = {(hx - 1, hy + 4), (hx, hy + 4)}
    else:
        eyes = {(hx + 4, hy - 1), (hx + 4, hy)} if tall else {(hx + 4, hy)}
        brows = {(hx + 3, hy - 2), (hx + 4, hy - 2)}
        mouth = {(hx + 5, hy + 4)}
    parts = [_eye_part(eyes, eye_color)]
    if face.get("brows"):
        parts.append(Part("", brows, z=52, flat=OUTLINE))
    if face.get("mouth"):
        parts.append(Part(look.body["head"], mouth, z=52, tone=0))
    return parts


def _eye_part(pixels: set, color: str) -> Part:
    if color == "outline":
        return Part("", pixels, z=52, flat=OUTLINE)
    return Part(color, pixels, z=52, tone=0)
