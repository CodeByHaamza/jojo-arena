"""The training dummy: what it does on its own while the player practises.

Beyond standing still or holding guard, the dummy can repeat one chosen action -- a
move picked from its own kit, a dash, a pose -- with a delay in frames between each
repetition. The delay is counted from the moment the dummy is free to act again, so a
delay of zero is a frame-perfect answer (the reversal fighting game players practise
against) and a long delay leaves room to walk in and press first.

It can also record what the second player does and loop it, for a sequence no single
action covers.

Like `CpuPlayer`, it only ever produces `InputFrame`s: it can never do something a pad
could not do, so what is practised against is what a human could really play.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from jojo_arena.combat.ai import move_reach
from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.combat.kit import ATTACK_SLOTS, Kit, MoveDef
from jojo_arena.engine.actions import NEUTRAL, InputFrame
from jojo_arena.engine.geometry import Vec2

# States from which the dummy can start something: on its feet, or holding guard.
FREE_STATES = (State.IDLE, State.WALK, State.GUARD)
SUPER_SLOTS = ("hha", "gha")
# Styles whose button swaps the moveset (so the dummy can reach the other stance).
TOGGLE_STYLES = ("stance_toggle", "vampire")
SWITCH_GIVE_UP_F = 90  # trying to swap stance for this long: act with what is at hand
# Delays offered in the training menu, in frames (0 = as soon as it can).
DELAYS = (0, 2, 4, 6, 8, 12, 16, 20, 30, 45, 60, 90, 120, 180, 300)
APPROACH_MARGIN = 0.8  # it walks in until this share of the move's reach


class Dummy(StrEnum):
    STAND = "stand"  # does nothing
    GUARD = "guard"  # holds guard all the time
    PLAYER = "player"  # played by the second player
    ACTION = "action"  # repeats the chosen action, every `delay_f` frames
    RECORD = "record"  # played by the second player, and recorded
    PLAYBACK = "playback"  # the recording, looped


class After(StrEnum):
    """What the dummy does while it waits for the next repetition."""

    IDLE = "idle"
    GUARD = "guard"


def dummy_input(mode: Dummy) -> InputFrame | None:
    """What the dummy does this step; None when a player controls it."""
    if mode == Dummy.GUARD:
        return InputFrame(held=frozenset({"guard"}))
    if mode == Dummy.STAND:
        return NEUTRAL
    return None


@dataclass(frozen=True)
class DummyAction:
    """One thing the dummy can be told to repeat."""

    key: str  # "stand/heavy", "hha", "dash"...: stable, and kept in the settings
    press: str = ""  # the button pressed ("heavy", "heart_heat", "dash"...)
    stance: str = ""  # the stance the move lives in ("" = whichever is out)
    direction: bool = False  # hold a direction: the _alt variant of a button, the GHA
    label: str = ""  # the move's name, already in the game's language
    text_key: str = ""  # a name in ui/text.py, when the label is not a move's
    move: MoveDef | None = None  # the move it starts, for its frame data

    @property
    def chainable(self) -> bool:
        return self.move is not None and bool(self.move.chain)


NO_ACTION = DummyAction("none", text_key="DUMMY_ACT_NONE")


def dummy_actions(kit: Kit) -> list[DummyAction]:
    """Everything a button can start for this kit, in the order of the training menu.

    The rest of a chain (`light2`) and a counter's answer are left out: they are not on a
    button of their own, they follow from the blow before.
    """
    actions = [NO_ACTION]
    named = len(kit.stances) > 1  # several stances: say which one each move needs
    for stance_name, stance in kit.stances.items():
        prefix = f"{kit.stance_labels.get(stance_name, stance_name)} : " if named else ""
        for slot, move in stance.moves.items():
            if slot.removesuffix("_alt") not in ATTACK_SLOTS:
                continue
            actions.append(
                DummyAction(
                    key=f"{stance_name}/{slot}",
                    press=slot.removesuffix("_alt"),
                    stance=stance_name,
                    direction=slot.endswith("_alt"),
                    label=prefix + (move.label or slot.upper()),
                    move=move,
                )
            )
    for slot in SUPER_SLOTS:
        move = kit.shared_moves.get(slot)
        if move is not None:
            actions.append(
                DummyAction(
                    key=slot,
                    press="heart_heat",
                    direction=slot == "gha",  # the GHA is the Heart Heat key plus a direction
                    label=move.label or slot.upper(),
                    move=move,
                )
            )
    actions.append(DummyAction("dash", press="dash", text_key="DUMMY_ACT_DASH"))
    actions.append(DummyAction("pose", press="pose", text_key="DUMMY_ACT_POSE"))
    return actions


@dataclass
class DummyPlan:
    """The dummy's settings, as the training pause menu leaves them."""

    mode: Dummy = Dummy.STAND
    action: int = 0  # index in the kit's catalog
    delay_f: int = 60  # frames waited once it is free to act again
    chain: bool = True  # press the same button again to follow a chain
    approach: bool = False  # walk in when the move cannot reach
    after: After = After.IDLE  # what it does while it waits


