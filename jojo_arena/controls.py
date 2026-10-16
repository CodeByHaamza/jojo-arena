"""Control presets (default mapping from the GDD) and the user's rebindable controls file.

The file lives in the user settings folder (see `controls_path`). Missing actions or
presets fall back to the defaults, so a partial or outdated file keeps working.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from jojo_arena.engine.input import (
    KEY_SCANCODES,
    PAD_BUTTON_NAMES,
    GamepadSource,
    KeyboardSource,
    MergedSource,
)
from jojo_arena.engine.storage import read_json, user_data_dir, write_json

APP_DIR_NAME = "JoJoArena"
CONTROLS_FILE = "controls.json"

ACTIONS = (
    "up",
    "down",
    "left",
    "right",
    "light",
    "heavy",
    "special",
    "stand",
    "dash",
    "guard",
    "heart_heat",
    "pose",
    "power_up",
    "confirm",
    "back",
    "pause",
)

# GDD mapping. Key names are physical positions on a US QWERTY keyboard:
# W A S D here are Z Q S D on an AZERTY keyboard.
KEYBOARD_MAIN = {
    "up": ["W", "Up"],
    "down": ["S", "Down"],
    "left": ["A", "Left"],
    "right": ["D", "Right"],
    "light": ["J"],
    "heavy": ["K"],
    "special": ["L"],
    "stand": ["I"],
    "dash": ["Space"],
    "guard": ["LShift"],
    "heart_heat": ["O"],
    "pose": ["P"],
    "power_up": ["U"],
    "confirm": ["Return", "KP_Enter", "J"],
    "back": ["Escape", "Backspace"],
    "pause": ["Escape"],
}
GAMEPAD = {
    "up": ["dpad_up"],
    "down": ["dpad_down"],
    "left": ["dpad_left"],
    "right": ["dpad_right"],
    "light": ["x"],
    "heavy": ["y"],
    "special": ["b"],
    "stand": ["rightshoulder"],
    "dash": ["a"],
    "guard": ["leftshoulder"],
    "heart_heat": ["righttrigger"],
    "pose": ["back", "touchpad"],
    "power_up": ["lefttrigger"],
    "confirm": ["a", "start"],
    "back": ["b"],
    "pause": ["start"],
}
# Two players on one keyboard: P1 on the left half, P2 on arrows + numpad.
SHARED_LEFT = {
    "up": ["W"],
    "down": ["S"],
    "left": ["A"],
    "right": ["D"],
    "light": ["F"],
    "heavy": ["G"],
    "special": ["H"],
    "stand": ["R"],
    "dash": ["V"],
    "guard": ["C"],
    "heart_heat": ["T"],
    "pose": ["Y"],
    "power_up": ["B"],
    "confirm": ["F"],
    "back": ["H"],
    "pause": ["Escape"],
}
SHARED_RIGHT = {
    "up": ["Up"],
    "down": ["Down"],
    "left": ["Left"],
    "right": ["Right"],
    "light": ["KP_4"],
    "heavy": ["KP_5"],
    "special": ["KP_6"],
    "stand": ["KP_8"],
    "dash": ["KP_0"],
    "guard": ["KP_1"],
    "heart_heat": ["KP_9"],
    "pose": ["KP_7"],
    "power_up": ["KP_3"],
    "confirm": ["KP_4", "KP_Enter"],
    "back": ["KP_6"],
    "pause": ["KP_Plus"],
}
# Menus accept any keyboard and any pad, whatever the preset.
MENU_KEYBOARD = {
    "up": ["Up", "W"],
    "down": ["Down", "S"],
    "left": ["Left", "A"],
    "right": ["Right", "D"],
    "confirm": ["Return", "KP_Enter", "Space", "J"],
    "back": ["Escape", "Backspace"],
    "pause": ["Escape"],
    "info": ["Tab", "I"],  # character details / move list
    "prev": ["Q", "PageUp"],  # previous tab (A on an AZERTY keyboard)
    "next": ["E", "PageDown"],  # next tab
}
MENU_GAMEPAD = {
    "up": ["dpad_up"],
    "down": ["dpad_down"],
    "left": ["dpad_left"],
    "right": ["dpad_right"],
    "confirm": ["a", "start"],
    "back": ["b"],
    "pause": ["start"],
    "info": ["y"],
    "prev": ["leftshoulder"],
    "next": ["rightshoulder"],
}

DEFAULT_ACTIVE = "keyboard_gamepad"
DEFAULT_PRESETS = {
    "keyboard_gamepad": {
        "label": "J1 CLAVIER  J2 MANETTE",
        "players": [
            {"device": "keyboard", "bindings": KEYBOARD_MAIN},
            {"device": "gamepad", "slot": 0, "bindings": GAMEPAD},
        ],
    },
    "shared_keyboard": {
        "label": "CLAVIER PARTAGÉ",
        "players": [
            {"device": "keyboard", "bindings": SHARED_LEFT},
            {"device": "keyboard", "bindings": SHARED_RIGHT},
        ],
    },
    "two_gamepads": {
        "label": "DEUX MANETTES",
        "players": [
            {"device": "gamepad", "slot": 0, "bindings": GAMEPAD},
            {"device": "gamepad", "slot": 1, "bindings": GAMEPAD},
        ],
    },
}

HELP = [
    "Fichier des contrôles de JoJo Arena. Modifie les listes de touches puis relance le jeu.",
    "Clavier : noms des touches selon leur POSITION sur un clavier QWERTY US.",
    "Exemple : 'W' est la touche Z d'un clavier AZERTY, 'A' est le Q, 'Q' est le A.",
    "Autres noms : Space, Return, Escape, LShift, RShift, LCtrl, Up, Down, Left, Right,",
    "KP_0 à KP_9 (pavé numérique), KP_Enter, KP_Plus, F1 à F12...",
    "Manette : a (bas), b (droite), x (gauche), y (haut), leftshoulder, rightshoulder,",
    "lefttrigger, righttrigger, back, start, touchpad, dpad_up, dpad_down...",
    "Supprime ce fichier pour revenir aux contrôles par défaut.",
]


@dataclass(frozen=True)
class PlayerControls:
    device: str  # "keyboard" or "gamepad"
    bindings: dict[str, list[str]]
    slot: int = 0

    def build_source(self) -> KeyboardSource | GamepadSource:
        if self.device == "gamepad":
            return GamepadSource(self.bindings, self.slot)
        return KeyboardSource(self.bindings)


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    players: tuple[PlayerControls, PlayerControls]

    def pads_needed(self) -> int:
        return max((p.slot + 1 for p in self.players if p.device == "gamepad"), default=0)

    def build_sources(self) -> list[KeyboardSource | GamepadSource | MergedSource]:
        """One input source per player. When nobody plays on the keyboard, player 1 also
        listens to it: a missing pad must never leave the game unplayable."""
        sources: list = [p.build_source() for p in self.players]
        if all(p.device == "gamepad" for p in self.players):
            sources[0] = MergedSource(sources[0], KeyboardSource(KEYBOARD_MAIN))
        return sources


@dataclass
class ControlsConfig:
    active: str
    presets: dict[str, Preset]

    @property
    def active_preset(self) -> Preset:
        return self.presets[self.active]

    def cycle(self, step: int) -> None:
        keys = list(self.presets)
        self.active = keys[(keys.index(self.active) + step) % len(keys)]

    def to_json(self) -> dict:
        return {
            "_aide": HELP,
            "active_preset": self.active,
            "presets": {
                key: {
                    "label": preset.label,
                    "players": [
                        {"device": p.device, "slot": p.slot, "bindings": p.bindings}
                        if p.device == "gamepad"
                        else {"device": p.device, "bindings": p.bindings}
                        for p in preset.players
                    ],
                }
                for key, preset in self.presets.items()
            },
        }


def _parse_player(raw: object, fallback: dict | None, where: str, warnings: list[str]):
    if not isinstance(raw, dict):
        warnings.append(f"{where}: entrée invalide, valeurs par défaut utilisées")
        raw = {}
    base = fallback or {"device": "keyboard", "bindings": {}}
    device = raw.get("device", base["device"])
    if device not in ("keyboard", "gamepad"):
        warnings.append(f"{where}: device inconnu '{device}'")
        device = base["device"]
    slot = raw.get("slot", base.get("slot", 0))
    if not isinstance(slot, int) or slot < 0:
        warnings.append(f"{where}: slot invalide '{slot}'")
        slot = base.get("slot", 0)
    known = KEY_SCANCODES if device == "keyboard" else PAD_BUTTON_NAMES
    default_bindings = base["bindings"] if base["device"] == device else {}
    bindings = {action: list(default_bindings.get(action, [])) for action in ACTIONS}
    user_bindings = raw.get("bindings", {})
    if isinstance(user_bindings, dict):
        for action, names in user_bindings.items():
            if action not in ACTIONS:
                warnings.append(f"{where}: action inconnue '{action}'")
                continue
            if isinstance(names, str):
                names = [names]
            if not isinstance(names, list):
                warnings.append(f"{where}.{action}: liste de touches attendue")
                continue
            valid = [n for n in names if isinstance(n, str) and n in known]
            for bad in (n for n in names if n not in valid):
                warnings.append(f"{where}.{action}: touche inconnue '{bad}'")
            bindings[action] = valid
    return PlayerControls(device, bindings, slot)


def parse_controls(data: object) -> tuple[ControlsConfig, list[str]]:
    """Build a config from parsed JSON, filling every gap with the defaults."""
    warnings: list[str] = []
    raw_presets = {}
    active = DEFAULT_ACTIVE
    if isinstance(data, dict):
        raw_presets = data.get("presets", {})
        if not isinstance(raw_presets, dict):
            warnings.append("presets: objet attendu")
            raw_presets = {}
        active = data.get("active_preset", DEFAULT_ACTIVE)
    elif data is not None:
        warnings.append("fichier de contrôles invalide, valeurs par défaut utilisées")

    presets: dict[str, Preset] = {}
    for key in list(DEFAULT_PRESETS) + [k for k in raw_presets if k not in DEFAULT_PRESETS]:
        default = DEFAULT_PRESETS.get(key)
        raw = raw_presets.get(key, {})
        if not isinstance(raw, dict):
            warnings.append(f"{key}: objet attendu")
            raw = {}
        raw_players = raw.get("players", [])
        if not isinstance(raw_players, list):
            raw_players = []
        players = []
        for i in range(2):
            fallback = default["players"][i] if default else None
            raw_player = raw_players[i] if i < len(raw_players) else (fallback or {})
            players.append(_parse_player(raw_player, fallback, f"{key}.J{i + 1}", warnings))
        label = raw.get("label", default["label"] if default else key.upper())
        presets[key] = Preset(key, str(label), (players[0], players[1]))

    if active not in presets:
        warnings.append(f"active_preset inconnu '{active}'")
        active = DEFAULT_ACTIVE
    return ControlsConfig(active, presets), warnings


def controls_path() -> Path:
    return user_data_dir(APP_DIR_NAME) / CONTROLS_FILE


def load_controls(path: Path) -> tuple[ControlsConfig, list[str]]:
    """Read the controls file, creating it with the defaults the first time."""
    if not path.exists():
        config, warnings = parse_controls(None)
        save_controls(config, path)
        return config, warnings
    try:
        data = read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        config, warnings = parse_controls(None)
        return config, [f"{path.name} illisible ({error}), contrôles par défaut utilisés"]
    return parse_controls(data)


def save_controls(config: ControlsConfig, path: Path) -> None:
    write_json(path, config.to_json())


def menu_sources() -> list[KeyboardSource | GamepadSource]:
    return [KeyboardSource(MENU_KEYBOARD), GamepadSource(MENU_GAMEPAD, slot=None)]
