"""Training aid: what the game reads from the player, live, and the last inputs pressed.

If a key seems to do nothing, this shows at once whether the game even sees it.
"""

from __future__ import annotations

import pygame

from jojo_arena.engine import font
from jojo_arena.engine.actions import InputFrame
from jojo_arena.ui.widgets import DIM, GOLD, OUTLINE, WHITE

ACTIONS = ("light", "heavy", "special", "stand", "dash", "guard", "heart_heat", "pose")
HISTORY = 7
ARROWS = {
    (0, -1): "↑",
    (0, 1): "↓",
    (-1, 0): "←",
    (1, 0): "→",
}


def direction_label(move: tuple[float, float]) -> str:
    dx = (move[0] > 0.3) - (move[0] < -0.3)
    dy = (move[1] > 0.3) - (move[1] < -0.3)
    if dx and dy:
        return ARROWS[(0, dy)] + ARROWS[(dx, 0)]
    return ARROWS.get((dx, dy), "")


class InputDisplay:
    def __init__(self, labels: dict[str, str]) -> None:
        self.labels = labels  # action -> key label for this player ("J", "MAJ G"...)
        self.frame = InputFrame()
        self.history: list[tuple[str, int]] = []  # (what was pressed, how long ago)

    def update(self, frame: InputFrame) -> None:
        self.frame = frame
        self.history = [(label, age + 1) for label, age in self.history]
        pressed = [self.labels.get(a, a) for a in ACTIONS if frame.was_pressed(a)]
        if pressed:
            arrow = direction_label(frame.move)
            label = " + ".join(([arrow] if arrow else []) + pressed)
            self.history = [(label, 0), *self.history][:HISTORY]

    def draw(self, surface: pygame.Surface, x: int, y: int) -> None:
        """Live keys on one row at (x, y), the history going up above it."""
        cx = x
        arrow = direction_label(self.frame.move)
        cx += self._cap(surface, arrow or "-", cx, y, bool(arrow)) + 2
        for action in ACTIONS:
            held = self.frame.is_held(action) or self.frame.was_pressed(action)
            cx += self._cap(surface, self.labels.get(action, "?"), cx, y, held) + 2
        for i, (label, age) in enumerate(self.history):
            color = WHITE if age < 30 else DIM
            font.draw(surface, label, (x, y - 11 * (i + 1)), color)

    @staticmethod
    def _cap(surface: pygame.Surface, label: str, x: int, y: int, lit: bool) -> int:
        width = font.text_width(label) + 6
        surface.fill(OUTLINE, (x - 1, y - 1, width + 2, 13))
        surface.fill((120, 96, 40) if lit else (38, 34, 52), (x, y, width, 11))
        font.draw(surface, label, (x + 3, y + 1), GOLD if lit else DIM, outline=None)
        return width
