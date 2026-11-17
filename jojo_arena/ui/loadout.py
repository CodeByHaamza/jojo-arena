"""What a player chose for a fighter besides the fighter itself: the costume, its colour and
the poses. Purely what is shown: the simulation never sees it, so a replay plays the same
fight whatever was picked."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from jojo_arena.engine.data import load_toml
from jojo_arena.engine.sprites import SpriteSet
from jojo_arena.paths import SPRITES_DIR

if TYPE_CHECKING:
    from jojo_arena.characters import FighterDef


@dataclass(frozen=True)
class Loadout:
    pose: str = ""  # the JoJo pose struck alone (id in the sheet's [poses])
    stand_pose: str = ""  # the one struck with the Stand out, the Stand posing too
    costume: str = ""  # a costume of the roster entry ("": the normal one)
    color: str = ""  # a colour of that costume's sheet ("": the first, the sheet as drawn)


def _ids(sprites: SpriteSet, stand: bool) -> list[str]:
    return [pose_id for pose_id, info in sprites.poses.items() if info.stand == stand]


def resolve_loadout(sprites: SpriteSet, loadout: Loadout | None) -> Loadout:
    """The loadout this sheet can play: a pose it does not have (an old settings file, a
    pose of the wrong kind) becomes its first pose of that kind, and "" when it has none,
    which plays the generic pose; a colour it does not have becomes its own."""
    loadout = loadout or Loadout()

    def keep(wanted: str, stand: bool) -> str:
        ids = _ids(sprites, stand)
        return wanted if wanted in ids else (ids[0] if ids else "")

    color = loadout.color if loadout.color in sprites.colors else ""
    return Loadout(
        keep(loadout.pose, False), keep(loadout.stand_pose, True), loadout.costume, color
    )


def random_loadout(sprites: SpriteSet, rng: random.Random) -> Loadout:
    """The computer's pick: any pose of each kind."""
    alone, together = _ids(sprites, False), _ids(sprites, True)
    return Loadout(rng.choice(alone) if alone else "", rng.choice(together) if together else "")


# Costumes and colours -----------------------------------------------------------------------


def outfit_sheet(fighter_def: FighterDef, loadout: Loadout | None) -> str:
    """The sheet of the costume asked: the normal one for a costume the fighter has not."""
    costume = loadout.costume if loadout is not None else ""
    return fighter_def.costumes.get(costume, fighter_def.sprite)


def outfit_colors(fighter_def: FighterDef, costume: str = "") -> list[str]:
    """The colours of one costume of a fighter, in order (none: its sheet has no colours).
    Read from the sheet's description alone: the image is not decoded for this."""
    sheet = fighter_def.costumes.get(costume, fighter_def.sprite)
    spec = (SPRITES_DIR / sheet).with_suffix(".toml") if sheet else None
    if spec is None or not spec.exists():
        return []
    return list(load_toml(spec).get("colors", {}))


def distinct(first: Loadout, second: Loadout, colors: list[str]) -> Loadout:
    """Two players on the same fighter never look the same: when both wear the same
    costume in the same colour, the second takes the next colour of `colors` (that
    costume's). With one colour or none, there is nothing to tell them apart with."""
    if first.costume != second.costume or len(colors) < 2:
        return second
    taken = first.color if first.color in colors else colors[0]
    mine = second.color if second.color in colors else colors[0]
    if mine != taken:
        return second
    return replace(second, color=colors[(colors.index(taken) + 1) % len(colors)])


def settle(fighter_defs, loadouts) -> list[Loadout]:
    """The loadouts a fight is drawn with: a costume the fighter does not have is its normal
    one, a colour that costume does not have is its first, and two sides on the same
    fighter are told apart (see `distinct`)."""
    settled = []
    for fighter_def, loadout in zip(fighter_defs, loadouts, strict=False):
        loadout = loadout or Loadout()
        costume = loadout.costume if loadout.costume in fighter_def.costumes else ""
        color = loadout.color if loadout.color in outfit_colors(fighter_def, costume) else ""
        settled.append(replace(loadout, costume=costume, color=color))
    if len(settled) == 2 and fighter_defs[0].id == fighter_defs[1].id:
        colors = outfit_colors(fighter_defs[1], settled[1].costume)
        settled[1] = distinct(settled[0], settled[1], colors)
    return settled


def random_outfit(fighter_def: FighterDef, rng: random.Random) -> Loadout:
    """The computer's pick: any costume of the fighter, in any of its colours."""
    costume = rng.choice(["", *fighter_def.costumes])
    colors = outfit_colors(fighter_def, costume)
    return Loadout(costume=costume, color=rng.choice(colors) if colors else "")
