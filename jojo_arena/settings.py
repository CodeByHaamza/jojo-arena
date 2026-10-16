"""Player settings kept between sessions (the language), in settings.json beside the
controls file."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from jojo_arena.engine import i18n
from jojo_arena.engine.input import LAYOUTS

PAD_STYLES = ("auto", "xbox", "playstation")


@dataclass
class Settings:
    language: str = field(default_factory=i18n.system_language)
    cpu_level: int = 1  # the computer's level, as last picked
    volume: int = 7  # sound effects, 0 (silent) to 10
    music_volume: int = 5  # music, 0 (silent) to 10
    # How inputs are *named* on screen. "auto" believes the system and the pad itself.
    rumble: int = 7  # pad rumble, 0 (off) to 10
    layout: str = "auto"  # auto, azerty, qwerty
    pad_style: str = "auto"  # auto, xbox, playstation

    def to_json(self) -> dict:
        return {
            "language": self.language,
            "cpu_level": self.cpu_level,
            "volume": self.volume,
            "music_volume": self.music_volume,
            "rumble": self.rumble,
            "layout": self.layout,
            "pad_style": self.pad_style,
        }


def settings_path(controls_file: Path) -> Path:
    return controls_file.parent / "settings.json"


def parse_settings(data: object) -> Settings:
    """Settings from the file's data; anything missing or wrong keeps its default."""
    settings = Settings()
    if isinstance(data, dict) and data.get("language") in i18n.LANGUAGES:
        settings.language = data["language"]
    if isinstance(data, dict) and data.get("cpu_level") in (0, 1, 2, 3):
        settings.cpu_level = data["cpu_level"]
    if isinstance(data, dict) and data.get("volume") in range(11):
        settings.volume = data["volume"]
    if isinstance(data, dict) and data.get("music_volume") in range(11):
        settings.music_volume = data["music_volume"]
    if isinstance(data, dict) and data.get("rumble") in range(11):
        settings.rumble = data["rumble"]
    if isinstance(data, dict) and data.get("layout") in LAYOUTS:
        settings.layout = data["layout"]
    if isinstance(data, dict) and data.get("pad_style") in PAD_STYLES:
        settings.pad_style = data["pad_style"]
    return settings


def load_settings(path: Path) -> Settings:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = None
    return parse_settings(data)


def save_settings(settings: Settings, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings.to_json(), indent=2) + "\n", encoding="utf-8")
