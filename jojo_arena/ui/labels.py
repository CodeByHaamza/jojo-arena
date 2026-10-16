"""How inputs are named on screen: keyboard keys (as printed on this keyboard) and pad
buttons (Xbox or PlayStation names, depending on the pad plugged in)."""

from __future__ import annotations

from jojo_arena.controls import MENU_GAMEPAD, MENU_KEYBOARD, PlayerControls, Preset
from jojo_arena.engine import font
from jojo_arena.engine.input import InputManager, key_label
from jojo_arena.ui import text

KEYPAD_NAMES = {
    "Plus": "+",
    "Minus": "-",
    "Divide": "/",
    "Multiply": "X",
    "Period": ".",
}
XBOX = {
    "a": "A",
    "b": "B",
    "x": "X",
    "y": "Y",
    "leftshoulder": "LB",
    "rightshoulder": "RB",
    "lefttrigger": "LT",
    "righttrigger": "RT",
    "back": "VIEW",
    "start": "MENU",
    "guide": "XBOX",
    "leftstick": "LS",
    "rightstick": "RS",
    "misc1": "SHARE",
    "touchpad": "TOUCHPAD",
}
PLAYSTATION = {
    "a": "CROSS",
    "b": "CIRCLE",
    "x": "SQUARE",
    "y": "TRIANGLE",
    "leftshoulder": "L1",
    "rightshoulder": "R1",
    "lefttrigger": "L2",
    "righttrigger": "R2",
    "back": "SHARE",
    "start": "OPTIONS",
    "guide": "PS",
    "leftstick": "L3",
    "rightstick": "R3",
    "misc1": "MIC",
    "touchpad": "TOUCHPAD",
}
DPAD = {"dpad_up": "↑", "dpad_down": "↓", "dpad_left": "←", "dpad_right": "→"}
PLAYSTATION_HINTS = ("ps3", "ps4", "ps5", "playstation", "dualshock", "dualsense", "sony")


def keyboard_label(name: str) -> str:
    """A key by its position name ("W"), as printed on this keyboard ("Z" in AZERTY)."""
    if name in text.KEY_NAMES:
        return text.KEY_NAMES[name]
    if name.startswith("KP_"):
        rest = name[3:]
        key = text.KEYPAD_ENTER if rest == "Enter" else KEYPAD_NAMES.get(rest, rest)
        return text.KEYPAD.format(key=key)
    label = key_label(name)
    if all(c in font.GLYPHS for c in label):
        return label
    return name.upper()  # a character the pixel font cannot draw


def pad_family(inputs: InputManager | None, slot: int | None) -> str:
    """ "playstation" when that pad looks like a Sony one, otherwise "xbox"."""
    pads = inputs.pads if inputs is not None else []
    index = slot or 0
    if index >= len(pads) or pads[index].controller is None:
        return "xbox"
    name = str(getattr(pads[index].controller, "name", "")).lower()
    return "playstation" if any(hint in name for hint in PLAYSTATION_HINTS) else "xbox"


def pad_label(name: str, family: str = "xbox") -> str:
    if name in DPAD:
        return DPAD[name]
    if family == "playstation":
        names = {**PLAYSTATION, **text.PAD_PLAYSTATION}
    else:
        names = {**XBOX, **text.PAD_XBOX}
    return names.get(name, name.upper())


def action_label(player: PlayerControls, action: str, inputs: InputManager | None = None) -> str:
    """The first key or button bound to an action, or "-" when nothing is."""
    names = player.bindings.get(action, [])
    if not names:
        return "-"
    if player.device == "gamepad":
        return pad_label(names[0], pad_family(inputs, player.slot))
    return keyboard_label(names[0])


def move_label(player: PlayerControls) -> str:
    """The four directions: "ZQSD" on an AZERTY keyboard, "STICK" on a pad."""
    if player.device == "gamepad":
        return text.STICK
    keys = [player.bindings.get(a, []) for a in ("up", "left", "down", "right")]
    if all(keys):
        labels = [keyboard_label(k[0]) for k in keys]
        if all(len(label) == 1 for label in labels):
            return "".join(labels)
        if [k[0] for k in keys] == ["Up", "Left", "Down", "Right"]:
            return "↑←↓→"
    return text.DIRECTIONS


def device_label(player: PlayerControls) -> str:
    return text.DEVICE_GAMEPAD if player.device == "gamepad" else text.DEVICE_KEYBOARD


def preset_label(preset: Preset) -> str:
    """A built-in control preset by its name in the current language; one written in
    controls.json by the player keeps the label given there."""
    names = text.FR["PRESET_NAMES"]
    if names.get(preset.key) == preset.label:
        return text.PRESET_NAMES.get(preset.key, preset.label)
    return preset.label


def menu_key(action: str, inputs: InputManager | None = None) -> str:
    """The menu key for an action, e.g. "ENTRÉE", or "ENTRÉE/A" when a pad is plugged in."""
    label = keyboard_label(MENU_KEYBOARD[action][0])
    if inputs is not None and inputs.pads:
        label += "/" + pad_label(MENU_GAMEPAD[action][0], pad_family(inputs, 0))
    return label
