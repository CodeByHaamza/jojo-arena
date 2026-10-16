"""The written references stay in step with the data."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KITS_DOC = (ROOT / "docs" / "KITS.md").read_text(encoding="utf-8")
STANCE_SLOTS = {"light", "heavy", "special", "special_alt"}


def keys_used(table: dict, found: set[str]) -> None:
    for key, value in table.items():
        found.add(key)
        if isinstance(value, dict):
            keys_used(value, found)


def test_every_kit_field_is_documented():
    found: set[str] = set()
    for path in (ROOT / "jojo_arena" / "characters").glob("*.toml"):
        if path.name in ("roster.toml", "parts.toml"):
            continue
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        for stance in data.get("stances", {}).values():
            keys_used({k: v for k, v in stance.items() if k != "moves"}, found)
            for move in stance.get("moves", {}).values():
                keys_used(move, found)
        for move in data.get("moves", {}).values():
            keys_used(move, found)
        for buff in data.get("buffs", {}).values():
            keys_used(buff, found)
        found |= {k for k in data if k not in ("stances", "moves", "buffs")}
    found -= {"projectile", "trap"} | STANCE_SLOTS
    missing = sorted(key for key in found if f"`{key}`" not in KITS_DOC)
    assert missing == [], f"add these fields to docs/KITS.md: {missing}"
