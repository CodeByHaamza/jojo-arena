"""The body skeleton, its proportions, its poses, and the animation table.

Coordinates are pixels inside a square cell (64 px by default), feet near the bottom.
Views are "down" (facing the camera), "up" (back to the camera) and "right"
(profile); "left" is mirrored by the game. In profile, index 0 of a pair is the far
limb and 1 the near one.

Poses were authored for limbs of 9 px; hand and foot offsets are scaled by the real
arm and leg lengths, so every body shape can play the same animations.
"""

from __future__ import annotations

from dataclasses import dataclass

Point = tuple[float, float]
DIRECTIONS = ("down", "up", "right")
LYING = ("lying0", "lying1")  # knocked-out frames, drawn by rotating a standing pose
POSE_LIMB = 9.0  # limb length the pose offsets were written for
MAX_REACH_SCALE = 1.45


@dataclass(frozen=True)
class Build:
    """Body proportions in pixels. The defaults are a standard adult, about 44 px tall."""

    head_r: float = 5.6
    neck: float = 1.5  # gap between the chin and the shoulder line
    torso: float = 13.0  # shoulder line to hips
    legs: float = 16.0  # hips to ankles
    arms: float = 14.0  # shoulder to hand, arms hanging
    shoulders: float = 8.0  # half the shoulder width
    hips: float = 3.2  # half the gap between the legs
    torso_r: float = 5.6
    arm_r: float = 2.0
    leg_r: float = 2.4
    hand_r: float = 2.1
    foot_r: float = 2.3


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
    build: Build
    head: Point
    torso: tuple[Point, Point, float]  # capsule: top, bottom, radius
    shoulders: tuple[Point, Point]
    hands: tuple[Point, Point]
    hips: tuple[Point, Point]
    feet: tuple[Point, Point]
    shoulder_y: float
    hip_y: float
    lean: float
    big_hand: bool

    @property
    def head_r(self) -> float:
        return self.build.head_r

    @property
    def k(self) -> float:
        """Head scale: head-relative shapes were designed for a head radius of 7."""
        return self.build.head_r / 7.0

    @property
    def center_x(self) -> float:
        return (self.torso[0][0] + self.torso[1][0]) / 2

    def at(self, dx: float, dy: float) -> Point:
        """A point given relative to the head center, in head units."""
        return self.head[0] + dx * self.k, self.head[1] + dy * self.k


def feet_line(cell: int) -> float:
    return cell - 6.0


def make_skeleton(view: str, pose: Pose, build: Build, cell: int) -> Skeleton:
    cx = cell / 2
    feet_y = feet_line(cell)
    # Long arms swing a little less than their length, so punches stay inside the cell.
    arm_k = min(build.arms / POSE_LIMB, MAX_REACH_SCALE)
    leg_k = build.legs / POSE_LIMB
    b, lean = pose.bob, pose.lean
    hip_y = feet_y - build.legs + b * 0.5
    shoulder_y = feet_y - build.legs - build.torso + b
    head_y = shoulder_y - build.neck - build.head_r + pose.head[1]

    def hand(x: float, y: float, off: Point) -> Point:
        # Hands raised high (poses) stay inside the cell, outline included.
        margin = build.hand_r + 4  # gloves and cuffs stick out a little
        return x + off[0] * arm_k, max(margin, y + off[1] * arm_k)

    def foot(x: float, off: Point) -> Point:
        return x + off[0] * leg_k, feet_y + off[1] * leg_k

    if view == "right":
        torso_r = build.torso_r * 0.87
        shoulder = (cx + lean, shoulder_y + 1)
        return Skeleton(
            view=view,
            build=build,
            head=(cx + 1 + lean * 1.2 + pose.head[0], head_y),
            torso=((cx + lean, shoulder_y + torso_r - 3.2), (cx, hip_y - 2), torso_r),
            shoulders=(shoulder, (shoulder[0] + 1.5, shoulder[1])),
            hands=(
                hand(shoulder[0] - 1, shoulder_y + build.arms, pose.hand_l),
                hand(shoulder[0] + 2.5, shoulder_y + build.arms, pose.hand_r),
            ),
            hips=((cx - 1, hip_y), (cx + 1, hip_y)),
            feet=(foot(cx - 2, pose.foot_l), foot(cx + 2, pose.foot_r)),
            shoulder_y=shoulder_y,
            hip_y=hip_y,
            lean=lean,
            big_hand=False,
        )
    half = build.shoulders
    return Skeleton(
        view=view,
        build=build,
        head=(cx + lean + pose.head[0], head_y),
        torso=(
            (cx + lean, shoulder_y + build.torso_r - 3.2),
            (cx + lean * 0.5, hip_y - 2),
            build.torso_r,
        ),
        shoulders=((cx - half + lean, shoulder_y), (cx + half + lean, shoulder_y)),
        hands=(
            hand(cx - half - 2 + lean, shoulder_y + build.arms, pose.hand_l),
            hand(cx + half + 2 + lean, shoulder_y + build.arms, pose.hand_r),
        ),
        hips=((cx - build.hips, hip_y), (cx + build.hips, hip_y)),
        feet=(foot(cx - build.hips, pose.foot_l), foot(cx + build.hips, pose.foot_r)),
        shoulder_y=shoulder_y,
        hip_y=hip_y,
        lean=lean,
        big_hand=pose.big_hand_r,
    )


