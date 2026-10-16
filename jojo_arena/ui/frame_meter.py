"""Drawing the frame meter: one colored strip per fighter, newest frame on the right.

One pixel column is one frame of the fight, so reading the two strips side by side
shows the gap between two blows and whether a punish fits in it. The colors are the
ones the frame data line uses for startup, active and recovery frames.
"""

from __future__ import annotations

import pygame

from jojo_arena.combat.framemeter import Band, FrameMeter
from jojo_arena.engine import font
from jojo_arena.ui import text
from jojo_arena.ui.widgets import DIM, FAINT, OUTLINE, WHITE

COLORS = {
    Band.FREE: (40, 36, 54),
    Band.STARTUP: (240, 196, 72),
    Band.ACTIVE: (232, 72, 72),
    Band.RECOVERY: (84, 134, 232),
    Band.GUARD: (96, 196, 140),
    Band.BLOCKSTUN: (154, 150, 174),
    Band.HITSTUN: (196, 96, 208),
    Band.BUSY: (118, 106, 158),
    Band.FROZEN: (236, 236, 244),
}
PHASE_KEYS = (
    (Band.STARTUP, "FM_STARTUP"),
    (Band.ACTIVE, "FM_ACTIVE"),
    (Band.RECOVERY, "FM_RECOVERY"),
)
ROW_H = 6  # height of one fighter's strip
ROW_GAP = 2


def draw_legend(surface: pygame.Surface, x: int, y: int) -> int:
    """The names of the three phases, each in its own color; returns the right edge.

    It reads both the frame data line below it and the colors of the strips beside it.
    """
    cursor = x
    for index, (band, key) in enumerate(PHASE_KEYS):
        if index:
            cursor = font.draw(surface, "/", (cursor, y), FAINT).right + 2
        cursor = font.draw(surface, getattr(text, key), (cursor, y), COLORS[band]).right + 2
    cursor += 6
    cursor = font.draw(surface, text.FM_ON_HIT, (cursor, y), DIM).right + 2
    cursor = font.draw(surface, "/", (cursor, y), FAINT).right + 2
    return font.draw(surface, text.FM_ON_BLOCK, (cursor, y), DIM).right


class FrameMeterPanel:
    """Draws a `FrameMeter`: the two strips, and the advantage it last measured."""

    def __init__(self, labels: tuple[str, str], columns: int) -> None:
        self.labels = labels
        self.columns = columns

    @property
    def height(self) -> int:
        return 2 * ROW_H + ROW_GAP

    def draw(self, surface: pygame.Surface, meter: FrameMeter, x: int, y: int) -> None:
        """The two strips with their top-left corner at (x, y)."""
        bands = meter.bands[-self.columns :]
        for row in (0, 1):
            top = y + row * (ROW_H + ROW_GAP)
            surface.fill(OUTLINE, (x - 1, top - 1, self.columns + 2, ROW_H + 2))
            surface.fill(COLORS[Band.FREE], (x, top, self.columns, ROW_H))
            # The newest frame is on the right, so an empty meter fills up from there.
            start = x + self.columns - len(bands)
            for column, pair in enumerate(bands):
                surface.fill(COLORS[pair[row]], (start + column, top, 1, ROW_H))
            font.draw(surface, self.labels[row], (x - 4, top - 1), DIM, align="right")

    def draw_advantage(
        self, surface: pygame.Surface, meter: FrameMeter, right: int, y: int
    ) -> None:
        """Who acts first after the last blow, and by how many frames."""
        advantage = meter.advantage
        if advantage is None or not advantage.visible:
            return
        label = text.FM_ON_BLOCK if advantage.blocked else text.FM_ON_HIT
        sign = f"+{advantage.frames}" if advantage.frames > 0 else str(advantage.frames)
        line = f"{self.labels[advantage.attacker]} {label} {sign}"
        font.draw(surface, line, (right, y), WHITE, align="right")
