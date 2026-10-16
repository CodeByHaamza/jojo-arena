"""Rumble and the light bar of a pad: what happens is felt, not only seen.

Generic, like the rest of `engine/`: it knows about motors and colours, never about what
a game does with them. A pad that cannot rumble, cannot light up, or is not plugged in
simply does nothing - asking is always safe.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass

import pygame

from jojo_arena.engine.input import InputManager

# A pad can be unplugged mid-rumble, or not support rumble or a light at all.
PAD_ERRORS = (AttributeError, TypeError, ValueError, pygame.error)


@dataclass(frozen=True)
class Shake:
    """One rumble: how hard each motor pushes, and for how long."""

    low: float = 0.0  # the heavy motor, 0 to 1: the weight of a blow
    high: float = 0.0  # the light motor, 0 to 1: the sharpness of it
    ms: int = 120

    def scaled(self, strength: float) -> Shake:
        at_most = max(0.0, min(1.0, strength))
        return Shake(self.low * at_most, self.high * at_most, self.ms)


NO_SHAKE = Shake()


class Haptics:
    """Drives the pads of a running game. One instance per screen that needs it."""

    def __init__(self, inputs: InputManager, enabled: bool = True) -> None:
        self.inputs = inputs
        self.enabled = enabled
        self.strength = 1.0  # overall scale, for an Options slider
        self.sent: list[tuple[int, Shake]] = []  # what was asked for, for the tests

    def _joystick(self, slot: int | None):
        """The pad of that player, or None when there is none to talk to."""
        if not self.enabled or slot is None or slot < 0:
            return None
        pads = self.inputs.pads
        if slot >= len(pads):
            return None
        return pads[slot].joystick

    def shake(self, slot: int | None, pattern: Shake) -> bool:
        """Rumble one player's pad. True when the pad took it."""
        if pattern is NO_SHAKE or (pattern.low <= 0 and pattern.high <= 0):
            return False
        joystick = self._joystick(slot)
        if joystick is None:
            return False
        scaled = pattern.scaled(self.strength)
        self.sent.append((slot, scaled))
        try:
            return bool(joystick.rumble(scaled.low, scaled.high, scaled.ms))
        except PAD_ERRORS:  # pragma: no cover - a pad can be unplugged mid-rumble
            return False

    def light(self, slot: int | None, color: tuple[int, int, int]) -> bool:
        """Set the light bar of a pad that has one (DualShock 4, DualSense)."""
        joystick = self._joystick(slot)
        if joystick is None:
            return False
        try:
            return bool(joystick.set_led(color))
        except PAD_ERRORS:  # pragma: no cover - not every pad has a light
            return False

    def stop(self) -> None:
        """Cut every motor: on pause, on leaving a screen, on quitting."""
        for pad in self.inputs.pads:
            with contextlib.suppress(*PAD_ERRORS):
                pad.joystick.stop_rumble()
