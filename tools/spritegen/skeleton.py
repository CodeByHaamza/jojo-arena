"""The body skeleton, its poses, and the animation table shared by every character.

Coordinates are pixels inside a 48x48 cell, feet around (24, 44). Views are "down"
(facing the camera), "up" (back to the camera) and "right" (profile); "left" is
mirrored by the game. In profile, index 0 of a pair is the far limb, 1 the near one.
"""

from __future__ import annotations

from dataclasses import dataclass

Point = tuple[float, float]
DIRECTIONS = ("down", "up", "right")
LYING = ("lying0", "lying1")  # knocked-out frames, drawn by rotating a standing pose


@dataclass(frozen=True)
class Pose:
    """Offsets from the neutral stance, in pixels. Hands and feet are relative to rest."""

    bob: float = 0.0  # whole upper body down
    lean: float = 0.0  # upper body forward (profile) or sideways (front/back)
    head: Point = (0.0, 0.0)
    hand_l: Point = (0.0, 0.0)  # screen-left hand, or far hand in profile
    hand_r: Point = (0.0, 0.0)  # screen-right hand, or near hand in profile
    foot_l: Point = (0.0, 0.0)
    foot_r: Point = (0.0, 0.0)
    big_hand_r: bool = False  # foreshortened fist coming at the viewer


@dataclass(frozen=True)
class Skeleton:
    view: str
    head: Point
    head_r: float
    torso: tuple[Point, Point, float]  # capsule: top, bottom, radius
    shoulders: tuple[Point, Point]
    hands: tuple[Point, Point]
    hips: tuple[Point, Point]
    feet: tuple[Point, Point]
    hip_y: float
    lean: float
    big_hand: bool

    @property
    def center_x(self) -> float:
        return (self.torso[0][0] + self.torso[1][0]) / 2


def make_skeleton(view: str, pose: Pose) -> Skeleton:
    b, lean = pose.bob, pose.lean
    if view == "right":
        hip = (24.0, 33 + b * 0.5)
        shoulder = (24 + lean, 23 + b)
        return Skeleton(
            view=view,
            head=(25 + lean * 1.2 + pose.head[0], 13 + b + pose.head[1]),
            head_r=7.0,
            torso=((24 + lean, 21 + b), (hip[0], hip[1] - 2), 5.4),
            shoulders=(shoulder, (shoulder[0] + 1.5, shoulder[1])),
            hands=(
                (shoulder[0] - 1 + pose.hand_l[0], 31 + b + pose.hand_l[1]),
                (shoulder[0] + 2.5 + pose.hand_r[0], 31 + b + pose.hand_r[1]),
            ),
            hips=((hip[0] - 1, hip[1]), (hip[0] + 1, hip[1])),
            feet=(
                (22 + pose.foot_l[0], 42 + pose.foot_l[1]),
                (26 + pose.foot_r[0], 42 + pose.foot_r[1]),
            ),
            hip_y=hip[1],
            lean=lean,
            big_hand=False,
        )
    hip_y = 33 + b * 0.5
    torso_top = 21 + b
    return Skeleton(
        view=view,
        head=(24 + lean + pose.head[0], 13 + b + pose.head[1]),
        head_r=7.0,
        torso=((24 + lean, torso_top + 4), (24 + lean * 0.5, hip_y - 2), 6.2),
        shoulders=((17.5 + lean, 22 + b), (30.5 + lean, 22 + b)),
        hands=(
            (15 + lean + pose.hand_l[0], 31 + b + pose.hand_l[1]),
            (33 + lean + pose.hand_r[0], 31 + b + pose.hand_r[1]),
        ),
        hips=((21.0, hip_y), (27.0, hip_y)),
        feet=(
            (21 + pose.foot_l[0], 42 + pose.foot_l[1]),
            (27 + pose.foot_r[0], 42 + pose.foot_r[1]),
        ),
        hip_y=hip_y,
        lean=lean,
        big_hand=pose.big_hand_r,
    )


# Animations: name -> (fps, loop, phases, frames). A frame is a Pose or a LYING marker.

AnimTable = dict[str, tuple[int, bool, list[int] | None, list]]


def animations(view: str) -> AnimTable:
    side = view == "right"
    up = view == "up"
    fwd = -1 if up else 1  # "toward the target" on the screen's y axis, front/back views

    def punch(reach: float) -> Pose:
        if side:
            return Pose(
                lean=1.5, hand_r=(reach, -8), hand_l=(-3, -2), foot_r=(3, 0), foot_l=(-2, 0)
            )
        return Pose(hand_r=(-6, (-14 if up else -3) * (reach / 12)), big_hand_r=not up)

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
                hand_r=(-8, -15 if up else -2),
                hand_l=(8, -15 if up else -2),
                big_hand_r=not up,
            ),
            Pose(
                bob=-1,
                hand_r=(-7, -13 if up else -2),
                hand_l=(7, -13 if up else -2),
                big_hand_r=not up,
            ),
            Pose(hand_r=(-2, -3), hand_l=(2, -3)),
        ]
        special = [
            Pose(bob=1, hand_r=(-3, -6), hand_l=(3, -6)),
            Pose(bob=1, hand_r=(-4, -8), hand_l=(4, -8)),
            Pose(hand_r=(-8, -16 if up else -5), hand_l=(8, -16 if up else -5), big_hand_r=not up),
            Pose(hand_r=(-7, -14 if up else -4), hand_l=(7, -14 if up else -4)),
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
    ko = [hurt[0], Pose(bob=5, lean=-2, head=(-1, 2), hand_l=(-3, 2), hand_r=(3, 2)), *LYING]
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
