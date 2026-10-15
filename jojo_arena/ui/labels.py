"""How inputs are named on screen: keyboard keys (as printed on this keyboard) and pad
buttons (Xbox or PlayStation names, depending on the pad plugged in)."""

from __future__ import annotations

from jojo_arena.controls import MENU_GAMEPAD, MENU_KEYBOARD, PlayerControls
from jojo_arena.engine import font
from jojo_arena.engine.input import InputManager, key_label

KEY_NAMES = {
    "Space": "ESPACE",
    "Return": "ENTRÉE",
    "Escape": "ÉCHAP",
    "Backspace": "EFFACER",
    "Tab": "TAB",
    "CapsLock": "VERR MAJ",
    "LShift": "MAJ G",
    "RShift": "MAJ D",
    "LCtrl": "CTRL G",
    "RCtrl": "CTRL D",
    "LAlt": "ALT",
    "RAlt": "ALT GR",
    "Up": "HAUT",
    "Down": "BAS",
    "Left": "GAUCHE",
    "Right": "DROITE",
    "Insert": "INSER",
    "Delete": "SUPPR",
    "Home": "DÉBUT",
    "End": "FIN",
    "PageUp": "PAGE HAUT",
    "PageDown": "PAGE BAS",
}
KEYPAD_NAMES = {
    "Enter": "ENTRÉE",
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
    "misc1": "PARTAGE",
    "touchpad": "PAVÉ",
}
PLAYSTATION = {
    "a": "CROIX",
    "b": "ROND",
    "x": "CARRÉ",
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
    "misc1": "MICRO",
    "touchpad": "PAVÉ TACTILE",
}
PLAYSTATION_HINTS = ("ps3", "ps4", "ps5", "playstation", "dualshock", "dualsense", "sony")


def keyboard_label(name: str) -> str:
    """A key by its position name ("W"), as printed on this keyboard ("Z" in AZERTY)."""
    if name in KEY_NAMES:
        return KEY_NAMES[name]
    if name.startswith("KP_"):
        rest = name[3:]
        return "PAVÉ " + KEYPAD_NAMES.get(rest, rest)
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
    names = PLAYSTATION if family == "playstation" else XBOX
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
        return "STICK"
    keys = [player.bindings.get(a, []) for a in ("up", "left", "down", "right")]
    if all(keys):
        labels = [keyboard_label(k[0]) for k in keys]
        if all(len(label) == 1 for label in labels):
            return "".join(labels)
        if [k[0] for k in keys] == ["Up", "Left", "Down", "Right"]:
            return "↑←↓→"
    return "DIRECTIONS"


def device_label(player: PlayerControls) -> str:
    return "MANETTE" if player.device == "gamepad" else "CLAVIER"


def menu_key(action: str, inputs: InputManager | None = None) -> str:
    """The menu key for an action, e.g. "ENTRÉE", or "ENTRÉE/A" when a pad is plugged in."""
    label = keyboard_label(MENU_KEYBOARD[action][0])
    if inputs is not None and inputs.pads:
        label += "/" + pad_label(MENU_GAMEPAD[action][0], pad_family(inputs, 0))
    return label
