"""The game's music: one original chiptune loop per screen family, rendered in code."""

from __future__ import annotations

from jojo_arena.engine.music import Track

NATURAL_MINOR = (0, 2, 3, 5, 7, 8, 10)
HARMONIC_MINOR = (0, 2, 3, 5, 7, 8, 11)
PHRYGIAN_DOMINANT = (0, 1, 4, 5, 7, 8, 10)

TRACKS = {
    # Menus: an upbeat minor riff.
    "menu": Track(
        tempo=138,
        root=57,  # A
        scale=NATURAL_MINOR,
        progression=(0, 5, 2, 6),
        motif=((0, 0, 3), (3, 2, 1), (4, 4, 2), (6, 2, 2), (8, 7, 4), (12, 4, 2), (14, 2, 2)),
    ),
    # Cairo at night: Middle-Eastern colors, a winding lead.
    "cairo_night": Track(
        tempo=126,
        root=50,  # D
        scale=PHRYGIAN_DOMINANT,
        progression=(0, 0, 1, 0),
        motif=(
            (0, 0, 2),
            (2, 1, 2),
            (4, 2, 2),
            (6, 1, 2),
            (8, 0, 4),
            (12, 4, 1),
            (13, 3, 1),
            (14, 2, 2),
        ),
    ),
    # The Joestar mansion: a gothic organ over harmonic minor.
    "joestar_mansion": Track(
        tempo=108,
        root=52,  # E
        scale=HARMONIC_MINOR,
        progression=(0, 5, 3, 4),
        motif=((0, 4, 4), (4, 3, 2), (6, 2, 2), (8, 6, 6), (14, 7, 2)),
        lead_wave="organ",
    ),
}


def track_for_stage(stage_id: str) -> str:
    """The music of an arena (the menu theme when it has none of its own)."""
    return stage_id if stage_id in TRACKS else "menu"
