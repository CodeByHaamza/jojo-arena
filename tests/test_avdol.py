"""Avdol as in ASBR: the ankh that sets alight and goes out when he is struck, the
Variation laid where he aims, Red Bind (the throw) through the guard, the ropes thrown at
range that bind, the fire breath, the Flaming Detector that hunts, the punch that takes a
blow to give one, the kick that flies, and Crossfire Hurricane Special."""

from helpers import NONE, hold, kinds, make_duel, press, run, run_held, run_until

from jojo_arena.combat.fighter import State
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
    assert "status_burn" in kinds(events)
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
    assert dummy.hp < dummy.max_hp and "burn" in dummy.statuses


def test_the_variation_cannot_be_laid_further_than_its_reach():
    match = make_duel("avdol", "mannequin_red", p1=(40, 100), p2=(380, 100))
    avdol = match.fighters[0]
    far = InputFrame((1.0, 0.0), frozenset(), {"special": 1}, cursor=(390.0, 100.0))
    run(match, 40, p1=far)
    reach = avdol.kit.move("base", "special_alt").trap.distance
    assert match.traps[0].pos.distance_to(avdol.pos) <= reach + 1


def test_red_bind_the_throw_goes_through_the_guard_and_burns():
    match = make_duel("avdol", "mannequin_red", p1=(100, 100), p2=(124, 100))
    dummy = match.fighters[1]
    match.step((press("heavy"), hold("guard")))
    run_held(match, 30, p2=hold("guard"))
    assert dummy.hp < dummy.max_hp
    assert "burn" in dummy.statuses


def test_the_ropes_thrown_at_range_are_blocked_by_a_guard():
    match = make_duel("avdol", "mannequin_red", p1=(100, 100), p2=(150, 100))
    dummy = match.fighters[1]
    match.step((press("heavy", move=(1.0, 0.0)), hold("guard")))
    avdol = match.fighters[0]
    move = avdol.kit.move("base", "heavy_alt")
    events = run_held(match, 40, p2=hold("guard"))
    assert "block" in kinds(events)
    # Only what a guard lets through: no fire, and nowhere near the full blow.
    assert "burn" not in dummy.statuses
    assert dummy.max_hp - dummy.hp < move.damage * 2


def test_the_ropes_thrown_at_range_bind_where_the_opponent_stands():
    match = make_duel("avdol", "mannequin_red", p1=(100, 100), p2=(150, 100))
    avdol, dummy = match.fighters
    move = avdol.kit.move("base", "heavy_alt")
    assert move.shape == "line" and not move.unblockable and move.hits == 3
    stood = dummy.pos.copy()
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_until(match, lambda m: avdol.attack is not None and avdol.attack.hits_done == 3, 60)
    run_held(match, 12)
    # Tied up: hurt, burning, still stunned, and not thrown anywhere.
    assert dummy.hp < dummy.max_hp and "burn" in dummy.statuses
    assert dummy.state == State.HITSTUN
    assert dummy.pos.distance_to(stood) < 3


def test_crossfire_hurricane_goes_out_when_avdol_is_struck():
    match = make_duel("avdol", "mannequin_red", p1=(40, 100), p2=(360, 100))
    avdol, dummy = match.fighters
    match.step((press("special"), NONE))
    run_until(match, lambda m: m.projectiles, 40)
    avdol.take_hit(10, 20, Vec2(0, 0), False)
    events = run_held(match, 2)
    assert not match.projectiles
    assert "trap_popped" in kinds(events)
    run_held(match, 120)
    assert dummy.hp == dummy.max_hp


def test_the_flaming_detector_goes_out_when_avdol_is_struck():
    match = make_duel("avdol", "mannequin_red", p1=(40, 100), p2=(360, 100))
    avdol = match.fighters[0]
    _stand(match)
    match.step((press("special"), NONE))
    run_until(match, lambda m: m.projectiles, 40)
    avdol.take_hit(10, 20, Vec2(0, 0), False)
    run_held(match, 2)
    assert not match.projectiles


def test_magicians_red_breathes_fire_in_four_hits():
    match = make_duel("avdol", "mannequin_red", p1=(150, 100), p2=(176, 100))
    avdol, dummy = match.fighters
    breath = avdol.kit.move("stand", "light3")
    assert breath.hits == 4 and breath.status == "burn"
    _stand(match)
    for _ in range(3):  # slap, kick, fire breath: the same button, each once the last lands
        match.step((press("light"), NONE))
        run_held(match, 14)
    run_held(match, 30)
    assert "burn" in dummy.statuses


def test_the_flaming_detector_hunts_a_moving_target():
    match = make_duel("avdol", "mannequin_red", p1=(80, 100), p2=(220, 100))
    dummy = match.fighters[1]
    _stand(match)
    match.step((press("special"), NONE))
    walk = InputFrame((0.0, 1.0))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 220, p2=walk)


def test_now_is_his_chance_the_punch_comes_down_on_its_own():
    match = make_duel("avdol", "mannequin_red", p1=(150, 100), p2=(172, 100))
    avdol, dummy = match.fighters
    _stand(match)
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    startup = avdol.attack.move.startup_f
    run_held(match, startup - 2)
    assert dummy.hp == dummy.max_hp  # still winding up
    run_held(match, 12)
    assert dummy.hp < dummy.max_hp and "burn" in dummy.statuses


def test_now_is_his_chance_a_blow_taken_sets_the_punch_off():
    match = make_duel("avdol", "mannequin_red", p1=(150, 100), p2=(172, 100))
    avdol, dummy = match.fighters
    _stand(match)
    match.step((press("heavy", move=(1.0, 0.0)), press("light")))
    startup = avdol.attack.move.startup_f
    events, steps = [], 0
    while avdol.hp == avdol.max_hp:
        events += match.step((NONE, NONE))
        steps += 1
    assert steps < startup - 5  # struck long before the punch was due...
    assert avdol.state == State.ATTACK and avdol.attack.active  # ...and here it is
    events += run_held(match, 8)
    assert "armor" in kinds(events)
    assert dummy.hp < dummy.max_hp


def test_give_me_four_wishes_flies_forward():
    match = make_duel("avdol", "mannequin_red", p1=(100, 100), p2=(160, 100))
    avdol, dummy = match.fighters
    assert avdol.kit.move("base", "hha").shape == "line"
    avdol.hh = match.rules.hh_bar
    match.step((press("heart_heat"), NONE))
    run_held(match, 40)
    assert dummy.hp < dummy.max_hp  # 60 px away: a blow on the spot would have missed


def test_crossfire_hurricane_special_closes_the_ring_in_a_cutscene():
    match = make_duel("avdol", "mannequin_red", p1=(100, 100), p2=(160, 100))
    match.fighters[0].hh = match.rules.hh_max
    events = run(match, 60, p1=GHA)
    assert match.cutscene is not None and match.cutscene.name == "crossfire_special"
    assert "cutscene_start" in kinds(events)
    events = run(match, match.cutscene.frames_left + 2)
    assert "cutscene_end" in kinds(events)
    assert "burn" in match.fighters[1].statuses
