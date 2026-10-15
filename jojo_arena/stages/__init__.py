"""Arenas: layout data and interactive elements."""

from __future__ import annotations

from pathlib import Path

from jojo_arena.stages.base import StageDef, load_stage_def

_DIR = Path(__file__).parent

# Explicit list (no dynamic import) so PyInstaller bundles every stage.
STAGE_IDS = ("cairo_night",)


def load_stage(stage_id: str) -> StageDef:
    if stage_id not in STAGE_IDS:
        raise KeyError(f"unknown stage '{stage_id}'")
    return load_stage_def(_DIR / f"{stage_id}.toml", stage_id)


def stage_renderer(stage: StageDef):
    from jojo_arena.stages.cairo_night import CairoNightRenderer

    renderers = {"cairo_night": CairoNightRenderer}
    return renderers[stage.id](stage)
