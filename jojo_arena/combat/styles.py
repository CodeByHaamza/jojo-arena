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

    def on_pressed(self, fighter: Fighter) -> bool:
        target = self.off if fighter.stance == self.on else self.on
        fighter.begin_stance_switch(target)
        return True

    def aura_active(self, fighter: Fighter) -> bool:
        return fighter.stance == self.on


STYLES: dict[str, type[Style]] = {"none": Style, "stance_toggle": StanceToggle}


def make_style(name: str, params: dict) -> Style:
    return STYLES[name](params)
