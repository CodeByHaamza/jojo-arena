"""Per-user settings folder and small JSON helpers."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def user_data_dir(app_name: str) -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / app_name


def read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


_SHORT_STRING_LIST = re.compile(r'\[\s*("[^"\s]*"(?:,\s*"[^"\s]*")*)\s*\]')


def to_readable_json(data: object) -> str:
    """Indented JSON, but lists of short words stay on one line: ["W", "Up"]."""
    text = json.dumps(data, indent=2, ensure_ascii=False)
    return _SHORT_STRING_LIST.sub(lambda m: "[" + re.sub(r",\s+", ", ", m.group(1)) + "]", text)


def write_json(path: Path, data: object) -> None:
    """Write through a temporary file so a crash never leaves a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(to_readable_json(data) + "\n", encoding="utf-8")
    tmp.replace(path)
