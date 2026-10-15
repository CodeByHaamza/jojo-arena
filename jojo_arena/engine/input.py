"""Keyboard and gamepad reading, turned into per-player InputFrames.

Keyboard bindings use *scancodes*: physical key positions, named after a US QWERTY
layout. "W" is the key under the left ring finger whatever the layout, so a binding
written for ZQSD on AZERTY is WASD on QWERTY without changing anything.

Gamepads go through SDL's GameController API, which gives every supported pad
(Xbox, DualShock, DualSense...) the same positional layout: "a" is the bottom face
button, "b" the right one, "x" the left one, "y" the top one.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import pygame

from .actions import MOVE_ACTIONS, InputFrame, direction_from_flags, quantize_8


def _build_scancodes() -> dict[str, int]:
    codes: dict[str, int] = {}
    for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        codes[letter] = 4 + i
    for i, digit in enumerate("1234567890"):
        codes[digit] = 30 + i
    for i in range(12):
        codes[f"F{i + 1}"] = 58 + i
    for i in range(9):
        codes[f"KP_{i + 1}"] = 89 + i
    codes.update(
        {
            "Return": 40,
            "Escape": 41,
            "Backspace": 42,
            "Tab": 43,
            "Space": 44,
            "Minus": 45,
            "Equals": 46,
            "LeftBracket": 47,
            "RightBracket": 48,
            "Backslash": 49,
            "Semicolon": 51,
            "Apostrophe": 52,
            "Grave": 53,
            "Comma": 54,
            "Period": 55,
            "Slash": 56,
            "CapsLock": 57,
            "Insert": 73,
            "Home": 74,
            "PageUp": 75,
            "Delete": 76,
            "End": 77,
            "PageDown": 78,
            "Right": 79,
            "Left": 80,
            "Down": 81,
            "Up": 82,
            "KP_Divide": 84,
            "KP_Multiply": 85,
            "KP_Minus": 86,
            "KP_Plus": 87,
            "KP_Enter": 88,
            "KP_0": 98,
            "KP_Period": 99,
            "NonUSBackslash": 100,
            "LCtrl": 224,
            "LShift": 225,
            "LAlt": 226,
            "RCtrl": 228,
            "RShift": 229,
            "RAlt": 230,
        }
    )
    return codes


KEY_SCANCODES = _build_scancodes()

PAD_BUTTONS: dict[int, str] = {
    pygame.CONTROLLER_BUTTON_A: "a",
    pygame.CONTROLLER_BUTTON_B: "b",
    pygame.CONTROLLER_BUTTON_X: "x",
    pygame.CONTROLLER_BUTTON_Y: "y",
    pygame.CONTROLLER_BUTTON_BACK: "back",
    pygame.CONTROLLER_BUTTON_GUIDE: "guide",
    pygame.CONTROLLER_BUTTON_START: "start",
    pygame.CONTROLLER_BUTTON_LEFTSTICK: "leftstick",
    pygame.CONTROLLER_BUTTON_RIGHTSTICK: "rightstick",
    pygame.CONTROLLER_BUTTON_LEFTSHOULDER: "leftshoulder",
    pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: "rightshoulder",
    pygame.CONTROLLER_BUTTON_DPAD_UP: "dpad_up",
    pygame.CONTROLLER_BUTTON_DPAD_DOWN: "dpad_down",
    pygame.CONTROLLER_BUTTON_DPAD_LEFT: "dpad_left",
    pygame.CONTROLLER_BUTTON_DPAD_RIGHT: "dpad_right",
    15: "misc1",  # Xbox Series share button, PS5 mic button
    20: "touchpad",  # DualShock 4 / DualSense touchpad click
}
PAD_TRIGGERS: dict[int, str] = {
    pygame.CONTROLLER_AXIS_TRIGGERLEFT: "lefttrigger",
    pygame.CONTROLLER_AXIS_TRIGGERRIGHT: "righttrigger",
}
PAD_BUTTON_NAMES = frozenset(PAD_BUTTONS.values()) | frozenset(PAD_TRIGGERS.values())

AXIS_MAX = 32767
TRIGGER_THRESHOLD = 0.5
STICK_DEADZONE = 0.35


@dataclass
class PadState:
    instance_id: int
    controller: object | None = None
    held: set[str] = field(default_factory=set)
    axes: dict[int, float] = field(default_factory=dict)
    pending: Counter[str] = field(default_factory=Counter)
    presses: Counter[str] = field(default_factory=Counter)

    def press(self, name: str) -> None:
        self.held.add(name)
        self.pending[name] += 1

    def stick(self) -> tuple[float, float]:
        return (
            self.axes.get(pygame.CONTROLLER_AXIS_LEFTX, 0.0),
            self.axes.get(pygame.CONTROLLER_AXIS_LEFTY, 0.0),
        )


class InputManager:
    """Collects device events; `begin_step` freezes the presses seen by the next step."""

    def __init__(self) -> None:
        self.keys_held: set[int] = set()
        self.key_presses: Counter[int] = Counter()
        self._key_pending: Counter[int] = Counter()
        self.pads: list[PadState] = []

    def start(self) -> None:
        """Enable gamepads. Pads already plugged in are opened right away."""
        try:
            from pygame._sdl2 import controller
        except ImportError:  # pragma: no cover - depends on the SDL build
            return
        controller.init()
        for index in range(controller.get_count()):
            if controller.is_controller(index):
                self._open_pad(index)

    def _open_pad(self, device_index: int) -> None:
        from pygame._sdl2 import controller

        pad = controller.Controller(device_index)
        instance_id = pad.as_joystick().get_instance_id()
        if all(state.instance_id != instance_id for state in self.pads):
            self.pads.append(PadState(instance_id, pad))

    def _pad(self, instance_id: int) -> PadState | None:
        return next((pad for pad in self.pads if pad.instance_id == instance_id), None)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self.keys_held.add(event.scancode)
            self._key_pending[event.scancode] += 1
        elif event.type == pygame.KEYUP:
            self.keys_held.discard(event.scancode)
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.keys_held.clear()
        elif event.type == pygame.CONTROLLERDEVICEADDED:
            self._open_pad(event.device_index)
        elif event.type == pygame.CONTROLLERDEVICEREMOVED:
            self.pads = [pad for pad in self.pads if pad.instance_id != event.instance_id]
        elif event.type in (pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERBUTTONUP):
            pad = self._pad(event.instance_id)
            name = PAD_BUTTONS.get(event.button)
            if pad is None or name is None:
                return
            if event.type == pygame.CONTROLLERBUTTONDOWN:
                pad.press(name)
            else:
                pad.held.discard(name)
        elif event.type == pygame.CONTROLLERAXISMOTION:
            pad = self._pad(event.instance_id)
            if pad is None:
                return
            value = max(-1.0, min(1.0, event.value / AXIS_MAX))
            pad.axes[event.axis] = value
            trigger = PAD_TRIGGERS.get(event.axis)
            if trigger is not None:
                if value >= TRIGGER_THRESHOLD and trigger not in pad.held:
                    pad.press(trigger)
                elif value < TRIGGER_THRESHOLD:
                    pad.held.discard(trigger)

    def begin_step(self) -> None:
        self.key_presses, self._key_pending = self._key_pending, Counter()
        for pad in self.pads:
            pad.presses, pad.pending = pad.pending, Counter()


def _frame(held: set[str], counts: dict[str, int]) -> InputFrame:
    move = direction_from_flags(*(action in held for action in MOVE_ACTIONS))
    return InputFrame(move, frozenset(held), {a: n for a, n in counts.items() if n})


class KeyboardSource:
    def __init__(self, bindings: Mapping[str, Sequence[str]]) -> None:
        self.unknown = sorted(
            {name for names in bindings.values() for name in names if name not in KEY_SCANCODES}
        )
        self.codes = {
            action: [KEY_SCANCODES[name] for name in names if name in KEY_SCANCODES]
            for action, names in bindings.items()
        }

    def read(self, inputs: InputManager) -> InputFrame:
        held = {a for a, codes in self.codes.items() if any(c in inputs.keys_held for c in codes)}
        counts = {a: sum(inputs.key_presses[c] for c in codes) for a, codes in self.codes.items()}
        return _frame(held, counts)


class GamepadSource:
    """One pad by connection order (`slot`), or every connected pad when slot is None."""

    STICK_ACTIONS = (("up", 1, -1), ("down", 1, 1), ("left", 0, -1), ("right", 0, 1))

    def __init__(self, bindings: Mapping[str, Sequence[str]], slot: int | None) -> None:
        self.slot = slot
        self.unknown = sorted(
            {name for names in bindings.values() for name in names if name not in PAD_BUTTON_NAMES}
        )
        self.buttons = {action: list(names) for action, names in bindings.items()}
        self._last_stick = (0.0, 0.0)

    def _pads(self, inputs: InputManager) -> list[PadState]:
        if self.slot is None:
            return inputs.pads
        return inputs.pads[self.slot : self.slot + 1]

    def read(self, inputs: InputManager) -> InputFrame:
        pads = self._pads(inputs)
        held: set[str] = set()
        counts: dict[str, int] = {}
        for action, names in self.buttons.items():
            if any(name in pad.held for pad in pads for name in names):
                held.add(action)
            counts[action] = sum(pad.presses[name] for pad in pads for name in names)

        stick = (0.0, 0.0)
        for pad in pads:
            stick = quantize_8(*pad.stick(), STICK_DEADZONE)
            if stick != (0.0, 0.0):
                break
        for action, axis, sign in self.STICK_ACTIONS:
            if stick[axis] * sign > 0:
                held.add(action)
                if self._last_stick[axis] * sign <= 0:
                    counts[action] = counts.get(action, 0) + 1
        self._last_stick = stick
        return _frame(held, counts)


def pad_connected(inputs: InputManager, slot: int | None) -> bool:
    return bool(inputs.pads) if slot is None else slot < len(inputs.pads)
