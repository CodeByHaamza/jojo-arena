"""A cutscene in progress: the fight holds, the view plays it, then its outcome lands."""

from __future__ import annotations

from dataclasses import dataclass

from jojo_arena.combat.kit import MoveDef


@dataclass
class Cutscene:
    name: str  # which cutscene the view plays (the move's `cinematic`)
    user: int
    target: int
    frames_left: int
    total_f: int
    move: MoveDef | None  # None for a cutscene that is not a blow (an awakening)
    serial: int  # the attack that started it

    @property
    def frame(self) -> int:
        """Frames since the cutscene started."""
        return self.total_f - self.frames_left