class DummyPlayer:
    """Drives the training dummy, one `InputFrame` at a time."""

    def __init__(self, actions: Sequence[DummyAction]) -> None:
        self.actions = list(actions) or [NO_ACTION]
        self.plan = DummyPlan()
        self.recording: list[InputFrame] = []
        self.recorded = False  # there is a recording to play back
        self.played: list[MoveDef] = []  # the moves it has started, for the tests and the HUD
        self._free_f = 0  # frames it has been free to act
        self._switch_f = 0  # frames spent trying to swap stance
        self._play_at = 0  # where the playback is in the recording
        self._serial = -1

    # Settings ---------------------------------------------------------------------------

    @property
    def action(self) -> DummyAction:
        return self.actions[min(self.plan.action, len(self.actions) - 1)]

    def select(self, key: str) -> None:
        """Choose an action by its key; unknown keys leave the choice alone."""
        for index, action in enumerate(self.actions):
            if action.key == key:
                self.plan.action = index
                return

    def to_json(self) -> dict:
        """The settings as they are, by the action's key: a number would not survive a
        change of character or of roster."""
        plan = self.plan
        return {
            "mode": str(plan.mode),
            "action": self.action.key,
            "delay_f": plan.delay_f,
            "chain": plan.chain,
            "approach": plan.approach,
            "after": str(plan.after),
        }

    def load_json(self, data: dict) -> None:
        """Put back what was saved, ignoring anything that no longer makes sense."""
        if not isinstance(data, dict):
            return
        plan = self.plan
        if data.get("mode") in tuple(Dummy):
            plan.mode = Dummy(data["mode"])
        if data.get("after") in tuple(After):
            plan.after = After(data["after"])
        if isinstance(data.get("delay_f"), int) and data["delay_f"] in DELAYS:
            plan.delay_f = data["delay_f"]
        plan.chain = bool(data.get("chain", plan.chain))
        plan.approach = bool(data.get("approach", plan.approach))
        if isinstance(data.get("action"), str):
            self.select(data["action"])

    def retarget(self, actions: Sequence[DummyAction]) -> None:
        """A new dummy character: its own catalog, keeping the action if it still exists."""
        key = self.action.key
        self.actions = list(actions) or [NO_ACTION]
        self.plan.action = 0
        self.select(key)
        self.reset()

    def reset(self) -> None:
        """Back to the start of the loop (both fighters were put back in place)."""
        self._free_f = 0
        self._switch_f = 0
        self._play_at = 0
        self.played.clear()

    @property
    def recording_now(self) -> bool:
        return self.plan.mode == Dummy.RECORD

    # Recording --------------------------------------------------------------------------

    def start_recording(self) -> None:
        self.recording = []
        self.recorded = False
        self.plan.mode = Dummy.RECORD

    def record(self, frame: InputFrame) -> None:
        """Keep what the second player just played, to loop it afterwards."""
        self.recording.append(frame)

    def stop_recording(self) -> None:
        """Play the recording from now on, or stand still if nothing was recorded."""
        self.recorded = bool(self.recording)
        self.plan.mode = Dummy.PLAYBACK if self.recorded else Dummy.STAND
        self.reset()

    # Playing ----------------------------------------------------------------------------

    def think(self, me: Fighter, foe: Fighter) -> InputFrame | None:
        """The dummy's input for this step; None when the second player holds the pad."""
        self._remember(me)
        mode = self.plan.mode
        if mode in (Dummy.PLAYER, Dummy.RECORD):
            return None
        if mode in (Dummy.STAND, Dummy.GUARD):
            return dummy_input(mode)
        if mode == Dummy.PLAYBACK:
            return self._play_back()
        return self._act(me, foe)

    def _remember(self, me: Fighter) -> None:
        """Keep every move it starts: the frame data panel reads the last one."""
        attack = me.attack
        if attack is not None and attack.serial != self._serial:
            self._serial = attack.serial
            self.played.append(attack.move)

    def _waiting(self) -> InputFrame:
        """Between two repetitions: nothing, or guard, so blows can be practised on it."""
        if self.plan.after == After.GUARD:
            return InputFrame(held=frozenset({"guard"}))
        return NEUTRAL

    def _act(self, me: Fighter, foe: Fighter) -> InputFrame:
        action = self.action
        if not action.press:
            return self._waiting()
        if me.frozen:
            return self._waiting()  # caught in stopped time: it cannot even hold guard
        # A chain goes on by pressing the same button again while the blow connects.
        attack = me.attack
        if self.plan.chain and attack is not None and attack.slot and attack.move.chain:
            if attack.connected:
                return InputFrame(press_counts={attack.slot: 1})
            return NEUTRAL
        if me.state not in FREE_STATES:
            self._free_f = 0
            return self._waiting()
        if self._needs_switch(me, action):
            self._switch_f += 1
            self._free_f = 0
            return InputFrame(press_counts={"stand": 1})
        self._switch_f = 0
        self._free_f += 1
        if self._free_f <= self.plan.delay_f:
            return self._approach(me, foe)
        self._free_f = 0
        aim = Vec2()
        if action.direction:
            offset = foe.pos - me.pos
            aim = offset.normalized() if offset.length_sq() else me.facing
        return InputFrame((aim.x, aim.y), self._waiting().held, {action.press: 1})

    def _needs_switch(self, me: Fighter, action: DummyAction) -> bool:
        """The chosen move lives in the other stance: the style button swaps to it."""
        if not action.stance or me.stance == action.stance:
            return False
        if me.kit.style not in TOGGLE_STYLES or self._switch_f >= SWITCH_GIVE_UP_F:
            return False
        return action.stance in me.kit.stances

    def _approach(self, me: Fighter, foe: Fighter) -> InputFrame:
        """Walk in while waiting, when the move could not reach from here."""
        move = self.action.move
        if not self.plan.approach or move is None:
            return self._waiting()
        reach = move_reach(move)
        offset = foe.pos - me.pos
        if reach <= 0 or offset.length() <= reach * APPROACH_MARGIN:
            return self._waiting()
        toward = offset.normalized()
        return InputFrame((toward.x, toward.y))  # no guard: it would stand still instead

    def _play_back(self) -> InputFrame:
        """The recording, then the delay, then the recording again."""
        if not self.recording:
            return NEUTRAL
        if self._play_at < len(self.recording):
            frame = self.recording[self._play_at]
            self._play_at += 1
            return frame
        self._free_f += 1
        if self._free_f > self.plan.delay_f:
            self._free_f = 0
            self._play_at = 0
        return self._waiting()
