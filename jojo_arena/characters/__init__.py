"""Playable characters: data files and per-character code."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jojo_arena.combat.kit import Kit, load_kit
from jojo_arena.combat.rules import load_rules
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
    # Characters who call in more than one helper: a sheet per stance.
    stand_sprites: dict[str, str] = field(default_factory=dict)
    stand_name: str = ""
    role: str = ""  # one line, for the character select screen
    blurb: str = ""  # a short presentation
    selectable: bool = True  # placeholders stay out of the character select screen
    part: int = 0  # the JoJo part the character comes from (0: none, like the dummies)


@dataclass(frozen=True)
class PartDef:
    """One of the nine parts of the saga, as the menus show it."""

    number: int
    title: str
    setting: str  # where and when it takes place
    colors: tuple[Color, Color]  # two accent colors
    emblem: str = ""  # icon name: a little symbol of the part


def load_parts() -> list[PartDef]:
    data = load_toml(_DIR / "parts.toml")
    return [
        PartDef(
            number=entry["number"],
            title=localized(entry, "title"),
            setting=localized(entry, "setting"),
            colors=(parse_color(entry["colors"][0]), parse_color(entry["colors"][1])),
            emblem=entry.get("emblem", ""),
        )
        for entry in sorted(data["parts"], key=lambda e: e["number"])
    ]


def load_roster() -> list[FighterDef]:
    data = load_toml(_DIR / "roster.toml")
    kits: dict[str, Kit] = {}
    hh_bar = load_rules().hh_bar  # an awakening is priced in bars, so it needs the size
    roster = []
    for entry in data["fighters"]:
        kit_id = entry["kit"]
        if kit_id not in kits:
            kits[kit_id] = load_kit(_DIR / f"{kit_id}.toml", hh_bar)
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
                stand_sprites=dict(entry.get("stand_sprites", {})),
                stand_name=entry.get("stand_name", ""),
                role=localized(entry, "role"),
                blurb=localized(entry, "blurb"),
                selectable=entry.get("selectable", True),
                part=entry.get("part", 0),
            )
        )
    return roster


def get_fighter(fighter_id: str) -> FighterDef:
    for fighter in load_roster():
        if fighter.id == fighter_id:
            return fighter
    raise KeyError(f"unknown fighter '{fighter_id}'")
