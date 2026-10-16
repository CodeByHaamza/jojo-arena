"""Dawn: the light spreads across the floor, and it kills what should not see it."""

import pytest
from helpers import NONE, make_duel

from jojo_arena.combat.fighter import State
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2
from jojo_arena.stages import load_stage

RULES = load_rules()
MANSION = "joestar_mansion"


def at_dawn(p1: str = "dio_p1", p2: str = "jonathan", over: int = 0):
    """A fight in the mansion, wound forward to `over` frames after dawn breaks."""
    match = make_duel(p1, p2)
    stage = load_stage(MANSION)
    match.arena = stage.build_arena()
    match.tick = match.arena.sun_after_f + over
    return match


def in_the_light(match, fighter_index: int = 0) -> None:
    """Stand that fighter in the middle of the first beam."""
    patch = match.arena.sun_patch(match.arena.sun_windows[0], 0.0)
    match.fighters[fighter_index].pos = Vec2(patch.center.x, patch.center.y)


def step(match, frames: int) -> list:
    events = []
    for _ in range(frames):
        events += match.step((NONE, NONE))
    return events


# The light itself -------------------------------------------------------------------------


def test_the_beams_lengthen_across_the_floor_as_the_sun_climbs():
    arena = load_stage(MANSION).build_arena()
    window = arena.sun_windows[0]
    dawn = arena.sun_patch(window, 0.0)
    noon = arena.sun_patch(window, 1.0)
    assert dawn.h == pytest.approx(window.h)  # at first, just under the window
    assert noon.h > dawn.h * 2  # then it reaches out
    assert noon.bottom >= arena.bounds.rect.bottom - 1  # all the way to the far wall
    assert noon.w > dawn.w  # and it widens a little


def test_the_far_side_of_the_room_is_safe_at_first_and_not_for_long():
    arena = load_stage(MANSION).build_arena()
    far = Vec2(arena.sun_windows[0].center.x, arena.bounds.rect.bottom - 14)
    assert not arena.in_sun(far, 0.0)
    assert arena.in_sun(far, 1.0)


def test_the_spread_runs_from_dawn_to_full_light_and_stops_there():
    arena = load_stage(MANSION).build_arena()
    assert arena.sun_spread(arena.sun_after_f - 60) == 0.0
    assert arena.sun_spread(arena.sun_after_f) == 0.0
    half = arena.sun_after_f + arena.sun_spread_f // 2
    assert 0.3 < arena.sun_spread(half) < 0.7
    assert arena.sun_spread(arena.sun_after_f + arena.sun_spread_f * 3) == 1.0


# What it does to the undead ---------------------------------------------------------------


def test_the_living_can_stand_in_it_all_day():
    match = at_dawn(p1="jonathan", p2="speedwagon")
    in_the_light(match)
    hp = match.fighters[0].hp
    step(match, 300)
    assert match.fighters[0].hp == hp


def test_a_vampire_caught_in_the_open_burns_and_goes_down():
    match = at_dawn(p1="dio_p1")
    dio = match.fighters[0]
    in_the_light(match)
    events = step(match, 60 * 24)  # the sun is up, he has nowhere to go
    assert dio.blood == 0  # the blood boils away first
    assert any(e.kind == "sunburn" for e in events)
    assert dio.state == State.KO, dio.hp


def test_it_burns_faster_the_longer_he_stays_in_it():
    match = at_dawn(p1="dio_p1")
    dio = match.fighters[0]
    dio.blood = 0  # already dry: straight to burning
    in_the_light(match)
    step(match, 60)
    first = dio.max_hp - dio.hp
    step(match, 60)
    second = (dio.max_hp - dio.hp) - first
    assert second > first * 1.4, (first, second)


def test_stepping_out_of_the_light_cools_him_down():
    match = at_dawn(p1="dio_p1")
    dio = match.fighters[0]
    dio.blood = 0
    in_the_light(match)
    step(match, 120)
    assert dio.sun_f > 0
    dio.pos = Vec2(24, 240)  # into the shadow of the far corner
    step(match, 120)
    assert dio.sun_f == 0 and not dio.in_sun


def test_a_zombie_burns_the_same_way():
    match = at_dawn(p1="bruford")
    in_the_light(match)
    hp = match.fighters[0].hp
    step(match, 300)
    assert match.fighters[0].hp < hp


def test_nothing_burns_before_dawn():
    match = make_duel("dio_p1", "jonathan")
    match.arena = load_stage(MANSION).build_arena()
    match.tick = 0
    in_the_light(match)
    hp = match.fighters[0].hp
    step(match, 120)
    assert match.fighters[0].hp == hp and not match.sun_active


def test_an_arena_without_windows_never_sees_the_sun():
    arena = load_stage("cairo_night").build_arena()
    assert not arena.sun_windows
    assert arena.sun_spread(10**6) == 0.0
    assert not arena.in_sun(Vec2(100, 100), 1.0)


def test_stopped_time_holds_the_burn_exactly_where_it_was():
    match = at_dawn(p1="dio_p1")
    dio = match.fighters[0]
    dio.blood = 0
    in_the_light(match)
    step(match, 60)
    burning, hp = dio.sun_f, dio.hp
    dio.frozen = True  # caught in someone else's stopped time, out of the light
    dio.pos = Vec2(24, 240)
    step(match, 60)
    assert dio.sun_f == burning and dio.hp == hp
