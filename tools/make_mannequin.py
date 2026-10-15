"""Generate the generic 48 px mannequin sprite sheet (style A) used as a base to dress.

    python tools/make_mannequin.py

Writes jojo_arena/assets/sprites/mannequin/mannequin.png and mannequin.toml.
The figure is a neutral wooden-doll body: no character, no costume. It uses fixed
"key" colors (grays for the body, browns for joints) that the game swaps for each
character's palette, and that an artist can repaint freely.

Layout: one row per (animation, direction), one 48x48 cell per frame.
Directions are down, up, right; the game mirrors "right" to get "left".
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

CELL = 48
ANCHOR = (24, 44)
DIRECTIONS = ("down", "up", "right")
OUTLINE = (23, 18, 31)

# Key colors: dark, mid, light, highlight. The loader swaps them per character.
BODY_KEYS = [(68, 68, 76), (116, 116, 124), (164, 164, 172), (212, 212, 220)]
TRIM_KEYS = [(78, 62, 54), (118, 96, 82), (160, 134, 114)]
MATERIALS = {"body": BODY_KEYS, "trim": TRIM_KEYS}

OUT_DIR = Path(__file__).resolve().parents[1] / "jojo_arena" / "assets" / "sprites" / "mannequin"

Pixel = tuple[int, int]


# Rasterizing ---------------------------------------------------------------------------


def disc(cx: float, cy: float, r: float) -> set[Pixel]:
    return {
        (x, y)
        for x in range(math.floor(cx - r) - 1, math.ceil(cx + r) + 1)
        for y in range(math.floor(cy - r) - 1, math.ceil(cy + r) + 1)
        if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r
    }


def capsule(x1: float, y1: float, x2: float, y2: float, r: float) -> set[Pixel]:
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx * dx + dy * dy or 1e-9
    pixels = set()
    for x in range(math.floor(min(x1, x2) - r) - 1, math.ceil(max(x1, x2) + r) + 1):
        for y in range(math.floor(min(y1, y2) - r) - 1, math.ceil(max(y1, y2) + r) + 1):
            px, py = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length_sq))
            if (px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2 <= r * r:
                pixels.add((x, y))
    return pixels


@dataclass
class Part:
    material: str
    pixels: set[Pixel]
    highlight: list[Pixel] = field(default_factory=list)
    flat: tuple[int, int, int] | None = None  # unshaded color (eyes)


def render(parts: list[Part]) -> pygame.Surface:
    """Draw parts back to front, shade each one from the top-left, then outline."""
    owner: dict[Pixel, int] = {}
    for index, part in enumerate(parts):
        for p in part.pixels:
            if 0 <= p[0] < CELL and 0 <= p[1] < CELL:
                owner[p] = index
    surface = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    for (x, y), index in owner.items():
        part = parts[index]
        if part.flat:
            surface.set_at((x, y), part.flat)
            continue
        tones = MATERIALS[part.material]
        shape = part.pixels
        neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        over_other = any(owner.get(n, index) < index for n in neighbors)
        if over_other or (x + 1, y) not in shape or (x, y + 1) not in shape:
            tone = 0
        elif (x - 1, y) not in shape or (x, y - 1) not in shape:
            tone = 2
        else:
            tone = 1
        if (x, y) in part.highlight:
            tone = len(tones) - 1
        surface.set_at((x, y), tones[tone])
    for y in range(CELL):
        for x in range(CELL):
            if (x, y) in owner:
                continue
            if any(n in owner for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                surface.set_at((x, y), OUTLINE)
    return surface


# The figure ----------------------------------------------------------------------------


@dataclass
class Pose:
    """Offsets from the neutral stance, in pixels. Hands/feet are relative to rest."""

    bob: float = 0.0  # whole upper body down
    lean: float = 0.0  # upper body forward (side view) or sideways (front view)
    head: tuple[float, float] = (0.0, 0.0)
    hand_l: tuple[float, float] = (0.0, 0.0)  # far / screen-left hand
    hand_r: tuple[float, float] = (0.0, 0.0)  # near / screen-right hand
    foot_l: tuple[float, float] = (0.0, 0.0)
    foot_r: tuple[float, float] = (0.0, 0.0)
    big_hand_r: bool = False  # foreshortened fist coming at the viewer


def front_figure(pose: Pose, facing_viewer: bool) -> list[Part]:
    b, lean = pose.bob, pose.lean
    hip_y = 33 + b * 0.5
    torso_top = 21 + b
    hx, hy = 24 + lean + pose.head[0], 13 + b + pose.head[1]
    sl, sr = (17.5 + lean, 22 + b), (30.5 + lean, 22 + b)  # shoulders
    hl = (15 + lean + pose.hand_l[0], 31 + b + pose.hand_l[1])
    hr = (33 + lean + pose.hand_r[0], 31 + b + pose.hand_r[1])
    fl = (21 + pose.foot_l[0], 42 + pose.foot_l[1])
    fr = (27 + pose.foot_r[0], 42 + pose.foot_r[1])

    parts = [
        Part("body", capsule(21, hip_y, *fl, 2.6)),
        Part("body", capsule(27, hip_y, *fr, 2.6)),
        Part("trim", disc(fl[0], fl[1] + 1, 2.4)),
        Part("trim", disc(fr[0], fr[1] + 1, 2.4)),
    ]
    arm_l = Part("body", capsule(*sl, *hl, 2.1))
    arm_r = Part("body", capsule(*sr, *hr, 2.1))
    torso = Part(
        "body",
        capsule(24 + lean, torso_top + 4, 24 + lean * 0.5, hip_y - 2, 6.2),
        highlight=[(20 + round(lean), round(torso_top) + 1)],
    )
    belt = Part("trim", {(x, round(hip_y) - 1) for x in range(19, 30)} & torso.pixels)
    head_part = Part(
        "body",
        disc(hx, hy, 7.0),
        highlight=[(round(hx) - 4, round(hy) - 4), (round(hx) - 3, round(hy) - 4)],
    )
    hand_r_radius = 3.0 if pose.big_hand_r else 2.3
    parts += [arm_l, arm_r, torso, belt, head_part]
    if facing_viewer:
        eye_y = round(hy) + 1
        parts.append(Part("body", {(round(hx) - 3, eye_y)}, flat=OUTLINE))
        parts.append(Part("body", {(round(hx) + 2, eye_y)}, flat=OUTLINE))
    else:
        # Back of the head: a seam so "up" never reads as "down".
        parts.append(
            Part("trim", {(round(hx) - 1, y) for y in range(round(hy) - 3, round(hy) + 5)})
        )
    hands_in_front = facing_viewer or pose.big_hand_r
    hand_parts = [
        Part("trim", disc(*hl, 2.3)),
        Part("trim", disc(*hr, hand_r_radius)),
    ]
    if hands_in_front or hr[1] > 27:
        parts += hand_parts
    else:
        parts = parts[:4] + hand_parts + parts[4:]
    return parts


def side_figure(pose: Pose) -> list[Part]:
    b, lean = pose.bob, pose.lean
    hip = (24, 33 + b * 0.5)
    torso_top = (24 + lean, 21 + b)
    head = (25 + lean * 1.2 + pose.head[0], 13 + b + pose.head[1])
    shoulder = (24 + lean, 23 + b)
    near_shoulder = (shoulder[0] + 1.5, shoulder[1])
    hand_far = (shoulder[0] - 1 + pose.hand_l[0], 31 + b + pose.hand_l[1])
    hand_near = (shoulder[0] + 2.5 + pose.hand_r[0], 31 + b + pose.hand_r[1])
    foot_far = (22 + pose.foot_l[0], 42 + pose.foot_l[1])
    foot_near = (26 + pose.foot_r[0], 42 + pose.foot_r[1])

    head_part = Part(
        "body",
        disc(*head, 7.0),
        highlight=[
            (round(head[0]) - 4, round(head[1]) - 4),
            (round(head[0]) - 3, round(head[1]) - 4),
        ],
    )
    torso = Part("body", capsule(*torso_top, hip[0], hip[1] - 2, 5.4))
    return [
        Part("body", capsule(*shoulder, *hand_far, 2.0)),
        Part("trim", disc(*hand_far, 2.2)),
        Part("body", capsule(hip[0] - 1, hip[1], *foot_far, 2.5)),
        Part("trim", disc(foot_far[0] + 1, foot_far[1] + 1, 2.4)),
        torso,
        Part("trim", {(x, round(hip[1]) - 1) for x in range(18, 31)} & torso.pixels),
        Part("body", capsule(hip[0] + 1, hip[1], *foot_near, 2.6)),
        Part("trim", disc(foot_near[0] + 1, foot_near[1] + 1, 2.5)),
        head_part,
        Part("body", {(round(head[0]) + 4, round(head[1]))}, flat=OUTLINE),
        Part("body", capsule(*near_shoulder, *hand_near, 2.2)),
        Part("trim", disc(*hand_near, 2.4)),
    ]


def lying_figure(sink: float) -> list[Part]:
    """Knocked out, flat on the ground (same for every view)."""
    y = 39 + sink
    torso = Part("body", capsule(17, y, 29, y, 5.0))
    return [
        Part("body", capsule(29, y - 1, 41, y - 2, 2.5)),
        Part("body", capsule(29, y + 2, 41, y + 2, 2.5)),
        Part("trim", disc(42, y - 2, 2.3)),
        Part("trim", disc(42, y + 2, 2.3)),
        Part("body", capsule(19, y - 5, 27, y - 7, 2.0)),
        torso,
        Part("trim", {(29, yy) for yy in range(round(y) - 4, round(y) + 5)} & torso.pixels),
        Part("body", disc(11, y - 1, 6.5), highlight=[(8, round(y) - 5)]),
        Part("body", capsule(18, y + 4, 26, y + 6, 2.0)),
        Part("trim", disc(27, y + 6, 2.2)),
    ]


# Animations: name -> (fps, loop, phases, list of poses per view) ----------------------

Frames = list[Pose]


def anim_frames(view: str) -> dict[str, tuple[int, bool, list[int] | None, list]]:
    side = view == "right"
    up = view == "up"
    fwd = -1 if up else 1  # "toward the target" on the screen's y axis for front/back views

    def punch(reach: float) -> Pose:
        if side:
            return Pose(
                lean=1.5, hand_r=(reach, -8), hand_l=(-3, -2), foot_r=(3, 0), foot_l=(-2, 0)
            )
        return Pose(hand_r=(-6, (-14 if up else -3) * (reach / 12)), big_hand_r=not up, head=(0, 0))

    idle = [Pose(bob=b, hand_l=(0, b * 0.5), hand_r=(0, b * 0.5)) for b in (0, 0, 1, 1)]
    if side:
        walk = [
            Pose(bob=0, foot_l=(-4, 0), foot_r=(4, 0), hand_l=(3, -1), hand_r=(-3, -1)),
            Pose(bob=-1, foot_l=(0, -1), foot_r=(0, 0)),
            Pose(bob=0, foot_l=(4, 0), foot_r=(-4, 0), hand_l=(-3, -1), hand_r=(3, -1)),
            Pose(bob=-1, foot_l=(0, 0), foot_r=(0, -1)),
        ]
    else:
        walk = [
            Pose(bob=0, foot_l=(0, -2), hand_l=(0, 2 * fwd), hand_r=(0, -2 * fwd)),
            Pose(bob=-1),
            Pose(bob=0, foot_r=(0, -2), hand_l=(0, -2 * fwd), hand_r=(0, 2 * fwd)),
            Pose(bob=-1),
        ]
    light = [
        Pose(lean=-1, hand_r=(-4, -6) if side else (0, -4), hand_l=(0, -3)),
        punch(12),
        punch(9),
        Pose(lean=0.5, hand_r=(2, -4) if side else (-1, -2)),
    ]
    if side:
        heavy = [
            Pose(lean=-2, bob=1, hand_r=(-7, -4), hand_l=(-5, -3), foot_l=(-3, 0)),
            Pose(lean=-2.5, bob=1, hand_r=(-8, -6), hand_l=(-6, -4), foot_l=(-3, 0)),
            Pose(lean=3, hand_r=(14, -7), hand_l=(10, -6), foot_r=(5, 0), foot_l=(-4, 0)),
            Pose(lean=2.5, hand_r=(12, -6), hand_l=(8, -5), foot_r=(5, 0), foot_l=(-4, 0)),
            Pose(lean=1, hand_r=(4, -3), hand_l=(2, -2), foot_r=(2, 0)),
        ]
        special = [
            Pose(lean=-1, hand_r=(-4, -4), hand_l=(-5, -4)),
            Pose(lean=-1.5, bob=1, hand_r=(-5, -5), hand_l=(-6, -5)),
            Pose(lean=2, hand_r=(11, -9), hand_l=(10, -7), foot_r=(3, 0)),
            Pose(lean=1, hand_r=(8, -8), hand_l=(7, -6)),
        ]
        dash = [
            Pose(lean=3, bob=1, hand_l=(-6, -3), hand_r=(-5, -4), foot_l=(-5, 0), foot_r=(5, -1)),
            Pose(lean=3.5, bob=1, hand_l=(-7, -4), hand_r=(-6, -5), foot_l=(-6, 0), foot_r=(6, 0)),
        ]
        guard = [Pose(lean=-0.5, bob=1, hand_r=(5, -14), hand_l=(4, -11), foot_l=(-2, 0))]
        hurt = [
            Pose(lean=-3, head=(-2, 0), hand_r=(-4, -8), hand_l=(-6, -6), foot_r=(2, 0)),
            Pose(lean=-2, head=(-1, 1), bob=1, hand_r=(-3, -5), hand_l=(-5, -4)),
        ]
        pose = [
            Pose(
                lean=-1.5,
                head=(-1, -1),
                hand_r=(4, -19),
                hand_l=(-4, -4),
                foot_r=(4, 0),
                foot_l=(-3, 0),
            ),
            Pose(
                lean=-1.5,
                head=(-1, -1),
                bob=1,
                hand_r=(4, -18),
                hand_l=(-4, -3),
                foot_r=(4, 0),
                foot_l=(-3, 0),
            ),
        ]
    else:
        heavy = [
            Pose(bob=1, lean=-1, hand_r=(2, -6 * fwd), hand_l=(0, -4 * fwd)),
            Pose(bob=1, lean=-1.5, hand_r=(3, -8 * fwd), hand_l=(-1, -6 * fwd)),
            Pose(
                bob=-1,
                hand_r=(-8, (-15 if up else -2)),
                hand_l=(8, (-15 if up else -2)),
                big_hand_r=not up,
            ),
            Pose(
                bob=-1,
                hand_r=(-7, (-13 if up else -2)),
                hand_l=(7, (-13 if up else -2)),
                big_hand_r=not up,
            ),
            Pose(hand_r=(-2, -3), hand_l=(2, -3)),
        ]
        special = [
            Pose(bob=1, hand_r=(-3, -6), hand_l=(3, -6)),
            Pose(bob=1, hand_r=(-4, -8), hand_l=(4, -8)),
            Pose(
                hand_r=(-8, (-16 if up else -5)), hand_l=(8, (-16 if up else -5)), big_hand_r=not up
            ),
            Pose(hand_r=(-7, (-14 if up else -4)), hand_l=(7, (-14 if up else -4))),
        ]
        dash = [
            Pose(bob=2, hand_l=(-3, -2 * fwd), hand_r=(3, -2 * fwd), foot_l=(-2, 0), foot_r=(2, 0)),
            Pose(
                bob=2, hand_l=(-4, -3 * fwd), hand_r=(4, -3 * fwd), foot_l=(-2, -1), foot_r=(2, -1)
            ),
        ]
        guard = [Pose(bob=1, hand_r=(-8, -9), hand_l=(8, -9))]
        hurt = [
            Pose(lean=2, head=(1, -1), hand_r=(4, -10), hand_l=(-4, -10), foot_l=(-1, 0)),
            Pose(lean=1, head=(1, 0), bob=1, hand_r=(3, -6), hand_l=(-3, -6)),
        ]
        pose = [
            Pose(
                lean=1,
                head=(1, -1),
                hand_r=(-11, -19),
                hand_l=(3, -2),
                foot_l=(-2, 0),
                foot_r=(2, 0),
            ),
            Pose(
                lean=1,
                head=(1, -1),
                bob=1,
                hand_r=(-11, -18),
                hand_l=(3, -1),
                foot_l=(-2, 0),
                foot_r=(2, 0),
            ),
        ]
    ko = [
        hurt[0],
        Pose(bob=5, lean=-2, head=(-1, 2), hand_l=(-3, 2), hand_r=(3, 2)),
        "lying0",
        "lying1",
    ]
    return {
        "idle": (6, True, None, idle),
        "walk": (10, True, None, walk),
        "light": (12, False, [1, 1, 2], light),
        "heavy": (12, False, [2, 1, 2], heavy),
        "special": (12, False, [2, 1, 1], special),
        "dash": (14, False, None, dash),
        "guard": (1, True, None, guard),
        "hurt": (10, False, None, hurt),
        "ko": (8, False, None, ko),
        "pose": (3, True, None, pose),
    }


def draw_pose(view: str, pose: Pose | str) -> pygame.Surface:
    if isinstance(pose, str):
        return render(lying_figure(0 if pose == "lying0" else 1))
    if view == "right":
        return render(side_figure(pose))
    return render(front_figure(pose, facing_viewer=(view == "down")))


def main() -> None:
    pygame.init()
    tables = {view: anim_frames(view) for view in DIRECTIONS}
    names = list(tables["down"])
    max_frames = max(len(entry[3]) for entry in tables["down"].values())
    sheet = pygame.Surface(
        (max_frames * CELL, len(names) * len(DIRECTIONS) * CELL), pygame.SRCALPHA
    )
    spec = [
        "# Generated by tools/make_mannequin.py. Edit the script, not this file.",
        f"frame_size = [{CELL}, {CELL}]",
        f"anchor = [{ANCHOR[0]}, {ANCHOR[1]}]",
        'directions = ["down", "up", "right"]',
        "",
        "[recolor]",
        f"body = {[list(c) for c in BODY_KEYS]}",
        f"trim = {[list(c) for c in TRIM_KEYS]}",
    ]
    for anim_index, name in enumerate(names):
        fps, loop, phases, _ = tables["down"][name]
        row = anim_index * len(DIRECTIONS)
        for dir_index, view in enumerate(DIRECTIONS):
            for frame_index, pose in enumerate(tables[view][name][3]):
                cell = draw_pose(view, pose)
                sheet.blit(cell, (frame_index * CELL, (row + dir_index) * CELL))
        spec += ["", f"[anims.{name}]", f"row = {row}", f"frames = {len(tables['down'][name][3])}"]
        spec += [f"fps = {fps}", f"loop = {'true' if loop else 'false'}"]
        if phases:
            spec.append(f"phases = {phases}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pygame.image.save(sheet, str(OUT_DIR / "mannequin.png"))
    (OUT_DIR / "mannequin.toml").write_text("\n".join(spec) + "\n", encoding="utf-8")
    print(f"wrote {OUT_DIR / 'mannequin.png'} ({sheet.get_width()}x{sheet.get_height()})")


if __name__ == "__main__":
    main()
