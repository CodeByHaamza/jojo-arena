"""The Joestar mansion (Part 1): dawn through the windows, the arena of each part, the
arena picked on the VS screen."""

import pygame
import pytest

from jojo_arena import controls
from jojo_arena.characters import get_fighter
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.context import GameContext
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.stages import STAGE_IDS, load_stage, stage_for_part, stage_renderer
from jojo_arena.ui.fight_view import sun_amount
from jojo_arena.ui.setup_scene import SetupScene


def test_dawn_comes_in_through_the_windows_late_in_the_round():
    stage = load_stage("joestar_mansion")
    assert stage.part == 1 and len(stage.sun_windows) == 3
    kits = (get_fighter("jonathan").kit, get_fighter("dio_p1").kit)
    match = Match(kits, load_rules(), stage.build_arena())
    assert not match.sun_active and sun_amount(match) == 0
    match.tick = stage.sun_after_f - 100
    assert not match.sun_active and 0 < sun_amount(match) < 0.3  # the windows glow first
    match.tick = stage.sun_after_f
    events = match.step((InputFrame(), InputFrame()))
    assert match.sun_active and any(e.kind == "dawn" for e in events)


def test_each_part_plays_in_its_own_arena():
    assert stage_for_part(1) == "joestar_mansion"
    assert stage_for_part(3) == "cairo_night"
    assert stage_for_part(9) == STAGE_IDS[0]  # no arena of its own yet


@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_every_arena_draws_at_night_and_at_dawn(stage_id, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    stage = load_stage(stage_id)
    renderer = stage_renderer(stage)
    surface = pygame.Surface((480, 270))
    arena = stage.build_arena()
    renderer.draw_background(surface)
    renderer.draw_floor_details(surface, arena)
    for obstacle in arena.obstacles:
        renderer.draw_obstacle(surface, obstacle)
        obstacle.damage(obstacle.max_hp)
    renderer.draw_floor_details(surface, arena)  # broken: debris
    if hasattr(renderer, "draw_sun"):
        renderer.draw_sun(surface, arena, 1.0, 1.0)
    renderer.draw_lights(surface, 30)
    pygame.display.quit()


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    config, _ = controls.parse_controls(None)
    context = GameContext(
        Display("test", (480, 270)), InputManager(), SceneManager(), config, tmp_path / "c.json"
    )
    yield context
    pygame.display.quit()


def test_the_vs_screen_picks_the_arena_of_player_one(ctx):
    setup = SetupScene(ctx, fighter_ids=("jonathan", "jotaro_p3"))
    assert setup.stage_id == "joestar_mansion"
    setup = SetupScene(ctx, fighter_ids=("jotaro_p3", "jonathan"))
    assert setup.stage_id == "cairo_night"
    setup.menu.item("stage").index = len(STAGE_IDS)  # at random
    assert setup.stage_id in STAGE_IDS
