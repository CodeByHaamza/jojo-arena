"""What a fight feels like in the hands: rumble patterns, and the pad's light bar.

Like the rest of `ui/`, this only *reads* the fight: the simulation reports what
happened and this turns it into motors. Each event names the fighter it concerns, so
the player who takes the blow feels the weight of it (low motor) and the one who lands
it feels the snap (high motor).
"""

from __future__ import annotations

from jojo_arena.combat.events import Event
from jojo_arena.engine.haptics import Haptics, Shake
from jojo_arena.engine.input import InputManager

# What the fighter the event is about feels. "hit" and "block" also give the attacker
# a shorter, sharper one (ATTACKER below): a blow landing is felt from both sides.
FELT: dict[str, Shake] = {
    "hit": Shake(low=0.55, high=0.25, ms=110),
    "block": Shake(low=0.18, high=0.10, ms=70),
    "guard_break": Shake(low=0.80, high=0.45, ms=240),
    "wall_bounce": Shake(low=0.70, high=0.20, ms=160),
    "ko": Shake(low=1.00, high=0.60, ms=500),
    "counter": Shake(low=0.65, high=0.55, ms=200),
    "freeze": Shake(low=0.30, high=0.70, ms=300),
    "cage": Shake(low=0.45, high=0.35, ms=260),
    "possessed": Shake(low=0.25, high=0.45, ms=400),
    "drain": Shake(low=0.35, high=0.15, ms=180),
    "sunburn": Shake(low=0.20, high=0.30, ms=200),
    "stylish": Shake(low=0.10, high=0.35, ms=120),
    "resolve": Shake(low=0.50, high=0.30, ms=350),
}
# The same events, felt by the one who caused them: shorter and sharper.
ATTACKER: dict[str, Shake] = {
    "hit": Shake(low=0.15, high=0.30, ms=60),
    "block": Shake(low=0.05, high=0.14, ms=45),
    "guard_break": Shake(low=0.30, high=0.40, ms=120),
    "counter": Shake(low=0.40, high=0.50, ms=140),
}
# Events that belong to the fighter who *does* them, not to a victim.
OWN: dict[str, Shake] = {
    "hha": Shake(low=0.45, high=0.55, ms=260),
    "gha": Shake(low=0.70, high=0.70, ms=420),
    "flash_cancel": Shake(low=0.20, high=0.40, ms=90),
    "clash_start": Shake(low=0.40, high=0.40, ms=200),
    "clash_win": Shake(low=0.55, high=0.30, ms=220),
    "throw": Shake(low=0.25, high=0.20, ms=90),
    "hamon": Shake(low=0.12, high=0.38, ms=140),
    "reflect": Shake(low=0.30, high=0.40, ms=120),
}
# Both pads at once: the world itself stops or starts again.
BOTH: dict[str, Shake] = {
    "time_stop": Shake(low=0.60, high=0.25, ms=400),
    "time_resume": Shake(low=0.45, high=0.55, ms=200),
    "dawn": Shake(low=0.15, high=0.25, ms=600),
    "cutscene_start": Shake(low=0.35, high=0.20, ms=200),
}


class FightRumble:
    """Turns the events of a fight into rumble on the two players' pads."""

    def __init__(
        self,
        inputs: InputManager,
        slots: tuple[int | None, int | None],
        enabled: bool = True,
        strength: float = 1.0,
    ) -> None:
        self.haptics = Haptics(inputs, enabled)
        self.haptics.strength = strength
        self.slots = slots  # the pad slot of each player, None for a keyboard

    @property
    def enabled(self) -> bool:
        return self.haptics.enabled

    def light_up(self, colors: tuple[tuple[int, int, int], tuple[int, int, int]]) -> None:
        """The light bar of each pad takes the colour of the fighter it plays."""
        for player, color in enumerate(colors):
            self.haptics.light(self.slots[player], color)

    def on_events(self, events: list[Event]) -> None:
        for event in events:
            who = event.fighter
            if event.kind in BOTH:
                for slot in self.slots:
                    self.haptics.shake(slot, BOTH[event.kind])
                continue
            if who is None:
                continue
            if event.kind in FELT:
                self.haptics.shake(self.slots[who], FELT[event.kind])
                if event.kind in ATTACKER:
                    self.haptics.shake(self.slots[1 - who], ATTACKER[event.kind])
            elif event.kind in OWN:
                self.haptics.shake(self.slots[who], OWN[event.kind])

    def stop(self) -> None:
        self.haptics.stop()


def pad_slots(players) -> tuple[int | None, int | None]:
    """The pad slot of each player, None for whoever plays on the keyboard."""
    slots = [p.slot if p.device == "gamepad" else None for p in players]
    return slots[0], slots[1]
