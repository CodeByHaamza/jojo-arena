"""Playable characters: data files and per-character code."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jojo_arena.combat.kit import Kit, load_kit
from jojo_arena.engine.data import load_toml
from jojo_arena.engine.i18n import localized
from jojo_arena.engine.sprites import Color, parse_color

_DIR = Path(__file__).parent


@dataclass(frozen=True)
class FighterDef:
    """Everything needed to field a character: gameplay kit plus how it looks."""

    id: str
    name: str
    kit: Kit
    sprite: str
    color: Color
    aura: Color
    palette: dict[str, list[Color]]
    stand_sprite: str = ""  # sheet of the Stand shown while it is out (if any)
    stand_name: str = ""
    role: str = ""  # one line, for the character select screen
    blurb: str = ""  # a short presentation
    selectable: bool = True  # placeholders stay out of the character select screen


def load_roster() -> list[FighterDef]:
    data = load_toml(_DIR / "roster.toml")
    kits: dict[str, Kit] = {}
    roster = []
    for entry in data["fighters"]:
        kit_id = entry["kit"]
        if kit_id not in kits:
            kits[kit_id] = load_kit(_DIR / f"{kit_id}.toml")
        palette = {
            slot: [parse_color(c) for c in colors]
            for slot, colors in entry.get("palette", {}).items()
        }
        roster.append(
            FighterDef(
                id=entry["id"],
                name=localized(entry, "name"),
                kit=kits[kit_id],
                sprite=entry.get("sprite", ""),
                color=parse_color(entry["color"]),
                aura=parse_color(entry.get("aura", entry["color"])),
                palette=palette,
                stand_sprite=entry.get("stand_sprite", ""),
                stand_name=entry.get("stand_name", ""),
                role=localized(entry, "role"),
                blurb=localized(entry, "blurb"),
                selectable=entry.get("selectable", True),
            )
        )
    return roster


def get_fighter(fighter_id: str) -> FighterDef:
    for fighter in load_roster():
        if fighter.id == fighter_id:
            return fighter
    raise KeyError(f"unknown fighter '{fighter_id}'")
