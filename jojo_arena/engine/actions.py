"""Device-independent input snapshot, consumed by game logic once per fixed step.

Pure Python (no pygame) so the simulation and its tests never touch real devices.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field

# Action names the engine treats as directions. Everything else is game-defined.
MOVE_ACTIONS = ("up", "down", "left", "right")

_DIAG = math.sqrt(0.5)
# Eight unit directions, counter-clockwise from +x, in screen coordinates (y down).
EIGHT_DIRECTIONS = (
    (1.0, 0.0),
    (_DIAG, _DIAG),
    (0.0, 1.0),
    (-_DIAG, _DIAG),
    (-1.0, 0.0),
    (-_DIAG, -_DIAG),
    (0.0, -1.0),
    (_DIAG, -_DIAG),
)


@dataclass(frozen=True, slots=True)
class InputFrame:
    """What one player is doing during one logic step."""

    move: tuple[float, float] = (0.0, 0.0)
    held: frozenset[str] = frozenset()
    # How many times each action was pressed since the previous step (for mashing).
    press_counts: Mapping[str, int] = field(default_factory=dict)

    def is_held(self, action: str) -> bool:
        return action in self.held

    def was_pressed(self, action: str) -> bool:
        return self.press_counts.get(action, 0) > 0

    def presses(self, action: str) -> int:
        return self.press_counts.get(action, 0)


NEUTRAL = InputFrame()


def direction_from_flags(up: bool, down: bool, left: bool, right: bool) -> tuple[float, float]:
    """Unit vector (or zero) from four digital directions; opposite keys cancel."""
    dx = int(right) - int(left)
    dy = int(down) - int(up)
    if dx and dy:
        return dx * _DIAG, dy * _DIAG
    return float(dx), float(dy)


def quantize_8(x: float, y: float, deadzone: float) -> tuple[float, float]:
    """Snap an analog stick to one of 8 directions so pads and keyboards are on par."""
    if math.hypot(x, y) < deadzone:
        return 0.0, 0.0
    sector = round(math.atan2(y, x) / (math.pi / 4)) % 8
    return EIGHT_DIRECTIONS[sector]


def merge_frames(*frames: InputFrame) -> InputFrame:
    """Combine several sources into one (e.g. menus accept any keyboard or pad)."""
    held: set[str] = set()
    counts: dict[str, int] = {}
    move = (0.0, 0.0)
    for frame in frames:
        held |= frame.held
        for action, count in frame.press_counts.items():
            counts[action] = counts.get(action, 0) + count
        if move == (0.0, 0.0):
            move = frame.move
    return InputFrame(move, frozenset(held), counts)
