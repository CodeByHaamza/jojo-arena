"""Keyboard and gamepad reading, turned into per-player InputFrames.

Keyboard bindings use *scancodes*: physical key positions, named after a US QWERTY
layout. "W" is the key under the left ring finger whatever the layout, so a binding
written for ZQSD on AZERTY is WASD on QWERTY without changing anything.

Gamepads go through SDL's GameController API, which gives every supported pad
(Xbox, DualShock, DualSense...) the same positional layout: "a" is the bottom face
button, "b" the right one, "x" the left one, "y" the top one.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import pygame

from .actions import MOVE_ACTIONS, InputFrame, direction_from_flags, merge_frames, quantize_8


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


# Who made the pad, read from the GUID: Sony pads get PlayStation button names.
PLAYSTATION_VENDOR = 0x054C
# Fallback when the GUID carries no vendor (Bluetooth, remapped pads, some drivers).
PLAYSTATION_HINTS = ("playstation", "dualshock", "dualsense", "ps3", "ps4", "ps5", "sony")


def guid_vendor(guid: str) -> int | None:
    """The USB vendor id inside an SDL joystick GUID, or None when it carries none.

    An SDL GUID is 32 hex characters; the vendor is a little-endian 16-bit field at
    characters 8 to 12, and it is zero for pads SDL could not identify.
    """
    if len(guid) < 12:
        return None
    try:
        return int(guid[10:12] + guid[8:10], 16) or None
    except ValueError:
        return None


@dataclass
class PadState:
    instance_id: int
    controller: object | None = None
    name: str = ""
    guid: str = ""
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

    @property
    def family(self) -> str:
        """ "playstation" or "xbox": which set of button names fits this pad."""
        vendor = guid_vendor(self.guid)
        if vendor is not None:
            return "playstation" if vendor == PLAYSTATION_VENDOR else "xbox"
        lowered = self.name.lower()
        return "playstation" if any(h in lowered for h in PLAYSTATION_HINTS) else "xbox"


class InputManager:
    """Collects device events; `begin_step` freezes the presses seen by the next step."""

    def __init__(self) -> None:
        self.keys_held: set[int] = set()
        self.key_presses: Counter[int] = Counter()
        self._key_pending: Counter[int] = Counter()
        self.pads: list[PadState] = []
        self.mouse_pos: tuple[int, int] = (0, 0)  # window pixels
        self.mouse_idle_f = 10**6  # steps since the mouse last moved or clicked

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
        joystick = pad.as_joystick()
        instance_id = joystick.get_instance_id()
        if all(state.instance_id != instance_id for state in self.pads):
            self.pads.append(PadState(instance_id, pad, *_pad_identity(joystick)))

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
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            self.mouse_pos = event.pos
            self.mouse_idle_f = 0
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
        self.mouse_idle_f += 1
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
        aim = None
        for pad in pads:
            x = pad.axes.get(pygame.CONTROLLER_AXIS_RIGHTX, 0.0)
            y = pad.axes.get(pygame.CONTROLLER_AXIS_RIGHTY, 0.0)
            if math.hypot(x, y) >= STICK_DEADZONE:
                aim = (x, y)
                break
        for action, axis, sign in self.STICK_ACTIONS:
            if stick[axis] * sign > 0:
                held.add(action)
                if self._last_stick[axis] * sign <= 0:
                    counts[action] = counts.get(action, 0) + 1
        self._last_stick = stick
        frame = _frame(held, counts)
        return InputFrame(frame.move, frame.held, frame.press_counts, stick=aim) if aim else frame


class MergedSource:
    """Several devices driving the same player (e.g. a pad and the keyboard)."""

    def __init__(self, *sources: KeyboardSource | GamepadSource) -> None:
        self.sources = sources

    def read(self, inputs: InputManager) -> InputFrame:
        return merge_frames(*(source.read(inputs) for source in self.sources))


def pad_connected(inputs: InputManager, slot: int | None) -> bool:
    return bool(inputs.pads) if slot is None else slot < len(inputs.pads)


_sdl_key_from_scancode = None


def _keycode_for(scancode: int) -> int | None:
    """The key this physical position types on the current layout (via SDL), or None."""
    global _sdl_key_from_scancode
    if _sdl_key_from_scancode is None:
        try:
            import ctypes
            import os

            names = ("SDL2.dll", "libSDL2-2.0.so.0", "libSDL2-2.0.0.dylib", "libSDL2.dylib")
            folder = os.path.dirname(pygame.__file__)
            library = next(
                ctypes.CDLL(os.path.join(folder, n))
                for n in names
                if os.path.exists(os.path.join(folder, n))
            )
            function = library.SDL_GetKeyFromScancode
            function.restype = ctypes.c_int32
            function.argtypes = [ctypes.c_int]
            _sdl_key_from_scancode = function
        except (OSError, StopIteration, AttributeError):
            _sdl_key_from_scancode = False
    if not _sdl_key_from_scancode or not pygame.display.get_init():
        return None
    keycode = _sdl_key_from_scancode(scancode)
    return keycode or None


def _pad_identity(joystick) -> tuple[str, str]:
    """(name, guid) of a pad; either can be missing on an older SDL build."""
    name = guid = ""
    for attribute, store in (("get_name", "name"), ("get_guid", "guid")):
        try:
            value = str(getattr(joystick, attribute)())
        except (AttributeError, pygame.error):  # pragma: no cover - depends on SDL
            value = ""
        if store == "name":
            name = value
        else:
            guid = value
    return name, guid


def _system_label(name: str) -> str:
    """What this physical key types on the layout the system reports."""
    scancode = KEY_SCANCODES.get(name)
    keycode = _keycode_for(scancode) if scancode is not None else None
    if keycode:
        label = pygame.key.name(keycode)
        if label:
            return label.upper()
    return name.upper()


LAYOUTS = ("auto", "azerty", "qwerty")
# A French AZERTY keyboard, named by US QWERTY position: only the keys that move.
AZERTY_LABELS = {"Q": "A", "W": "Z", "A": "Q", "Z": "W", "Semicolon": "M", "M": ","}
_layout = "auto"


def set_layout(name: str) -> None:
    """Force how keys are named, or "auto" to believe the system."""
    global _layout
    if name not in LAYOUTS:
        raise ValueError(f"unknown keyboard layout '{name}' (one of {', '.join(LAYOUTS)})")
    _layout = name


def layout() -> str:
    return _layout


def detected_layout() -> str:
    """What the system says this keyboard is, whatever the forced choice."""
    return "azerty" if _system_label("W") == "Z" else "qwerty"


def key_label(name: str) -> str:
    """How a physical key is labelled on this computer's keyboard: "W" reads "Z" on an
    AZERTY keyboard. Falls back to the US name when the layout cannot be asked."""
    if _layout == "qwerty":
        return name.upper()
    if _layout == "azerty":
        return AZERTY_LABELS.get(name, name.upper())
    return _system_label(name)
