"""Anubis, the sword that possesses whoever draws it: it remembers every blow it takes and
never loses twice to the same one, growing stronger and faster with each; its blade passes
through what stands in the way."""

from helpers import (
    NONE,
    OPEN_BOUNDS,
    crate,
    hold,
    kinds,
    make_duel,
    press,
    run,
    run_held,
    run_until,
)

from jojo_arena.characters import get_fighter
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2


def _struck_once(match):
    anubis = match.fighters[0]
    match.step((NONE, press("light")))  # one press: no chain
    run_until(match, lambda m: anubis.hp < anubis.max_hp, 40)
    run_until(match, lambda m: anubis.can_act() and match.fighters[1].can_act(), 120)


def test_a_blow_taken_once_is_remembered_and_parried_the_next_time():
    match = make_duel("anubis", "jotaro_p3", p1=(150, 100), p2=(172, 100))
    anubis = match.fighters[0]
    _struck_once(match)
    assert len(anubis.learned) == 1
    hp = anubis.hp
    jotaro = match.fighters[1]
    events = []
    match.step((NONE, press("light")))
    for _ in range(30):
        events += match.step((NONE, NONE))
        if "learned" in kinds(events):
            break
    assert anubis.hp == hp and "learned" in kinds(events)  # never twice
    assert jotaro.state.name == "HITSTUN"  # parried: thrown off balance


def test_each_blow_learned_makes_it_stronger_and_faster():
    match = make_duel("anubis", "jotaro_p3", p1=(150, 100), p2=(172, 100))
    anubis = match.fighters[0]
    speed, damage = anubis.walk_speed(), anubis.damage_dealt_mult
    _struck_once(match)
    assert anubis.walk_speed() > speed and anubis.damage_dealt_mult > damage


def test_the_thrown_blade_passes_through_a_crate():
    arena = Arena(OPEN_BOUNDS, (Vec2(60, 100), Vec2(200, 100)), [crate(120, 94)])
    kits = (get_fighter("anubis").kit, get_fighter("mannequin_red").kit)
    match = Match(kits, load_rules(), arena)
    dummy = match.fighters[1]
    match.step((press("special"), NONE))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 90)
    assert not arena.obstacles[0].broken  # untouched: the blade went through it


def test_the_blade_goes_through_a_guard():
    match = make_duel("anubis", "mannequin_red", p1=(150, 100), p2=(176, 100))
    dummy = match.fighters[1]
    match.step((press("heavy"), hold("guard")))
    run_held(match, 40, p2=hold("guard"))
    assert dummy.hp < dummy.max_hp


def test_never_lose_twice_answers_a_blow_at_once():
    match = make_duel("anubis", "jotaro_p3", p1=(150, 100), p2=(172, 100))
    anubis, jotaro = match.fighters
    anubis.hh = match.rules.hh_bar
    match.step((press("heart_heat"), NONE))
    run_until(match, lambda m: anubis.countering, 90)
    events = run(match, 40, p2=press("light"))
    assert "counter" in kinds(events) and jotaro.hp < jotaro.max_hp


def test_its_ultimate_passes_through_everything_into_its_cutscene():
    match = make_duel("anubis", "mannequin_red", p1=(60, 100), p2=(140, 100))
    anubis = match.fighters[0]
    gha = anubis.kit.move("base", "gha")
    assert gha.unblockable and gha.shape == "line"
    anubis.hh = match.rules.hh_max
    events = run(match, 60, p1=press("heart_heat", move=(1.0, 0.0)))
    assert match.cutscene is not None and match.cutscene.name == "anubis_through"
    assert "cutscene_start" in kinds(events)
