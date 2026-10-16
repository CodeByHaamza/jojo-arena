"""Arenas: layout data and interactive elements."""

from __future__ import annotations

from pathlib import Path

from jojo_arena.stages.base import StageDef, load_stage_def

_DIR = Path(__file__).parent

# Explicit list (no dynamic import) so PyInstaller bundles every stage.
STAGE_IDS = ("joestar_mansion", "swiss_castle", "cairo_night")


def load_stage(stage_id: str) -> StageDef:
    if stage_id not in STAGE_IDS:
        raise KeyError(f"unknown stage '{stage_id}'")
    return load_stage_def(_DIR / f"{stage_id}.toml", stage_id)


def stage_for_part(part: int) -> str:
    """The arena of a JoJo part (where its fighters play by default), or the first one."""
    for stage_id in STAGE_IDS:
        if load_stage(stage_id).part == part:
            return stage_id
    return STAGE_IDS[0]


def stage_renderer(stage: StageDef):
    from jojo_arena.stages.cairo_night import CairoNightRenderer
    from jojo_arena.stages.joestar_mansion import JoestarMansionRenderer
    from jojo_arena.stages.swiss_castle import SwissCastleRenderer

    renderers = {
        "cairo_night": CairoNightRenderer,
        "joestar_mansion": JoestarMansionRenderer,
        "swiss_castle": SwissCastleRenderer,
    }
    return renderers[stage.id](stage)
