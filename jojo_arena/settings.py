"""Player settings kept between sessions (the language), in settings.json beside the
controls file."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from jojo_arena.engine import i18n


@dataclass
class Settings:
    language: str = field(default_factory=i18n.system_language)

    def to_json(self) -> dict:
        return {"language": self.language}


def settings_path(controls_file: Path) -> Path:
    return controls_file.parent / "settings.json"


def parse_settings(data: object) -> Settings:
    """Settings from the file's data; anything missing or wrong keeps its default."""
    settings = Settings()
    if isinstance(data, dict) and data.get("language") in i18n.LANGUAGES:
        settings.language = data["language"]
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
