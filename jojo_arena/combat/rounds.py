"""Round flow around the simulation: intro, timer, KO or time up, score, sudden death.

A fight is won by the first to win `rounds_to_win` rounds. A draw (double KO, or the
same life percentage when time runs out) gives the round to both. If that makes both
reach the target, a sudden-death round follows: both at 1 HP, no timer, first clean
hit wins (blocked hits deal no damage at such low life).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from jojo_arena.combat.arena import Arena
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import State
from jojo_arena.combat.kit import Kit
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import Rules
from jojo_arena.engine.actions import NEUTRAL, InputFrame

ROUNDS_TO_WIN_CHOICES = (1, 3, 5)


class Phase(StrEnum):
    INTRO = "intro"
    FIGHT = "fight"
    ROUND_OVER = "round_over"
    MATCH_OVER = "match_over"


@dataclass(frozen=True)
class RoundResult:
    winners: tuple[int, ...]  # one index, or both for a draw
    reason: str  # "ko", "double_ko", "time"

    @property
    def draw(self) -> bool:
        return len(self.winners) == 2


class Rounds:
    def __init__(
        self,
        kits: tuple[Kit, Kit],
        rules: Rules,
        arena_factory: Callable[[], Arena],
        rounds_to_win: int,
    ) -> None:
        self.kits = kits
        self.rules = rules
        self.arena_factory = arena_factory
        self.rounds_to_win = rounds_to_win
        self.wins = [0, 0]
        self.round_number = 0
        self.sudden_death = False
        self.result: RoundResult | None = None
        self.winner: int | None = None  # of the whole fight
        self.match: Match
        self._start_round(carry=(0.0, 0.0))

    # Queries ----------------------------------------------------------------------------

    @property
    def timer_seconds(self) -> int | None:
        """Seconds shown on the HUD, rounded up; None in sudden death (no timer)."""
        if self.sudden_death:
            return None
        return -(-self.timer_f // 60)

    # Flow -------------------------------------------------------------------------------

    def _start_round(self, carry: tuple[float, float]) -> None:
        self.round_number += 1
        self.match = Match(self.kits, self.rules, self.arena_factory())
        for fighter, hh in zip(self.match.fighters, carry, strict=True):
            fighter.hh = hh
            if self.sudden_death:
                fighter.hp = self.rules.sudden_death_hp
        self.timer_f = self.rules.round_timer_f
        self.phase = Phase.INTRO
        self.phase_f = 0
        self.result = None

    def step(self, inputs: tuple[InputFrame, InputFrame]) -> list[Event]:
        self.phase_f += 1
        if self.phase == Phase.INTRO:
            # The world is drawn but nobody moves until "FIGHT!".
            if self.phase_f == 1:
                kind = "sudden_death" if self.sudden_death else "round_start"
                return [Event(kind, value=self.round_number)]
            if self.phase_f >= self.rules.round_intro_f:
                self.phase = Phase.FIGHT
                self.phase_f = 0
                return [Event("fight")]
            return []
        if self.phase == Phase.FIGHT:
            return self._step_fight(inputs)
        # After the round: the simulation keeps running (bodies fly, dust settles),
        # but players no longer control anything.
        events = self.match.step((NEUTRAL, NEUTRAL))
        if self.phase == Phase.ROUND_OVER and self.phase_f >= self.rules.round_outro_f:
            events += self._next_round()
        return events

    def _step_fight(self, inputs: tuple[InputFrame, InputFrame]) -> list[Event]:
        match = self.match
        cinematic = match.cinematic  # clash, super flash or stopped time: the clock waits
        events = match.step(inputs)
        if not self.sudden_death and not cinematic:
            self.timer_f = max(0, self.timer_f - 1)
        a, b = match.fighters
        if a.state == State.KO or b.state == State.KO:
            if a.state == State.KO and b.state == State.KO:
                result = RoundResult((0, 1), "double_ko")
            else:
                result = RoundResult((1 if a.state == State.KO else 0,), "ko")
            match.slowmo = self.rules.ko_slowmo_f
            return events + self._end_round(result)
        if self.timer_f == 0 and not self.sudden_death:
            ratio_a, ratio_b = a.hp / a.max_hp, b.hp / b.max_hp
            if ratio_a == ratio_b:
                result = RoundResult((0, 1), "time")
            else:
                result = RoundResult((0,) if ratio_a > ratio_b else (1,), "time")
            return events + [Event("time_up")] + self._end_round(result)
        return events

    def _end_round(self, result: RoundResult) -> list[Event]:
        self.result = result
        self.phase = Phase.ROUND_OVER
        self.phase_f = 0
        winner = None if result.draw else result.winners[0]
        return [Event("round_over", fighter=winner)]

    def _next_round(self) -> list[Event]:
        result = self.result
        for index in result.winners:
            self.wins[index] += 1
        target = self.rounds_to_win
        reached = [i for i in (0, 1) if self.wins[i] >= target]
        if self.sudden_death and not result.draw:
            reached = list(result.winners)
        if len(reached) == 1:
            self.winner = reached[0]
            self.phase = Phase.MATCH_OVER
            self.phase_f = 0
            return [Event("match_over", fighter=self.winner)]
        # Nobody won yet, or both reached the target together: play on.
        self.sudden_death = len(reached) == 2 or self.sudden_death
        carry = (0.0, 0.0)
        if self.rules.carry_heart_heat:
            carry = (self.match.fighters[0].hh, self.match.fighters[1].hh)
        self._start_round(carry)
        return []
