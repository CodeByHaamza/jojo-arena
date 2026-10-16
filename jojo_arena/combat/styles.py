"""Fighting styles: what the style button (the "Stand" key) does for a character.

Each style is a small reusable component chosen in the character's data file, so new
characters of an existing style need no new code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jojo_arena.combat.fighter import Fighter


class Style:
    """No style: the button does nothing."""

    event = "stance_switch"  # what the fight reports when the button starts something

    def __init__(self, params: dict) -> None:
        self.params = params

    def on_pressed(self, fighter: Fighter) -> bool:
        """React to the style button. Return True if it started an action."""
        return False

    def aura_active(self, fighter: Fighter) -> bool:
        return False


class StanceToggle(Style):
    """Switch between two movesets ("off" and "on" stances), with an aura while on.

    Example in a character file:
        style = { type = "stance_toggle", off = "base", on = "stand" }
    """

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        self.off = params.get("off", "base")
        self.on = params.get("on", "stand")
        # Optional remote control (long-range Stands): holding the key sends the Stand
        # off on its own, in this stance, within this range, at this speed (px/s).
        self.remote = params.get("remote")
        self.remote_range = params.get("remote_range", 140)
        self.remote_speed = params.get("remote_speed", 150)

    def on_pressed(self, fighter: Fighter) -> bool:
        if fighter.awakened:
            return False  # what it awakened into is what it stays
        if fighter.remote:
            fighter.leave_remote()  # the Stand comes back to its user
            return True
        target = self.off if fighter.stance == self.on else self.on
        fighter.begin_stance_switch(target)
        return True

    def aura_active(self, fighter: Fighter) -> bool:
        # Awakened into a third stance, the aura stays on: it is not going off again.
        if fighter.awakened:
            return True
        return fighter.stance == self.on or (self.remote and fighter.stance == self.remote)


class Vampire(StanceToggle):
    """A stance toggle fed by the blood gauge: the "on" stance (Vaporization Freezing)
    needs some blood to start, burns it while it lasts and ends when it runs dry. The
    blood fills by draining and heals the vampire when untouched (GDD "Vampire").

    Example in a character file:
        style = { type = "vampire", off = "base", on = "freeze" }
    """

    def on_pressed(self, fighter: Fighter) -> bool:
        if fighter.stance != self.on and fighter.blood < fighter.rules.vampire_stance_min_blood:
            return False
        return super().on_pressed(fighter)


class StanceCycle(Style):
    """The style button walks through a list of movesets, one after the other.

    Where `stance_toggle` flips between two, this one cycles: a character who can call
    in two different helpers, or a Pillar Man with several Modes, needs no new code.

    Example in a character file:
        style = { type = "stance_cycle", stances = ["base", "tattoo", "amato"] }
    """

    def __init__(self, params: dict) -> None:
        super().__init__(params)
        self.order: list[str] = list(params.get("stances", []))

    def on_pressed(self, fighter: Fighter) -> bool:
        if len(self.order) < 2:
            return False
        here = self.order.index(fighter.stance) if fighter.stance in self.order else 0
        fighter.begin_stance_switch(self.order[(here + 1) % len(self.order)])
        return True

    def aura_active(self, fighter: Fighter) -> bool:
        """Lit up whenever someone other than the fighter is out."""
        return bool(self.order) and fighter.stance != self.order[0]


class Hamon(Style):
    """Hold the button to breathe: the Hamon gauge fills, but the fighter stands still,
    open to hits. Moves with a `hamon_cost` spend it to strike harder (GDD "Hamon").

    Example in a character file:
        style = { type = "hamon" }
    """

    event = "breath"

    def on_pressed(self, fighter: Fighter) -> bool:
        fighter.begin_breath()
        return True

    def aura_active(self, fighter: Fighter) -> bool:
        return fighter.breathing


STYLES: dict[str, type[Style]] = {
    "none": Style,
    "stance_toggle": StanceToggle,
    "stance_cycle": StanceCycle,
    "hamon": Hamon,
    "vampire": Vampire,
}


def make_style(name: str, params: dict) -> Style:
    return STYLES[name](params)
