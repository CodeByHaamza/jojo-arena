"""Clash: two attacks meet at the same instant and both players mash to win the duel."""

from __future__ import annotations

from dataclasses import dataclass, field

from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Vec2

MASH_ACTIONS = ("light", "heavy", "special")


@dataclass
class Clash:
    pos: Vec2
    frames_left: int
    duration_f: int
    presses: list[int] = field(default_factory=lambda: [0, 0])

    def count(self, inputs: tuple[InputFrame, InputFrame]) -> None:
        for i, frame in enumerate(inputs):
            self.presses[i] += sum(frame.presses(a) for a in MASH_ACTIONS)

    @property
    def balance(self) -> float:
        """-1 = player 1 crushing, +1 = player 2 crushing, 0 = even. For the duel bar."""
        p1, p2 = self.presses
        return (p2 - p1) / (p1 + p2 + 4)

    @property
    def over(self) -> bool:
        return self.frames_left <= 0

    def winner(self) -> int | None:
        p1, p2 = self.presses
        if p1 == p2:
            return None
        return 0 if p1 > p2 else 1
