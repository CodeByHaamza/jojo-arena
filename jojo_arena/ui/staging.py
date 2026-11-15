"""The little scenes around a fight, played on the arena itself: both fighters walking in,
each striking its pose and saying its line before the first round; and the winner's moment
(its pose, its Stand, its line) before the summary.

View only. The entrance plays on a match that the fight scene throws away when it ends, so
the fight that follows starts exactly as it would have without it: replays do not know it
exists.
"""

from __future__ import annotations

import pygame

from jojo_arena.characters.lines import Exchange
from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.engine import font
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.sprites import shade
from jojo_arena.ui.widgets import draw_box

WALK_F = 50  # frames to walk in
WALK_PX = 64  # ...from this far behind where the round starts them
POSE_F = 120  # a pose held while its line is said
SILENT_POSE_F = 70  # ...and when the pair has nothing to say
GAP_F = 14  # a breath between two poses
TYPE_PER_F = 2  # letters typed each frame
LINE_W = 190  # px a line may take over its speaker before it wraps
WINNER_HOLD_F = 150  # frames the winner's typed line is left to be read
WINNER_SILENT_F = 150  # the winner's moment when it has nothing to say


def typed(line: str, frames: int) -> int:
    """Letters of `line` on screen after `frames` frames of typing."""
    return max(0, min(len(line), frames * TYPE_PER_F))


def draw_line_over(
    surface: pygame.Surface, line: str, shown: int, head: Vec2, color, width: int = LINE_W
) -> None:
    """A line in a small box centred over `head`, kept on screen; `shown` letters typed."""
    rows = font.wrap(line, width)
    box = pygame.Rect(0, 0, max(font.text_width(row) for row in rows) + 12, len(rows) * 10 + 7)
    box.midbottom = (round(head.x), round(head.y))
    box.clamp_ip(surface.get_rect().inflate(-8, -8))
    draw_box(surface, box)
    for i, row in enumerate(rows):
        if shown <= 0:
            break
        font.draw(surface, row[:shown], (box.centerx, box.y + 4 + i * 10), color, align="center")
        shown -= len(row) + 1  # the space the wrap ate


class Entrance:
    """Both walk in from behind their marks, then each one in turn strikes the pose picked
    and says its line to the other (together and silent when the games gave them none)."""

    def __init__(self, fighters, views, fighter_ids, exchange: Exchange | None) -> None:
        self.fighters: list[Fighter] = list(fighters)
        self.views = list(views)
        self.marks = [fighter.pos.copy() for fighter in self.fighters]
        lines = exchange.intro if exchange is not None else ()
        # A beat: who poses (None: both) and what is said meanwhile.
        self.beats: list[tuple[int | None, str]] = [
            (fighter_ids.index(who), line) for who, line in lines
        ] or [(None, "")]
        self.frame = 0
        self._stage()

    def _beat_f(self, line: str) -> int:
        return (POSE_F if line else SILENT_POSE_F) + GAP_F

    @property
    def length(self) -> int:
        return WALK_F + sum(self._beat_f(line) for _, line in self.beats)

    @property
    def done(self) -> bool:
        return self.frame >= self.length

    def beat(self) -> tuple[int | None, str, int] | None:
        """(who poses, the line, frames into the beat) right now; None while walking in or
        between two poses."""
        at = self.frame - WALK_F
        if at < 0:
            return None
        for who, line in self.beats:
            span = self._beat_f(line)
            if at < span:
                return (who, line, at) if at < span - GAP_F else None
            at -= span
        return None

    def update(self) -> None:
        self.frame += 1
        self._stage()

    def _stage(self) -> None:
        """Put every fighter where this frame of the entrance wants it."""
        walk = min(1.0, self.frame / WALK_F)
        beat = self.beat()
        for side, (fighter, view, mark) in enumerate(
            zip(self.fighters, self.views, self.marks, strict=True)
        ):
            other = self.marks[1 - side]
            toward = (other - mark).normalized()
            fighter.facing = toward
            fighter.pos = mark - toward * (WALK_PX * (1 - walk))
            state = State.WALK if walk < 1 else State.IDLE
            if fighter.state != state:
                fighter.set_state(state)
            fighter.state_f += 1  # the match is not stepped: the animation clock is ours
            view.celebrating = beat is not None and beat[0] in (None, side)

    def draw(self, surface: pygame.Surface, fighter_defs) -> None:
        """The line being said, over its speaker and in its speaker's color."""
        beat = self.beat()
        if beat is None or beat[0] is None or not beat[1]:
            return
        side, line, at = beat
        head = self.fighters[side].pos + Vec2(0, -self.views[side].height - 12)
        color = shade(fighter_defs[side].color, 70)
        draw_line_over(surface, line, typed(line, at + 1), head, color)

    def finish(self) -> None:
        for view in self.views:
            view.celebrating = False
