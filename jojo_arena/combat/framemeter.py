"""Frame meter: what each fighter was doing, frame by frame, and who acts first.

Fighting game players read a frame meter to see where a move's startup, active and
recovery frames went, how wide the gap between two blows is, and whether a punish fits
inside it. This one *watches* the fight rather than reading the move data, so hitstop,
armor, cancels, counters and cutscenes all show up exactly as they happened.

The advantage it reports is measured the same way: after a blow lands or is blocked, it
waits for both sides to be able to act again and gives the difference. A `+6` means the
attacker is free six frames before the defender.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import StrEnum

from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import ACTIONABLE, Attack, Fighter, State
from jojo_arena.combat.match import Match

WIDTH = 150  # frames kept, 2.5 seconds at 60 Hz
SHOW_ADVANTAGE_F = 180  # how long a measured advantage stays on screen


class Band(StrEnum):
    """What one fighter was doing during one frame."""

    FREE = "free"  # on its feet, free to start anything
    STARTUP = "startup"  # a move is coming out, it cannot hit yet
    ACTIVE = "active"  # the hitbox is out
    RECOVERY = "recovery"  # the move is over, it is still stuck in it
    GUARD = "guard"  # holding guard, free to act out of it
    BLOCKSTUN = "blockstun"  # stuck after blocking
    HITSTUN = "hitstun"  # stuck after being hit (or broken, or K.O.)
    BUSY = "busy"  # dash, pose, stance switch, breathing, clash
    FROZEN = "frozen"  # impact freeze, stopped time, cutscene: nothing moves


# Bands from which a fighter can start its next action.
ACTIONABLE_BANDS = (Band.FREE, Band.GUARD)
# Bands a fighter is stuck in: it has to see them through before it can act.
STUCK_BANDS = (
    Band.STARTUP,
    Band.ACTIVE,
    Band.RECOVERY,
    Band.BLOCKSTUN,
    Band.HITSTUN,
    Band.BUSY,
)
BUSY_STATES = (State.DASH, State.POSE, State.SWITCH, State.BREATHE, State.CLASH)
STUCK_STATES = (State.HITSTUN, State.GUARD_BROKEN, State.KO)
PHASE_BANDS = (Band.STARTUP, Band.ACTIVE, Band.RECOVERY)


def _phase(attack: Attack) -> int:
    """The phase the move was in *during* the step that just ran.

    The fight advances its timers at the end of a step, so by the time the meter looks,
    `attack.frame` already points at the next frame.
    """
    frame = max(0, attack.frame - 1)
    move = attack.move
    if frame < move.startup_f:
        return 0
    if frame < move.startup_f + move.active_f:
        return 1
    return 2


def band_of(fighter: Fighter, previous: Band | None = None) -> Band:
    """The band one fighter was in during the step that just ran.

    `previous` is its band on the step before: when a state ended during this very step
    (`state_f` is back to zero), the frame belonged to the state that ended, not to the
    one that follows, so the meter keeps showing it.
    """
    if fighter.frozen:
        return Band.FROZEN
    if fighter.state == State.ATTACK and fighter.attack is not None:
        return PHASE_BANDS[_phase(fighter.attack)]
    free = fighter.state in ACTIONABLE or fighter.state == State.GUARD
    if free and fighter.state_f == 0 and previous in STUCK_BANDS:
        # It got free during this very step: the frame belonged to the move, the dash or
        # the stun that ended, and it can only act on the next one.
        return previous
    if fighter.state in STUCK_STATES:
        return Band.HITSTUN
    if fighter.state == State.BLOCKSTUN:
        return Band.BLOCKSTUN
    if fighter.state == State.GUARD:
        return Band.GUARD
    if fighter.state in BUSY_STATES:
        return Band.BUSY
    return Band.FREE


@dataclass
class Advantage:
    """The frames of advantage the last exchange really gave, as measured."""

    frames: int = 0
    blocked: bool = False  # the blow was blocked, not landed
    attacker: int = 0
    shown_f: int = 0  # frames left on screen

    @property
    def visible(self) -> bool:
        return self.shown_f > 0


class FrameMeter:
    """A rolling strip of bands for both fighters, plus the advantage it measures."""

    def __init__(self, width: int = WIDTH) -> None:
        self.width = width
        self.columns: deque[tuple[Band, Band]] = deque(maxlen=width)
        self.advantage: Advantage | None = None
        self._frame = 0
        self._attacker: int | None = None  # the exchange being measured
        self._blocked = False
        self._free: list[int | None] = [None, None]
        self._timers: tuple | None = None

    def reset(self) -> None:
        self.columns.clear()
        self.advantage = None
        self._frame = 0
        self._attacker = None
        self._free = [None, None]
        self._timers = None

    def update(self, match: Match, events: list[Event]) -> None:
        """One column per logic step, whether the fight moved or held still."""
        self._frame += 1
        # Impact freeze, stopped time, a cutscene, slow motion: no timer moved at all.
        timers = tuple(
            (f.state_f, f.attack.frame if f.attack is not None else -1) for f in match.fighters
        )
        held = timers == self._timers
        self._timers = timers
        before = self.columns[-1] if self.columns else (None, None)
        if held:
            bands = (Band.FROZEN, Band.FROZEN)
        else:
            bands = tuple(band_of(f, before[i]) for i, f in enumerate(match.fighters))
        self.columns.append(bands)  # type: ignore[arg-type]
        if self.advantage is not None and self.advantage.shown_f > 0:
            self.advantage.shown_f -= 1
        self._watch(events)
        self._measure(bands)

    @property
    def bands(self) -> list[tuple[Band, Band]]:
        return list(self.columns)

    def row(self, index: int) -> list[Band]:
        """The strip of one fighter, oldest frame first."""
        return [column[index] for column in self.columns]

    # Measuring ---------------------------------------------------------------------------

    def _watch(self, events: list[Event]) -> None:
        """A blow landed or was blocked: start measuring who recovers first."""
        for event in events:
            if event.kind not in ("hit", "block", "guard_break") or event.fighter is None:
                continue
            self._attacker = 1 - event.fighter
            self._blocked = event.kind != "hit"
            self._free = [None, None]

    def _measure(self, bands: tuple[Band, Band]) -> None:
        if self._attacker is None:
            return
        attacker = self._attacker
        defender = 1 - attacker
        if bands[attacker] == Band.HITSTUN and self._free[attacker] is None:
            self._attacker = None  # traded blows: there is no advantage to read
            return
        for index in (attacker, defender):
            if self._free[index] is None and bands[index] in ACTIONABLE_BANDS:
                self._free[index] = self._frame
        if None in self._free:
            return
        self.advantage = Advantage(
            frames=self._free[defender] - self._free[attacker],  # type: ignore[operator]
            blocked=self._blocked,
            attacker=attacker,
            shown_f=SHOW_ADVANTAGE_F,
        )
        self._attacker = None
