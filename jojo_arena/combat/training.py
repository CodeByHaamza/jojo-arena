"""Training: an endless fight to practise, with refills, a dummy and a combo counter.

`Training` offers the same queries as `Rounds` (match, phase, wins, timer...) so the
fight screen and the HUD draw it the same way. There is no timer and no score: a KO
just puts both fighters back in place.
"""

from __future__ import annotations

from collections.abc import Callable

from jojo_arena.combat.arena import Arena
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import State
from jojo_arena.combat.kit import Kit
from jojo_arena.combat.match import Match
from jojo_arena.combat.rounds import Phase, RoundResult
from jojo_arena.combat.rules import Rules
from jojo_arena.combat.stats import COMBO_STATES, Combo
from jojo_arena.engine.actions import NEUTRAL, InputFrame


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
        self.time_stop_mult = 1.0  # how long ZA WARUDO lasts here
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
        self.match.time_stop_mult = self.time_stop_mult
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
