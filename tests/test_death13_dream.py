"""Death 13's dream: Death 13 walks the arena on its own to whoever is nearest, raises its
scythe and sweeps; the fighters can beat it back, and it comes back later."""

import os

import pygame
from helpers import NONE, kinds, press

from jojo_arena.characters import get_fighter
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2
from jojo_arena.stages import STAGE_IDS, load_stage, stage_renderer
from jojo_arena.stages.base import StageOptions

RULES = load_rules()


def duel(at=((140, 150), (340, 150)), options=None) -> Match:
    stage = load_stage("death13_dream")
    match = Match(
        (get_fighter("jotaro_p3").kit, get_fighter("kakyoin").kit),
        RULES,
        stage.build_arena(options),
    )
    for fighter, spot in zip(match.fighters, at, strict=True):
        fighter.pos = Vec2(*spot)
    return match


def test_the_dream_is_an_arena_of_part_three_with_death_13():
    assert "death13_dream" in STAGE_IDS
    stage = load_stage("death13_dream")
    assert stage.part == 3 and stage.has_events and stage.roamers


def test_death_13_comes_to_the_nearest_and_its_scythe_comes_down():
    match = duel()
    events = []
    for _ in range(15 * 60):
        events += match.step((NONE, NONE))
        if "roamer_swing" in kinds(events):
            break
    assert "roamer_windup" in kinds(events) and "roamer_swing" in kinds(events)
    assert any(f.hp < f.max_hp for f in match.fighters)


def test_beaten_down_it_is_gone_a_while_then_comes_back():
    match = duel(at=((240, 100), (400, 220)))
    roamer = match.arena.hazards.roamers[0]
    while not roamer.present:
        match.step((NONE, NONE))
    roamer.hp = 5
    roamer.pos = Vec2(258, 100)  # right in front of Jotaro
    events = []
    for _ in range(20):
        events += match.step((press("light"), NONE))
        if not roamer.present:
            break
    assert "roamer_banished" in kinds(events) and not roamer.present
    for _ in range(roamer.defn.banish_f + 1):
        match.step((NONE, NONE))
    assert roamer.present and roamer.hp == roamer.defn.hp


def test_no_death_13_with_the_events_off():
    match = duel(options=StageOptions(events=False))
    assert match.arena.hazards.roamers == []


def test_the_dream_draws():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    stage = load_stage("death13_dream")
    renderer = stage_renderer(stage)
    surface = pygame.Surface((480, 270))
    renderer.draw_background(surface)
    arena = stage.build_arena()
    for obstacle in arena.obstacles:
        renderer.draw_obstacle(surface, obstacle)
    renderer.draw_lights(surface, 10)
