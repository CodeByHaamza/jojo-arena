"""Zombies (Part 1): Bruford's hair, Tarkus's Chain Neck Ring, Hamon and sunlight on them,
and their ultimates."""

import pygame
import pytest
from helpers import NONE, OPEN_BOUNDS, make_duel, press, run_held, run_until, walk

from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Rect, Vec2


def test_the_grasping_hair_pulls_the_opponent_in_and_drinks():
    match = make_duel("bruford", "mannequin_red", p1=(120, 100), p2=(190, 100))
    bruford, dummy = match.fighters
    bruford.hp = 700
    match.step((press("special"), NONE))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 40)
    run_held(match, 20)
    assert dummy.pos.x < 190 - 10  # drawn toward Bruford
    assert bruford.hp > 700


def test_hamon_burns_a_zombie_twice_as_hard():
    def scarlet_on(victim_id: str) -> int:
        match = make_duel("jonathan", victim_id, p2=(172, 100))
        jonathan, victim = match.fighters
        jonathan.hamon = 100
        match.step((press("special"), NONE))
        run_until(match, lambda m: victim.hp < victim.max_hp, 80)
        return victim.max_hp - victim.hp

    assert abs(scarlet_on("tarkus") - 2 * scarlet_on("jotaro_p3")) <= 2


def test_the_chain_neck_ring_locks_both_fighters_in():
    match = make_duel("tarkus", "mannequin_red", p1=(150, 100), p2=(220, 100))
    tarkus, dummy = match.fighters
    ring = tarkus.kit.move("base", "special")
    match.step((press("special"), NONE))
    events = run_until(match, lambda m: m.arena.cage is not None, 40)
    assert any(e.kind == "cage" for e in events)
    cage = match.arena.cage
    run_held(match, 90, p2=walk(1.0, 0.0))  # it tries to run away
    room = cage.radius - match.rules.body_radius
    assert (dummy.pos - cage.center).length() <= room + 0.5
    events = run_held(match, ring.cage_f)
    assert match.arena.cage is None and any(e.kind == "cage_end" for e in events)
    start = dummy.pos.x
    run_held(match, 60, p2=walk(1.0, 0.0))
    assert dummy.pos.x > start + 20  # free again


def test_the_sun_burns_zombies_at_once():
    arena = Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(330, 100)), [])
    arena.sun_windows = [Rect(120, 70, 60, 60)]
    match = Match(
        (get_fighter("bruford").kit, get_fighter("mannequin_red").kit), load_rules(), arena
    )
    bruford = match.fighters[0]
    run_held(match, 30)
    assert bruford.hp < bruford.max_hp  # no blood to boil away first


@pytest.mark.parametrize("user_id", ["bruford", "tarkus"])
def test_the_zombie_ultimates_play_to_the_end(user_id, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    from jojo_arena.stages import load_stage
    from jojo_arena.ui.fight_view import FightView

    stage = load_stage("joestar_mansion")
    defs = [f for f in load_roster() if f.id in (user_id, "jonathan")]
    defs.sort(key=lambda f: f.id != user_id)
    match = Match((defs[0].kit, defs[1].kit), load_rules(), stage.build_arena())
    user, jonathan = match.fighters
    jonathan.pos = user.pos + Vec2(26, 0)
    user.hh = match.rules.hh_max
    view = FightView(stage, defs)
    surface = pygame.Surface((480, 270))
    started = False
    for i in range(400):
        frame = press("heart_heat", move=(1.0, 0.0)) if i == 0 else NONE
        events = match.step((frame, NONE))
        view.on_events(events, match)
        view.update(match)
        view.draw(surface, match)
        started = started or match.cutscene is not None
        if started and match.cutscene is None:
            break
    assert started
    finish = user.kit.shared_moves["gha"].finish_damage
    assert jonathan.hp < jonathan.max_hp - finish * 0.9
    pygame.display.quit()
