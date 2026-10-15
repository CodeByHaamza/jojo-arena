"""A very simple computer opponent, used for demos and smoke tests.

It plays with the same InputFrames a human produces, so it can never cheat.
"""

from __future__ import annotations

import random

from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.engine.actions import InputFrame, quantize_8


class SimpleBot:
    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.strafe = 0.0
        self.guard_f = 0

    def think(self, me: Fighter, foe: Fighter) -> InputFrame:
        rng = self.rng
        offset = foe.pos - me.pos
        distance = offset.length()
        presses: dict[str, int] = {}
        held: set[str] = set()
        if rng.random() < 0.02:
            self.strafe = rng.choice((-0.6, 0.0, 0.6))
        direction = offset.normalized()
        move = (direction.x - direction.y * self.strafe, direction.y + direction.x * self.strafe)
        threatened = foe.state == State.ATTACK and distance < 50
        if threatened and self.guard_f == 0 and rng.random() < 0.08:
            if rng.random() < 0.3:
                presses["dash"] = 1
                move = (-direction.y, direction.x)  # sidestep
            else:
                self.guard_f = rng.randint(15, 40)
        if self.guard_f:
            self.guard_f -= 1
            held.add("guard")
            move = (0.0, 0.0)
        elif distance < 34:
            move = (0.0, 0.0)
            roll = rng.random()
            if roll < 0.10:
                presses["light"] = 1
            elif roll < 0.13:
                presses["heavy"] = 1
        elif distance > 120 and rng.random() < 0.02:
            presses["special"] = 1
        return InputFrame(quantize_8(*move, 0.1), frozenset(held), presses)
