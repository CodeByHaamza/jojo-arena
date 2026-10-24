"""Avdol: the ankh that sets alight, the Variation laid where he aims, Red Bind through
the guard, the Flaming Detector that hunts, the counter, and Crossfire Hurricane
Special."""

from helpers import NONE, hold, kinds, make_duel, press, run, run_held, run_until

from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Vec2

GHA = press("heart_heat", move=(1.0, 0.0))


def _stand(match) -> None:
    avdol = match.fighters[0]
    match.step((press("stand"), NONE))
    run_until(match, lambda m: avdol.stance == "stand", 30)


def test_crossfire_hurricane_sets_the_opponent_alight():
    match = make_duel("avdol", "mannequin_red", p1=(80, 100), p2=(200, 100))
    dummy = match.fighters[1]
    events = run(match, 80, p1=press("special"))
    assert "ignite" in kinds(events)
    hit_at = dummy.hp
    assert hit_at < dummy.max_hp
    # The blow is over, and still he burns.
    run(match, 60)
    assert dummy.hp < hit_at


def test_the_variation_is_laid_where_he_aims_and_erupts_under_whoever_steps_on_it():
    match = make_duel("avdol", "mannequin_red", p1=(80, 100), p2=(320, 100))
    avdol, dummy = match.fighters
    aim = InputFrame((1.0, 0.0), frozenset(), {"special": 1}, cursor=(180.0, 140.0))
    run(match, 40, p1=aim)
    assert len(match.traps) == 1
    trap = match.traps[0]
    assert trap.pos.distance_to(Vec2(180, 140)) < 2  # on the aimed point, not ahead of him
    dummy.pos = Vec2(180, 140)
    events = run(match, 20)
    assert "trap_triggered" in kinds(events)
    assert dummy.hp < dummy.max_hp and dummy.fire_f > 0


def test_the_variation_cannot_be_laid_further_than_its_reach():
    match = make_duel("avdol", "mannequin_red", p1=(40, 100), p2=(380, 100))
    avdol = match.fighters[0]
    far = InputFrame((1.0, 0.0), frozenset(), {"special": 1}, cursor=(390.0, 100.0))
    run(match, 40, p1=far)
    reach = avdol.kit.move("base", "special_alt").trap.distance
    assert match.traps[0].pos.distance_to(avdol.pos) <= reach + 1


def test_red_bind_goes_through_the_guard_and_burns():
    match = make_duel("avdol", "mannequin_red", p1=(100, 100), p2=(150, 100))
    dummy = match.fighters[1]
    match.step((press("heavy", move=(1.0, 0.0)), hold("guard")))
    run_held(match, 40, p2=hold("guard"))
    assert dummy.hp < dummy.max_hp
    assert dummy.fire_f > 0


def test_the_flaming_detector_hunts_a_moving_target():
    match = make_duel("avdol", "mannequin_red", p1=(80, 100), p2=(220, 100))
    dummy = match.fighters[1]
    _stand(match)
    match.step((press("special"), NONE))
    walk = InputFrame((0.0, 1.0))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 220, p2=walk)


def test_now_is_his_chance_the_counter_answers_with_fire():
    match = make_duel("avdol", "mannequin_red", p1=(150, 100), p2=(172, 100))
    avdol, dummy = match.fighters
    _stand(match)
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_held(match, 6)
    assert avdol.countering
    events = match.step((NONE, press("light")))
    events += run_held(match, 24)
    assert "counter" in kinds(events)
    assert dummy.hp < dummy.max_hp and dummy.fire_f > 0


def test_crossfire_hurricane_special_closes_the_ring_in_a_cutscene():
    match = make_duel("avdol", "mannequin_red", p1=(100, 100), p2=(160, 100))
    match.fighters[0].hh = match.rules.hh_max
    events = run(match, 60, p1=GHA)
    assert match.cutscene is not None and match.cutscene.name == "crossfire_special"
    assert "cutscene_start" in kinds(events)
    events = run(match, match.cutscene.frames_left + 2)
    assert "cutscene_end" in kinds(events)
    assert match.fighters[1].fire_f > 0
