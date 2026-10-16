"""Young Joseph: grenades that roll then blow up, Hamon threads, the hidden plan, the
secret technique of running away, and "your next line is...!" """

from helpers import NONE, hold, kinds, make_duel, press, run_held, run_until

from jojo_arena.combat.fighter import State


def test_a_grenade_rolls_to_a_stop_then_blows_up():
    match = make_duel("joseph_p2", "mannequin_red", p1=(100, 100), p2=(150, 100))
    dummy = match.fighters[1]
    grenade = match.fighters[0].kit.move("base", "special_alt").projectile
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_until(match, lambda m: m.projectiles, 30)
    assert dummy.hp == dummy.max_hp  # rolling past is harmless...
    events = run_until(match, lambda m: not m.projectiles, 120)
    assert "explosion" in kinds(events)
    assert dummy.max_hp - dummy.hp == grenade.damage  # ...the blast is not


def test_a_grenade_far_away_hurts_nobody():
    match = make_duel("joseph_p2", "mannequin_red", p1=(100, 60), p2=(100, 260))
    dummy = match.fighters[1]
    match.step((press("special", move=(1.0, 0.0)), NONE))
    events = run_held(match, 120)
    assert "explosion" in kinds(events)
    assert dummy.hp == dummy.max_hp


def test_threads_trip_whoever_steps_on_them():
    match = make_duel("joseph_p2", "mannequin_red", p1=(100, 100), p2=(250, 100))
    dummy = match.fighters[1]
    match.step((press("heavy"), NONE))
    run_held(match, 30)
    assert len(match.traps) == 1
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 240, p2=hold(move=(-1.0, 0.0)))
    assert dummy.state == State.HITSTUN


def test_the_hidden_plan_blows_every_trap_and_one_under_the_opponent():
    match = make_duel("joseph_p2", "mannequin_red", p1=(100, 100), p2=(200, 100))
    joseph, dummy = match.fighters
    for _ in range(2):
        match.step((press("heavy"), NONE))
        run_held(match, 30)
    assert len(match.traps) == 2
    joseph.hh = match.rules.hh_max
    match.step((press("heart_heat", move=(1.0, 0.0)), NONE))
    events = run_held(match, match.rules.super_freeze_f + 60)
    assert not match.traps
    assert kinds(events).count("explosion") == 3  # two threads and the hidden grenade
    assert dummy.hp < dummy.max_hp


def test_the_secret_technique_runs_away_invincible():
    match = make_duel("joseph_p2", "mannequin_red", p1=(200, 100), p2=(240, 100))
    joseph = match.fighters[0]
    start = joseph.pos.x
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_held(match, 4)
    assert joseph.invincible
    run_held(match, 14)
    assert joseph.pos.x < start - 40


def test_he_calls_the_same_button_again_and_counters_it():
    match = make_duel("joseph_p2", "mannequin_red", p1=(150, 100), p2=(172, 100))
    joseph, dummy = match.fighters
    dummy.last_slot = "light"  # the dummy's last attack was a light blow
    run_held(match, 40, p1=hold("pose"))
    assert joseph.countering
    events = match.step((hold("pose"), press("light")))
    events += run_held(match, 20, p1=hold("pose"))
    assert "counter" in kinds(events) and "foreseen" in kinds(events)
    run_held(match, 40)
    assert joseph.hp == joseph.max_hp and dummy.hp < dummy.max_hp


def test_a_wrong_call_leaves_him_open():
    match = make_duel("joseph_p2", "mannequin_red", p1=(150, 100), p2=(172, 100))
    joseph, dummy = match.fighters
    dummy.last_slot = "special"  # he expects a special...
    run_held(match, 40, p1=hold("pose"))
    match.step((hold("pose"), press("light")))  # ...and gets a jab
    run_held(match, 30, p1=hold("pose"))
    assert joseph.hp < joseph.max_hp
