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
    b = sk.build
    hx, hy = sk.head
    shine = round(0.57 * b.head_r)
    head_highlight = {
        (round(hx) - shine, round(hy) - shine),
        (round(hx) - shine + 1, round(hy) - shine),
    }
    (ta, tb, tr) = sk.torso
    head = Part(m["head"], disc(hx, hy, b.head_r), z=50, highlight=head_highlight)
    if sk.view == "right":
        (far_sh, near_sh), (far_hand, near_hand) = sk.shoulders, sk.hands
        (far_hip, near_hip), (far_foot, near_foot) = sk.hips, sk.feet
        parts = [
            Part(m["arms"], capsule(*far_sh, *far_hand, b.arm_r * 0.95), z=5),
            Part(m["hands"], disc(*far_hand, b.hand_r * 0.95), z=6),
            Part(m["legs"], capsule(*far_hip, *far_foot, b.leg_r * 0.96), z=7),
            Part(m["feet"], disc(far_foot[0] + 1, far_foot[1] + 1, b.foot_r), z=8),
            Part(m["torso"], capsule(*ta, *tb, tr), z=30),
            Part(m["legs"], capsule(*near_hip, *near_foot, b.leg_r), z=35),
            Part(m["feet"], disc(near_foot[0] + 1, near_foot[1] + 1, b.foot_r * 1.04), z=36),
            head,
            Part(m["arms"], capsule(*near_sh, *near_hand, b.arm_r * 1.05), z=60),
            Part(m["hands"], disc(*near_hand, b.hand_r * 1.15), z=61),
        ]
    else:
        (sl, sr), (hl, hr) = sk.shoulders, sk.hands
        (pl, pr), (fl, fr) = sk.hips, sk.feet
        torso_highlight = {(round(ta[0] - 0.65 * tr), round(ta[1] - 0.5 * tr))}
        # Hands go in front of the body, except raised hands seen from the back.
        rest_y = sk.shoulder_y + b.arms * 0.6
        hands_z = 60 if sk.view == "down" or sk.big_hand or hr[1] > rest_y else 15
        parts = [
            Part(m["legs"], capsule(*pl, *fl, b.leg_r), z=10),
            Part(m["legs"], capsule(*pr, *fr, b.leg_r), z=10),
            Part(m["feet"], disc(fl[0], fl[1] + 1, b.foot_r), z=11),
            Part(m["feet"], disc(fr[0], fr[1] + 1, b.foot_r), z=11),
            Part(m["arms"], capsule(*sl, *hl, b.arm_r), z=20),
            Part(m["arms"], capsule(*sr, *hr, b.arm_r), z=20),
            Part(m["torso"], capsule(*ta, *tb, tr), z=30, highlight=torso_highlight),
            head,
            Part(m["hands"], disc(*hl, b.hand_r), z=hands_z),
            Part(m["hands"], disc(*hr, b.hand_r * (1.35 if sk.big_hand else 1.0)), z=hands_z),
        ]
    return parts + face_parts(sk, look)


def face_parts(sk: Skeleton, look: Look) -> list[Part]:
    """Eyes, and optional brows, mouth and nose. Nothing from the back.

    face.eyes = "outline" or a palette color (the iris);
    face.eye_style = dot (1 pixel), tall (1x2) or wide (2x2: eyelid over iris).
    """
    if sk.view == "up":
        return []
    face = look.face
    eye_color = face.get("eyes", "outline")
    style = face.get("eye_style", "tall")
    r = sk.head_r
    hx = round(sk.head[0])
    ey = round(sk.head[1] + 0.15 * r)
    lids: set = set()
    if sk.view == "down":
        e = round(0.33 * r)
        left, right = hx - e - 1, hx + e
        if style == "dot":
            irises = {(left, ey), (right, ey)}
        elif style == "wide":
            irises = {(left - 1, ey), (left, ey), (right, ey), (right + 1, ey)}
            lids = {(x, ey - 1) for x, _ in irises}
        else:
            irises = {(left, ey - 1), (left, ey), (right, ey - 1), (right, ey)}
        brow_y = ey - (3 if style == "wide" else 2)
        brows = {(left - 1, brow_y), (left, brow_y), (right, brow_y), (right + 1, brow_y)}
        mouth = {(hx - 1, round(sk.head[1] + 0.6 * r)), (hx, round(sk.head[1] + 0.6 * r))}
        nose: set = set()
    else:
        ex = round(sk.head[0] + 0.57 * r)
        if style == "dot":
            irises = {(ex, ey)}
        elif style == "wide":
            irises = {(ex, ey)}
            lids = {(ex, ey - 1), (ex - 1, ey - 1)}
        else:
            irises = {(ex, ey - 1), (ex, ey)}
        brows = {
            (ex - 1, ey - (3 if style == "wide" else 2)),
            (ex, ey - (3 if style == "wide" else 2)),
        }
        mouth = {(ex + 1, round(sk.head[1] + 0.6 * r))}
        nose = {(round(sk.head[0] + r), round(sk.head[1] + 0.25 * r))}
    parts = [_eye_part(irises, eye_color)]
    if lids:
        parts.append(Part("", lids, z=52.5, flat=OUTLINE))
    if face.get("brows"):
        parts.append(Part("", brows, z=52, flat=OUTLINE))
    if face.get("mouth"):
        parts.append(Part(look.body["head"], mouth, z=52, tone=0))
    if face.get("nose") and nose:
        parts.append(Part(look.body["head"], nose, z=49))
    return parts


def _eye_part(pixels: set, color: str) -> Part:
    if color == "outline":
        return Part("", pixels, z=52, flat=OUTLINE)
    return Part(color, pixels, z=52, tone=1)
