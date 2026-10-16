"""The glossary: lore terms, characters and Stands of each part, from characters/lore/.

One file per part (part1.toml...), filled as the parts come into the game. Texts are
read in the current language (engine.i18n).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jojo_arena.engine.data import load_toml
from jojo_arena.engine.i18n import localized

LORE_DIR = Path(__file__).parent / "lore"
KINDS = ("terms", "characters", "stands")
STAT_NAMES = ("power", "speed", "range", "durability", "precision", "potential")


@dataclass(frozen=True)
class Entry:
    kind: str  # one of KINDS
    id: str
    name: str
    text: str
    icon: str = ""  # icon shown for a term
    fighter: str = ""  # fighter whose sprite shows, for a character
    sprite: str = ""  # sprite sheet shown, for a Stand
    subtitle: str = ""  # a character's Stand, or a Stand's user
    family: str = ""
    name_origin: str = ""
    stats: str = ""  # six grades A to E, in STAT_NAMES order (Stands)

    def stat_grades(self) -> dict[str, str]:
        return dict(zip(STAT_NAMES, self.stats, strict=False))


def _entry(kind: str, data: dict) -> Entry:
    subtitle = data.get("stand", "") if kind == "characters" else data.get("user", "")
    return Entry(
        kind=kind,
        id=data["id"],
        name=localized(data, "name"),
        text=localized(data, "text"),
        icon=data.get("icon", ""),
        fighter=data.get("fighter", ""),
        sprite=data.get("sprite", ""),
        subtitle=subtitle,
        family=localized(data, "family"),
        name_origin=localized(data, "name_origin"),
        stats=data.get("stats", ""),
    )


def load_glossary(lore_dir: Path = LORE_DIR) -> dict[int, dict[str, list[Entry]]]:
    """Part number -> kind -> entries, in the order of the files."""
    glossary: dict[int, dict[str, list[Entry]]] = {}
    for path in sorted(lore_dir.glob("part*.toml")):
        data = load_toml(path)
        part = glossary.setdefault(data["part"], {kind: [] for kind in KINDS})
        for kind in KINDS:
            part[kind] += [_entry(kind, item) for item in data.get(kind, [])]
    return glossary
