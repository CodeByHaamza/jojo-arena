"""The Cairo bridge: DIO's knives in stopped time on whoever's turn it is - unless DIO is
the one fighting - and the hole torn in the deck."""

import os

import pygame
from helpers import NONE

from jojo_arena.characters import get_fighter
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2
from jojo_arena.stages import STAGE_IDS, load_stage, stage_renderer

RULES = load_rules()


def duel(p1="jotaro_p3", p2="kakyoin", at=((140, 150), (340, 150))) -> Match:
    stage = load_stage("cairo_bridge")
    match = Match((get_fighter(p1).kit, get_fighter(p2).kit), RULES, stage.build_arena())
    for fighter, spot in zip(match.fighters, at, strict=True):
        fighter.pos = Vec2(*spot)
    return match


def test_the_bridge_is_an_arena_of_part_three_with_events():
    assert "cairo_bridge" in STAGE_IDS
    stage = load_stage("cairo_bridge")
    assert stage.part == 3 and stage.has_events


def test_the_knives_come_down_on_a_fighter():
    match = duel()
    hurt = False
    for _ in range(20 * 60):
        match.step((NONE, NONE))
        if any(f.hp < f.max_hp for f in match.fighters):
            hurt = True
            break
    assert hurt


def test_no_knives_while_dio_is_fighting():
    match = duel(p1="dio_p3")
    for _ in range(20 * 60):
        match.step((NONE, NONE))
    assert all(f.hp == f.max_hp for f in match.fighters)


def test_knocked_into_the_hole_in_the_deck_hurts():
    match = duel(at=((240, 120), (300, 200)))
    jotaro = match.fighters[0]
    jotaro.take_hit(0, 20, Vec2(0, -6), False)  # thrown back toward the hole
    for _ in range(30):
        match.step((NONE, NONE))
    assert jotaro.hp < jotaro.max_hp


def test_the_bridge_draws(monkeypatch):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    stage = load_stage("cairo_bridge")
    renderer = stage_renderer(stage)
    surface = pygame.Surface((480, 270))
    renderer.draw_background(surface)
    arena = stage.build_arena()
    renderer.draw_floor_details(surface, arena)
    for obstacle in arena.obstacles:
        renderer.draw_obstacle(surface, obstacle)
    renderer.draw_lights(surface, 10)
