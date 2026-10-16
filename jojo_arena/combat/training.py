"""Training: an endless fight to practise, with refills, a dummy and a combo counter.

`Training` offers the same queries as `Rounds` (match, phase, wins, timer...) so the
fight screen and the HUD draw it the same way. There is no timer and no score: a KO
just puts both fighters back in place.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from jojo_arena.combat.arena import Arena
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.combat.kit import Kit
from jojo_arena.combat.match import Match
from jojo_arena.combat.rounds import Phase, RoundResult
from jojo_arena.combat.rules import Rules
from jojo_arena.engine.actions import NEUTRAL, InputFrame

# States in which a combo goes on: the defender cannot do anything yet.
COMBO_STATES = (State.HITSTUN, State.GUARD_BROKEN, State.KO)
SHOW_COMBO_F = 120  # a finished combo stays on screen this long


class Dummy(StrEnum):
    STAND = "stand"  # does nothing
    GUARD = "guard"  # holds guard all the time
    PLAYER = "player"  # played by the second player


def dummy_input(mode: Dummy) -> InputFrame | None:
    """What the dummy does this step; None when a player controls it."""
    if mode == Dummy.GUARD:
        return InputFrame(held=frozenset({"guard"}))
    if mode == Dummy.STAND:
        return NEUTRAL
    return None


@dataclass
class Combo:
    """Hits landed in a row on one defender, and the damage they did."""

    hits: int = 0
    damage: int = 0
    live: bool = False  # the defender is still stuck in it
    shown_f: int = 0  # frames left on screen once it is over

    def update(self, events: list[Event], defender: Fighter) -> None:
        for event in events:
            if event.kind != "hit" or event.fighter != defender.index:
                continue
            if not self.live:
                self.hits, self.damage, self.live = 0, 0, True
            self.hits += 1
            self.damage += round(event.value)
        if self.live and defender.state not in COMBO_STATES and not defender.frozen:
            self.live = False
            self.shown_f = SHOW_COMBO_F
        elif not self.live and self.shown_f > 0:
            self.shown_f -= 1

    @property
    def visible(self) -> bool:
        return self.hits > 0 and (self.live or self.shown_f > 0)


class Training:
    training = True
    rounds_to_win = 0
    sudden_death = False
    timer_seconds = None  # no clock
    winner = None

    def __init__(
        self, kits: tuple[Kit, Kit], rules: Rules, arena_factory: Callable[[], Arena]
    ) -> None:
        self.kits = kits
        self.rules = rules
        self.arena_factory = arena_factory
        self.wins = [0, 0]
        self.round_number = 0
        self.infinite_life = True
        self.infinite_hh = True
        # combos[i] = the combo fighter i is landing on the other one
        self.combos = [Combo(), Combo()]
        self.match: Match
        self.reset()

    def reset(self) -> None:
        """Both fighters back in place, full life, arena rebuilt."""
        self.round_number += 1
        self.match = Match(self.kits, self.rules, self.arena_factory())
        self.phase = Phase.FIGHT
        self.phase_f = 0
        self.result: RoundResult | None = None
        self._calm_f = [0, 0]
        self.combos = [Combo(), Combo()]
        self.apply_options()

    def apply_options(self) -> None:
        for fighter in self.match.fighters:
            fighter.min_hp = 1 if self.infinite_life else 0
            if self.infinite_hh:
                fighter.hh = self.rules.hh_max
                if fighter.kit.style == "hamon":
                    fighter.hamon = self.rules.hamon_max
                if fighter.kit.style == "vampire":
                    fighter.blood = self.rules.blood_max

    def step(self, inputs: tuple[InputFrame, InputFrame]) -> list[Event]:
        self.phase_f += 1
        if self.phase == Phase.ROUND_OVER:
            events = self.match.step((NEUTRAL, NEUTRAL))
            if self.phase_f >= self.rules.round_outro_f:
                self.reset()
            return events
        events = self.match.step(inputs)
        a, b = self.match.fighters
        self.combos[0].update(events, b)
        self.combos[1].update(events, a)
        self._refill()
        if a.state == State.KO or b.state == State.KO:
            winners = tuple(i for i, f in enumerate((a, b)) if f.state != State.KO) or (0, 1)
            self.result = RoundResult(winners, "ko" if len(winners) == 1 else "double_ko")
            self.phase = Phase.ROUND_OVER
            self.phase_f = 0
            self.match.slowmo = self.rules.ko_slowmo_f
        return events

    def _refill(self) -> None:
        self.apply_options()
        if not self.infinite_life:
            return
        for i, fighter in enumerate(self.match.fighters):
            busy = fighter.state in COMBO_STATES or fighter.state == State.BLOCKSTUN
            if busy or fighter.frozen or self.combos[1 - i].live:
                self._calm_f[i] = 0
                continue
            self._calm_f[i] += 1
            if self._calm_f[i] >= self.rules.training_refill_f and fighter.hp < fighter.max_hp:
                fighter.hp = fighter.max_hp
                fighter.resolve_announced = False
