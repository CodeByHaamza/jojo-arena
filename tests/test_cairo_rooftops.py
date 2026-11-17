"""The rooftops of Cairo: holes through the roof, the neon sign whose letters fall on
whoever is slammed into it, the clock tower and the water tower."""

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
    stage = load_stage("cairo_rooftops")
    match = Match((get_fighter(p1).kit, get_fighter(p2).kit), RULES, stage.build_arena())
    for fighter, spot in zip(match.fighters, at, strict=True):
        fighter.pos = Vec2(*spot)
    return match


def test_the_rooftops_are_an_arena_of_part_three_with_events():
    assert "cairo_rooftops" in STAGE_IDS
    stage = load_stage("cairo_rooftops")
    assert stage.part == 3 and stage.has_events


def test_its_props_are_the_clock_tower_and_the_water_tower():
    kinds = {o.kind for o in duel().arena.obstacles}
    assert {"clock_tower", "water_tower"} <= kinds


def test_knocked_into_a_hole_in_the_roof_hurts():
    match = duel(at=((103, 150), (300, 120)))
    jotaro = match.fighters[0]
    jotaro.take_hit(0, 20, Vec2(0, 6), False)  # thrown toward the hole below him
    for _ in range(30):
        match.step((NONE, NONE))
    assert jotaro.hp < jotaro.max_hp


def test_the_rooftops_draw(monkeypatch):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    stage = load_stage("cairo_rooftops")
    renderer = stage_renderer(stage)
    surface = pygame.Surface((480, 270))
    renderer.draw_background(surface)
    arena = stage.build_arena()
    renderer.draw_floor_details(surface, arena)
    for obstacle in arena.obstacles:
        renderer.draw_obstacle(surface, obstacle)
    renderer.draw_lights(surface, 10)
