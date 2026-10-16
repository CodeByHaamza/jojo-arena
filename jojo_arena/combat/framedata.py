"""Frame data of a move, as fighting game players read it.

Startup is the number of frames before the move can hit; advantage is how many frames
earlier (+) or later (-) the attacker can act again than the defender, after a hit or a
block on the first active frame. Hitstop freezes both sides alike, so it does not count.
"""

from __future__ import annotations

from dataclasses import dataclass

from jojo_arena.combat.kit import MoveDef
from jojo_arena.combat.rules import Rules


@dataclass(frozen=True)
class FrameData:
    startup: int
    active: int
    recovery: int
    on_hit: int | None  # None when it does not apply (projectiles, rushes, cutscenes)
    on_block: int | None


def frame_data(move: MoveDef, rules: Rules) -> FrameData:
    on_hit = on_block = None
    single_blow = move.radius > 0 and move.hits <= 1 and not move.cinematic
    if single_blow:
        # Frames the attacker still has to play after its first active frame.
        busy = move.active_f - 1 + move.recovery_f
        blockstun = move.blockstun_f or round(move.hitstun_f * rules.blockstun_ratio)
        on_hit = move.hitstun_f - busy
        on_block = None if move.unblockable else blockstun - busy
    return FrameData(move.startup_f, move.active_f, move.recovery_f, on_hit, on_block)


def signed(value: int | None) -> str:
    """+6, -2, 0, or "-" when it does not apply."""
    if value is None:
        return "-"
    return f"+{value}" if value > 0 else str(value)
