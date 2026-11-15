"""What a player chose for a fighter besides the fighter itself: the poses (and, later,
the costume and the colours). Purely what is shown: the simulation never sees it, so a
replay plays the same fight whatever was picked."""

from __future__ import annotations

import random
from dataclasses import dataclass

from jojo_arena.engine.sprites import SpriteSet


@dataclass(frozen=True)
class Loadout:
    pose: str = ""  # the JoJo pose struck alone (id in the sheet's [poses])
    stand_pose: str = ""  # the one struck with the Stand out, the Stand posing too


def _ids(sprites: SpriteSet, stand: bool) -> list[str]:
    return [pose_id for pose_id, info in sprites.poses.items() if info.stand == stand]


def resolve_loadout(sprites: SpriteSet, loadout: Loadout | None) -> Loadout:
    """The loadout this sheet can play: a pose it does not have (an old settings file, a
    pose of the wrong kind) becomes its first pose of that kind, and "" when it has none,
    which plays the generic pose."""
    loadout = loadout or Loadout()

    def keep(wanted: str, stand: bool) -> str:
        ids = _ids(sprites, stand)
        return wanted if wanted in ids else (ids[0] if ids else "")

    return Loadout(keep(loadout.pose, False), keep(loadout.stand_pose, True))


def random_loadout(sprites: SpriteSet, rng: random.Random) -> Loadout:
    """The computer's pick: any pose of each kind."""
    alone, together = _ids(sprites, False), _ids(sprites, True)
    return Loadout(rng.choice(alone) if alone else "", rng.choice(together) if together else "")