# Animations: name -> (fps, loop, phases, frames). A frame is a Pose or a LYING marker.

AnimTable = dict[str, tuple[int, bool, list[int] | None, list]]


def animations(view: str, pose_name: str = "raise") -> AnimTable:
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
        "pose": (3, True, None, pose_frames(pose_name, view)),
    }


# Signature poses: the JoJo pose of each character, picked by name in its look file
# (`pose = "point"`). Each gives two frames per view; the second breathes a little.


def _breathe(pose: Pose) -> list[Pose]:
    return [pose, Pose(**{**pose.__dict__, "bob": pose.bob + 1})]


def pose_frames(name: str, view: str) -> list[Pose]:
    side, up = view == "right", view == "up"
    if name == "point":
        # Points straight at the opponent, the other hand at the cap's brim.
        if side:
            frame = Pose(lean=-1, hand_r=(12, -10), hand_l=(1, -20), foot_r=(3, 0), foot_l=(-3, 0))
        elif up:
            frame = Pose(hand_r=(-3, -16), hand_l=(3, -20))
        else:
            frame = Pose(hand_r=(-6, -9), hand_l=(2, -20), big_hand_r=True, foot_l=(-1, 0))
    elif name == "arch":
        # Arched far back, one arm raised high, the other hand at the face.
        if side:
            frame = Pose(
                lean=-3.5,
                head=(-2, -1),
                hand_r=(2, -25),
                hand_l=(4, -15),
                foot_r=(5, 0),
                foot_l=(-4, 0),
            )
        elif up:
            frame = Pose(lean=-2.5, hand_l=(3, -26), hand_r=(-3, -16), foot_l=(-2, 0))
        else:
            frame = Pose(
                lean=2.5,
                head=(2, -1),
                hand_r=(-3, -27),
                hand_l=(3, -17),
                foot_l=(-3, 0),
                foot_r=(3, 0),
            )
    elif name == "frame_face":
        # Both hands raised before the face, fingers spread, the body twisted.
        if side:
            frame = Pose(
                lean=-1,
                head=(-1, 0),
                hand_r=(6, -17),
                hand_l=(8, -14),
                foot_l=(3, 0),
                foot_r=(-2, 0),
            )
        elif up:
            frame = Pose(hand_r=(-5, -16), hand_l=(5, -16))
        else:
            frame = Pose(
                lean=1.5,
                head=(1, 0),
                hand_r=(-6, -15),
                hand_l=(8, -17),
                foot_l=(2, 0),
                foot_r=(1, 0),
            )
    elif name == "point_up":
        # The index finger pointing to the sky, the other fist on the hip.
        if side:
            frame = Pose(lean=-0.5, hand_r=(3, -29), hand_l=(-3, -6), foot_r=(3, 0), foot_l=(-2, 0))
        elif up:
            frame = Pose(hand_l=(1, -29), hand_r=(-3, -6))
        else:
            frame = Pose(lean=1, hand_r=(-1, -29), hand_l=(4, -6), foot_l=(-2, 0))
    elif name == "spread":
        # Arms thrown wide and high: a Stand showing itself off.
        if side:
            frame = Pose(lean=-1.5, head=(-1, -1), hand_r=(7, -17), hand_l=(-7, -15))
        else:
            frame = Pose(hand_r=(9, -17), hand_l=(-9, -17), head=(0, -1))
    elif name == "flex":
        # Fists up, ready: a guard that dares the opponent.
        if side:
            frame = Pose(lean=1, hand_r=(9, -16), hand_l=(6, -13), foot_r=(4, 0), foot_l=(-3, 0))
        else:
            frame = Pose(hand_r=(-7, -15), hand_l=(7, -15), bob=1)
    else:  # "raise": the default, one arm up
        if side:
            frame = Pose(
                lean=-1.5,
                head=(-1, -1),
                hand_r=(4, -19),
                hand_l=(-4, -4),
                foot_r=(4, 0),
                foot_l=(-3, 0),
            )
        else:
            frame = Pose(lean=1, head=(1, -1), hand_r=(-11, -19), hand_l=(3, -2), foot_l=(-2, 0))
    return _breathe(frame)


POSE_NAMES = ("raise", "point", "arch", "frame_face", "point_up", "spread", "flex")
