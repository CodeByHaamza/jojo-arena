"""Status effects: what a blow leaves behind once it has landed.

Three of them, because three things in this fight keep working after the impact: fire,
cold and a current running through a body. The engine knows no character: a move names
a status and how long it lasts, the numbers live in rules.toml, and whoever has one
carries it until it runs out.

A second hit does not stack - it refreshes, up to that status's own ceiling - so a
zoner cannot cook someone to death from across the arena by holding one button.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from jojo_arena.engine.data import seconds_to_frames

_HZ = 60  # the fixed step; kept here so this module needs nothing from the rules

# The vocabulary of the engine. A kit that names anything else fails to load.
BURN = "burn"
CHILL = "chill"
SHOCK = "shock"
KINDS: tuple[str, ...] = (BURN, CHILL, SHOCK)


@dataclass(frozen=True)
class StatusDef:
    """One status, as rules.toml describes it."""

    name: str
    max_f: int  # it never lasts longer than this, however often it is reapplied
    damage_per_f: float  # life lost while it holds
    walk_mult: float  # how much of their walk they keep
    blocks_regen: bool  # an undead body cannot close a wound while this lasts
    no_breath: bool  # no Hamon breathed in, no blood drunk
    no_meter: bool  # no Heart Heat gained
    guard_drain_per_f: float  # the guard gauge shakes apart on its own

    @classmethod
    def from_data(cls, name: str, data: dict) -> StatusDef:
        return cls(
            name=name,
            max_f=seconds_to_frames(data["max_s"]),
            damage_per_f=data.get("damage_per_s", 0.0) / _HZ,
            walk_mult=data.get("walk_mult", 1.0),
            blocks_regen=data.get("blocks_regen", False),
            no_breath=data.get("no_breath", False),
            no_meter=data.get("no_meter", False),
            guard_drain_per_f=data.get("guard_drain_per_s", 0.0) / _HZ,
        )


def load_statuses(data: dict) -> dict[str, StatusDef]:
    """The `[status.*]` tables of rules.toml. Every kind the engine knows must be there."""
    missing = [kind for kind in KINDS if kind not in data]
    if missing:
        raise ValueError(f"rules.toml: [status] is missing {', '.join(missing)}")
    return {kind: StatusDef.from_data(kind, data[kind]) for kind in KINDS}


class Statuses:
    """What is burning, freezing or crackling on one body, and for how much longer."""

    def __init__(self, defs: Mapping[str, StatusDef]) -> None:
        self._defs = defs
        self.left: dict[str, int] = {}
        self._damage_carry = 0.0

    # Reading ---------------------------------------------------------------------------

    def __contains__(self, name: str) -> bool:
        return self.left.get(name, 0) > 0

    def frames(self, name: str) -> int:
        return self.left.get(name, 0)

    @property
    def active(self) -> tuple[str, ...]:
        """The statuses in hand, always in the engine's own order (determinism)."""
        return tuple(kind for kind in KINDS if self.left.get(kind, 0) > 0)

    def _defs_active(self) -> tuple[StatusDef, ...]:
        return tuple(self._defs[kind] for kind in self.active)

    @property
    def walk_mult(self) -> float:
        mult = 1.0
        for defn in self._defs_active():
            mult *= defn.walk_mult
        return mult

    @property
    def blocks_regen(self) -> bool:
        return any(defn.blocks_regen for defn in self._defs_active())

    @property
    def no_breath(self) -> bool:
        return any(defn.no_breath for defn in self._defs_active())

    @property
    def no_meter(self) -> bool:
        return any(defn.no_meter for defn in self._defs_active())

    @property
    def guard_drain_per_f(self) -> float:
        return sum(defn.guard_drain_per_f for defn in self._defs_active())

    # Writing ---------------------------------------------------------------------------

    def apply(self, name: str, frames: int) -> bool:
        """Put a status on this body. Returns True when it was not already there, so the
        view and the sound only fire on the moment it catches."""
        defn = self._defs.get(name)
        if defn is None or frames <= 0:
            return False
        fresh = self.left.get(name, 0) <= 0
        self.left[name] = min(defn.max_f, max(self.left.get(name, 0), frames))
        return fresh

    def clear(self) -> None:
        self.left.clear()
        self._damage_carry = 0.0

    def tick(self) -> None:
        """One frame of it: everything counts down, what reaches zero is gone."""
        for name in list(self.left):
            self.left[name] -= 1
            if self.left[name] <= 0:
                del self.left[name]

    def damage_this_frame(self) -> int:
        """Whole points of life the statuses take this frame (fractions carry over)."""
        self._damage_carry += sum(defn.damage_per_f for defn in self._defs_active())
        whole = int(self._damage_carry)
        self._damage_carry -= whole
        return whole
