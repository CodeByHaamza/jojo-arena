"""What two fighters say to each other: before the fight, and the winner after it.

The lines live in `lines.toml`, one entry per pair, each with the battle of the games it
comes from. A pair without an entry falls back on each fighter's own lines (`[solo.<id>]`:
the entrance and the victory the games give them against anyone); a pair whose entry
lacks a winner's victory line takes that fighter's own. Nobody with either says nothing.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from jojo_arena.engine.data import load_toml
from jojo_arena.engine.i18n import localized

LINES_FILE = Path(__file__).parent / "lines.toml"


@dataclass(frozen=True)
class Exchange:
    fighters: frozenset[str]
    source: str
    intro: tuple[tuple[str, str], ...]  # (who speaks, the line), in the order they are said
    victory: Mapping[str, str]  # the winner's id -> what they say

    def victory_line(self, winner: str) -> str:
        return self.victory.get(winner, "")


def load_exchanges(path: Path = LINES_FILE) -> dict[frozenset[str], Exchange]:
    """Every pair that has something to say, in the current language."""
    found: dict[frozenset[str], Exchange] = {}
    for entry in load_toml(path).get("exchanges", []):
        pair = frozenset(entry["fighters"])
        found[pair] = Exchange(
            fighters=pair,
            source=entry.get("source", ""),
            intro=tuple((line["by"], localized(line, "text")) for line in entry.get("intro", [])),
            victory={
                who: localized(line, "text") for who, line in entry.get("victory", {}).items()
            },
        )
    return found


@dataclass(frozen=True)
class SoloLines:
    """What one fighter says against anyone: its entrance and its victory."""

    intro: str
    victory: str
    source: str


def load_solo(path: Path = LINES_FILE) -> dict[str, SoloLines]:
    """Each fighter's own lines, in the current language."""
    return {
        fighter: SoloLines(
            intro=localized(entry["intro"], "text") if "intro" in entry else "",
            victory=localized(entry["victory"], "text") if "victory" in entry else "",
            source=entry.get("source", ""),
        )
        for fighter, entry in load_toml(path).get("solo", {}).items()
    }


def exchange_for(first: str, second: str, path: Path = LINES_FILE) -> Exchange | None:
    """What these two say to each other, whichever side each is on (None: nothing)."""
    pair = load_exchanges(path).get(frozenset((first, second)))
    solo = load_solo(path)
    both = list(dict.fromkeys((first, second)))  # a mirror match: one fighter, said once
    own_victory = {who: solo[who].victory for who in both if who in solo and solo[who].victory}
    if pair is not None:
        # A pair's own lines first; a winner it has no line for says its own.
        return replace(pair, victory={**own_victory, **pair.victory})
    intro = tuple((who, solo[who].intro) for who in both if who in solo and solo[who].intro)
    if not intro and not own_victory:
        return None
    return Exchange(frozenset(both), "", intro, own_victory)
