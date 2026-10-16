"""Speedwagon: the bladed hat comes back like a boomerang, the cheer heals, and he
withdraws coolly."""

from helpers import NONE, hold, make_duel, press, run_held, run_until

from jojo_arena.combat.fighter import State


def test_the_bladed_hat_comes_back_to_his_hand():
    match = make_duel("speedwagon", "mannequin_red", p1=(100, 100), p2=(160, 100))
    dummy = match.fighters[1]
    match.step((press("special"), NONE))
    run_until(match, lambda m: m.projectiles, 30)
    events = run_until(match, lambda m: not m.projectiles, 200)
    assert dummy.hp < dummy.max_hp  # it cut on the way out...
    assert any(e.kind == "catch" for e in events)  # ...and he caught it


def test_a_boomerang_hits_only_once():
    match = make_duel("speedwagon", "mannequin_red", p1=(100, 100), p2=(150, 100))
    dummy = match.fighters[1]
    hat = match.fighters[0].kit.move("base", "special").projectile
    match.step((press("special"), NONE))
    run_until(match, lambda m: m.projectiles, 30)
    run_until(match, lambda m: not m.projectiles, 200)
    assert dummy.max_hp - dummy.hp == hat.damage


def test_his_cheer_heals_while_he_poses():
    match = make_duel("speedwagon", "mannequin_red", p2=(300, 100))
    speedwagon = match.fighters[0]
    speedwagon.hp = 500
    run_held(match, 120, p1=hold("pose"))
    assert speedwagon.state == State.POSE
    assert speedwagon.hp >= 500 + speedwagon.kit.pose_heal_per_s * 2 - 1  # 2 s of cheering


def test_speedwagon_withdraws_coolly():
    match = make_duel("speedwagon", "mannequin_red", p1=(200, 100), p2=(240, 100))
    speedwagon = match.fighters[0]
    speedwagon.hh = match.rules.hh_max
    speedwagon.hp = 500
    start = speedwagon.pos.x
    match.step((press("heart_heat", move=(1.0, 0.0)), NONE))
    run_held(match, match.rules.super_freeze_f + 30)
    assert speedwagon.invincible and speedwagon.pos.x < start - 20  # backing away
    run_held(match, 90)
    assert speedwagon.hp > 500
