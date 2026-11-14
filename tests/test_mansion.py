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
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.input import InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.stages import (
    REACHED_IDS,
    STAGE_IDS,
    load_stage,
    stage_for_part,
    stage_renderer,
)
from jojo_arena.ui.fight_view import sun_amount
from jojo_arena.ui.setup_scene import SetupScene
from jojo_arena.ui.stage_scene import StageSelectScene


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


@pytest.mark.parametrize("stage_id", STAGE_IDS + REACHED_IDS)
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


def test_the_arena_screen_opens_on_the_home_ground_of_player_one(ctx):
    arenas = StageSelectScene(ctx, "versus", ("jonathan", "jotaro_p3"))
    assert arenas.choice == "joestar_mansion"
    arenas = StageSelectScene(ctx, "versus", ("joseph_p2", "caesar"))
    assert arenas.choice == "swiss_castle"
    arenas = StageSelectScene(ctx, "versus", ("jotaro_p3", "jonathan"))
    assert arenas.choice == "cairo_night" and arenas.stage_id == "cairo_night"
    arenas.index = arenas.choices.index("random")
    assert arenas.stage_id in STAGE_IDS  # the last entry draws one


def test_the_vs_screen_shows_the_arena_it_was_given(ctx):
    setup = SetupScene(ctx, fighter_ids=("jonathan", "jotaro_p3"), stage_id="swiss_castle")
    assert setup.stage_id == "swiss_castle" and setup.stage.part == 2
    assert all(item.key != "stage" for item in setup.menu.items)  # not chosen here anymore


def test_the_swiss_castle_is_the_arena_of_part_two():
    stage = load_stage("swiss_castle")
    assert stage.part == 2 and stage_for_part(2) == "swiss_castle"
    assert len(stage.sun_windows) == 4  # four windows: more light than the mansion
    assert stage.sun_spread_f > 0  # and the beams walk across the hall


def test_the_castle_leaves_an_undead_almost_nowhere_to_hide_at_full_sun():
    arena = load_stage("swiss_castle").build_arena()
    floor = arena.bounds.rect
    spots = [
        Vec2(x, y)
        for x in range(int(floor.left) + 4, int(floor.right) - 4, 6)
        for y in range(int(floor.top) + 4, int(floor.bottom) - 4, 6)
    ]
    at_dawn = sum(arena.in_sun(p, 0.0) for p in spots)
    at_noon = sum(arena.in_sun(p, 1.0) for p in spots)
    assert at_noon > at_dawn * 2  # the light really walks the floor
    assert at_noon > len(spots) * 0.6  # and by then most of the hall is lit
