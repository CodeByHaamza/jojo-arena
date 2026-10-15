"""Loading of hand-edited data files (TOML)."""

from __future__ import annotations

import tomllib
from pathlib import Path


def load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def seconds_to_frames(seconds: float, hz: int = 60) -> int:
    return round(seconds * hz)
