import pytest
from helpers import NONE, hold, kinds, make_match, press, run, run_held

from jojo_arena.combat.fighter import State

LIGHT = 35


def test_hitting_and_getting_hit_fill_heart_heat():
    match = make_match()
    run(match, 30, p1=press("light"))
    attacker, defender = match.fighters
    assert attacker.hh == pytest.approx(LIGHT * match.rules.hh_per_damage_dealt)
    assert defender.hh == pytest.approx(LIGHT * match.rules.hh_per_damage_taken)


def test_blocked_hits_give_half_the_heart_heat():
    match = make_match()
    run_held(match, 2, p2=hold("guard"))
    for i in range(30):
        match.step((press("light") if i == 0 else NONE, hold("guard")))
    rules = match.rules
    assert match.fighters[0].hh == pytest.approx(LIGHT * rules.hh_per_damage_dealt * 0.5)


def test_heart_heat_caps_at_three_bars():
    match = make_match()
    match.fighters[0].gain_hh(1000)
    assert match.fighters[0].hh == 300


def test_hha_needs_one_bar():
    match = make_match()
    match.fighters[0].hh = 99
    events = run(match, 5, p1=press("heart_heat"))
    assert "hha" not in kinds(events)
    assert match.fighters[0].state != State.ATTACK


def test_hha_spends_a_bar_freezes_time_and_hits_hard():
    match = make_match()
    attacker, defender = match.fighters
    attacker.hh = 150
    events = run(match, 1, p1=press("heart_heat"))
    assert "hha" in kinds(events)
    assert attacker.hh == pytest.approx(50)
    assert match.super_freeze > 0 and match.super_user == 0
    events = run(match, 90)
    assert "hit" in kinds(events)
    assert defender.max_hp - defender.hp >= 160


def test_hha_startup_is_invincible():
    match = make_match()
    match.fighters[1].hh = 100
    run(match, 1, p2=press("heart_heat"))
    run(match, match.super_freeze)
    run(match, 1, p1=press("light"))
    run(match, 6)
    assert match.fighters[1].hp == match.fighters[1].max_hp  # light went through


def test_flash_cancel_drops_the_attack_for_half_a_bar():
    match = make_match(p1=(100, 100), p2=(300, 100))
    fighter = match.fighters[0]
    fighter.hh = 60
    run(match, 3, p1=press("heavy"))
    events = run(match, 1, p1=press("guard"))
    assert "flash_cancel" in kinds(events)
    assert fighter.state == State.IDLE
    assert fighter.hh == pytest.approx(10)


def test_no_flash_cancel_without_meter():
    match = make_match(p1=(100, 100), p2=(300, 100))
    run(match, 3, p1=press("heavy"))
    events = run(match, 1, p1=press("guard"))
    assert "flash_cancel" not in kinds(events)
    assert match.fighters[0].state == State.ATTACK


def test_guard_pressed_just_before_an_attack_does_not_cancel_it():
    match = make_match(p1=(100, 100), p2=(300, 100))
    match.fighters[0].hh = 100
    match.step((press("guard"), NONE))
    match.step((press("light"), NONE))
    run(match, 3)
    assert match.fighters[0].state == State.ATTACK


def test_pose_charges_heart_heat_and_roots_in_place():
    match = make_match(p1=(100, 100), p2=(300, 100))
    fighter = match.fighters[0]
    run_held(match, 60, p1=hold("pose", move=(1.0, 0.0)))
    assert fighter.state == State.POSE
    assert fighter.hh == pytest.approx(20, abs=0.5)
    assert fighter.pos.x == 100
    run(match, 1)
    assert fighter.state == State.IDLE


def test_posing_fighter_cannot_guard():
    match = make_match()
    run_held(match, 2, p2=hold("pose"))  # strike a pose, then also hold guard
    for i in range(30):
        match.step((press("light") if i == 0 else NONE, hold("pose", "guard")))
    assert match.fighters[1].hp == match.fighters[1].max_hp - LIGHT


def test_resolve_boosts_damage_under_a_quarter_life():
    match = make_match()
    match.fighters[0].hp = 200
    events = run(match, 30, p1=press("light"))
    assert match.fighters[1].hp == match.fighters[1].max_hp - round(LIGHT * 1.15)
    assert "resolve" in kinds(events)


def test_stance_switch_changes_the_moveset():
    match = make_match()
    fighter = match.fighters[0]
    events = run(match, 1, p1=press("stand"))
    assert "stance_switch" in kinds(events)
    assert fighter.state == State.SWITCH
    run(match, 12)
    assert fighter.stance == "stand" and fighter.aura_active
    run(match, 30, p1=press("light"))
    assert match.fighters[1].hp == match.fighters[1].max_hp - 45
    run(match, 13, p1=press("stand"))
    assert fighter.stance == "base" and not fighter.aura_active


def test_stylish_evade_gives_heart_heat():
    match = make_match()
    run(match, 5, p1=press("light"))
    run(match, 1, p2=press("dash", move=(0.0, 1.0)))
    assert match.fighters[1].hh == pytest.approx(15)
