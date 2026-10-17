"""What the fighters did over a whole fight, counted for the screen at the end.

Generic: it reads events and fighter states, and knows nothing about who the fighters
are. `Combo` lives here too - the training room shows a live counter with it, the end of
a fight shows the best one of the whole match.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import Fighter, State

# States in which a combo goes on: the defender cannot do anything yet.
COMBO_STATES = (State.HITSTUN, State.GUARD_BROKEN, State.KO)
SHOW_COMBO_F = 120  # a finished combo stays on screen this long


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


@dataclass
class Side:
    """One fighter's fight, in numbers."""

    damage: int = 0  # dealt
    hits: int = 0  # blows that landed
    biggest_hit: int = 0
    best_combo_hits: int = 0
    best_combo_damage: int = 0
    supers: int = 0  # Heart Heat and Great Heat attacks used
    blocks: int = 0  # blows guarded
    taken: int = 0  # damage taken


@dataclass
class FightStats:
    """Fed every step of a fight; read once it is over."""

    sides: tuple[Side, Side] = field(default_factory=lambda: (Side(), Side()))
    frames: int = 0
    combos: tuple[Combo, Combo] = field(default_factory=lambda: (Combo(), Combo()))

    def update(self, events: list[Event], fighters: tuple[Fighter, Fighter]) -> None:
        """One step of the fight: count what happened, and follow the live combos."""
        self.frames += 1
        for event in events:
            if event.fighter is None:
                continue
            if event.kind == "hit":
                # `fighter` is the one who was hit: the damage belongs to the other one.
                damage = round(event.value or 0)
                defender = self.sides[event.fighter]
                attacker = self.sides[1 - event.fighter]
                attacker.damage += damage
                attacker.hits += 1
                attacker.biggest_hit = max(attacker.biggest_hit, damage)
                defender.taken += damage
            elif event.kind == "block":
                self.sides[event.fighter].blocks += 1
            elif event.kind in ("hha", "gha"):
                self.sides[event.fighter].supers += 1
        for defender in fighters:
            # The combo on this defender is the attacker's: keep the best one.
            combo = self.combos[defender.index]
            combo.update(events, defender)
            attacker = self.sides[1 - defender.index]
            if combo.hits > attacker.best_combo_hits or (
                combo.hits == attacker.best_combo_hits and combo.damage > attacker.best_combo_damage
            ):
                attacker.best_combo_hits = combo.hits
                attacker.best_combo_damage = combo.damage

    @property
    def seconds(self) -> int:
        return self.frames // 60
