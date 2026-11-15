"""The sound pack: real sound files a player keeps on their own machine, next to their
settings, that the game plays in place of (or on top of) the sounds it synthesizes.

The game ships no recorded voice, music or effect: the pack is never part of it. Without
one, everything plays as before. With one, three folders are read:

    sound_pack/
      sfx/<name>.ogg                      in place of a synthesized effect (time_stop, hamon...)
      music/<track>.ogg                   in place of a rendered track, or for an arena
      voices/<fighter>/<slot>.ogg         what a fighter says

A fighter's slots: `<stance>.<move>` for the shout of a move ("stand.heavy"), `hha` and
`gha` for its supers, `intro.<opponent>` and `victory.<opponent>` for the lines it has
for one opponent, and `pose`, `win` and `ko`. `expected_slots` lists them all, for the
manifest written by tools/sound_pack.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jojo_arena.combat.kit import Kit, MoveDef
from jojo_arena.engine import audio, music

PACK_DIR_NAME = "sound_pack"
GENERIC_SLOTS = ("pose", "win", "ko")


def pack_dir(controls_path: Path) -> Path:
    """Where the pack lives: beside the player's own files, never inside the game."""
    return controls_path.parent / PACK_DIR_NAME


def load_pack(folder: Path) -> dict[str, list[str]]:
    """Read the pack into the audio and music players that are set up. Returns what was
    read, by kind (nothing when there is no pack)."""
    return {
        "sfx": audio.load_folder(folder / "sfx"),  # each under the effect's own name
        "music": music.load_folder(folder / "music"),
        "voices": audio.load_folder(folder / "voices", prefix="voices/"),
    }


def move_slot(fighter_id: str, kit: Kit, stance: str, move: MoveDef) -> str:
    """The voice slot of a move: a super is the same in every stance."""
    if kit.shared_moves.get(move.name) is move:
        return f"voices/{fighter_id}/{move.name}"
    return f"voices/{fighter_id}/{stance}.{move.name}"


def line_slot(fighter_id: str, kind: str, opponent_id: str) -> str:
    """The voice slot of a line said to one opponent: kind is "intro" or "victory"."""
    return f"voices/{fighter_id}/{kind}.{opponent_id}"


def generic_slot(fighter_id: str, kind: str) -> str:
    return f"voices/{fighter_id}/{kind}"


def say(*slots: str) -> bool:
    """Play the first of these slots the pack has. False when it has none of them."""
    return any(audio.has(slot) and audio.play(slot) for slot in slots)


@dataclass(frozen=True)
class Slot:
    name: str  # the file to put in the pack, without its extension
    kind: str  # "sfx", "music" or "voices"
    hint: str  # what goes there: the line said, or what the sound is


def expected_slots(roster, exchanges, sfx_names, track_names) -> list[Slot]:
    """Every file a complete pack would hold, with what each one is."""
    slots = [Slot(f"sfx/{name}", "sfx", "") for name in sorted(sfx_names)]
    slots += [Slot(f"music/{name}", "music", "") for name in sorted(track_names)]
    for fighter in roster:
        kit = fighter.kit
        for move in kit.shared_moves.values():
            if move.shout:
                slots.append(Slot(move_slot(fighter.id, kit, "", move), "voices", move.shout))
        for stance_name, stance in kit.stances.items():
            for move in stance.moves.values():
                if move.shout:
                    name = move_slot(fighter.id, kit, stance_name, move)
                    slots.append(Slot(name, "voices", move.shout))
        for kind in GENERIC_SLOTS:
            slots.append(Slot(generic_slot(fighter.id, kind), "voices", ""))
    for exchange in exchanges.values():
        for who, line in exchange.intro:
            (other,) = exchange.fighters - {who}
            slots.append(Slot(line_slot(who, "intro", other), "voices", line))
        for who, line in exchange.victory.items():
            (other,) = exchange.fighters - {who}
            slots.append(Slot(line_slot(who, "victory", other), "voices", line))
    return slots
