"""Hol Horse and Emperor: a fast bullet that goes out when he is hit; a slower one steered
in flight by the free aim while he keeps moving; "Gun beats sword." charging the next
starred move; the bottle whose puddle hides Hanged Man; his grab; the ladies."""

import pytest
from helpers import NONE, hold, kinds, make_duel, press, run, run_held, run_until, walk

from jojo_arena.engine.actions import InputFrame


def _aim(x: float, y: float, move=(0.0, 0.0), actions=()) -> InputFrame:
    """A step with the mouse on (x, y)."""
    return InputFrame(move, frozenset(), {a: 1 for a in actions}, cursor=(x, y))


def test_you_lose_loser_is_a_fast_bullet_that_goes_out_if_he_is_hit():
    match = make_duel("hol_horse", "mannequin_red", p1=(60, 100), p2=(380, 100))
    run(match, 16, p1=press("special"))
    assert match.projectiles
    shot = match.projectiles[0]
    assert shot.defn.fragile and shot.velocity.length() >= 6


def test_his_bullet_turns_where_he_aims_while_he_keeps_walking():
    match = make_duel("hol_horse", "mannequin_red", p1=(60, 100), p2=(380, 30))
    hol = match.fighters[0]
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_until(match, lambda m: m.projectiles, 40)
    shot = match.projectiles[0]
    start, y0 = shot.pos.copy(), hol.pos.y
    for _ in range(40):
        match.step((_aim(shot.pos.x + 30, 190, move=(0.0, -1.0)), NONE))
    assert shot.alive and shot.pos.y > start.y + 15  # it turned down, toward the aim
    assert hol.pos.y < y0 - 10  # and he walked up all the while


def test_with_no_free_aim_his_bullet_flies_straight():
    match = make_duel("hol_horse", "mannequin_red", p1=(60, 100), p2=(380, 30))
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_until(match, lambda m: m.projectiles, 40)
    shot = match.projectiles[0]
    heading = shot.velocity.copy()
    run(match, 20)
    assert (shot.velocity - heading).length() < 1e-6


def test_gun_beats_sword_charges_the_next_starred_move_once():
    match = make_duel("hol_horse", "mannequin_red", p1=(60, 100), p2=(380, 100))
    hol = match.fighters[0]
    kit = hol.kit

    def total(name: str) -> int:
        shot = kit.move("base", name).projectile
        return shot.damage * shot.count * shot.waves

    assert total("special_boosted") > total("special")  # two bullets
    match.step((press("stand"), NONE))
    assert hol.attack is not None and hol.attack.move.name == "style"
    run_until(match, lambda m: hol.can_act(), 120)
    assert hol.buff is not None and hol.buff.charge
    match.step((press("special"), NONE))
    assert hol.attack.move.name == "special_boosted" and hol.buff is None
    run_until(match, lambda m: hol.can_act(), 120)
    match.step((press("special"), NONE))
    assert hol.attack.move.name == "special"  # spent: the next one is plain again


def test_the_bottle_leaves_a_puddle_where_he_aims_and_hanged_man_strikes_from_it():
    match = make_duel("hol_horse", "mannequin_red", p1=(60, 100), p2=(300, 100))
    dummy = match.fighters[1]
    match.step((_aim(200, 100, move=(1.0, 0.0), actions=("heavy",)), NONE))
    run_until(match, lambda m: m.traps, 60)
    assert abs(match.traps[0].pos.x - 200) < 2
    assert match.fighters[0].pos.x < 70  # thrown there: he does not go there himself
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 240, p2=walk(-1))


def test_now_ive_got_ya_is_a_grab_through_the_guard():
    match = make_duel("hol_horse", "mannequin_red", p1=(150, 100), p2=(172, 100))
    dummy = match.fighters[1]
    match.step((press("heavy"), hold("guard")))
    run_held(match, 40, p2=hold("guard"))
    assert dummy.hp < dummy.max_hp


def test_hol_horse_loves_the_ladies():
    hol = make_duel("hol_horse", "lisa_lisa").fighters[0]
    assert hol.passive_on and hol.damage_dealt_mult == pytest.approx(1.1)
    hol.gain_hh(10)
    assert hol.hh == pytest.approx(9)  # his Heart Heat comes a little slower
    assert not make_duel("hol_horse", "jotaro_p3").fighters[0].passive_on


def test_eat_this_bullets_hit_again_and_again():
    match = make_duel("hol_horse", "mannequin_red", p1=(100, 100), p2=(190, 100))
    hol = match.fighters[0]
    hha = hol.kit.move("base", "hha")
    assert hha.boosted  # stronger with Gun beats sword
    hol.hh = match.rules.hh_bar
    events = run(match, 150, p1=press("heart_heat"))
    assert kinds(events).count("hit") >= 6


def test_hol_horse_is_gonna_kill_ya_shatters_bottles_all_round_into_its_cutscene():
    match = make_duel("hol_horse", "mannequin_red", p1=(150, 100), p2=(190, 100))
    hol = match.fighters[0]
    gha = hol.kit.move("base", "gha")
    assert gha.reach == 0 and gha.radius >= 45  # a shockwave all round him
    hol.hh = match.rules.hh_max
    events = run(match, 60, p1=press("heart_heat", move=(1.0, 0.0)))
    assert match.cutscene is not None and match.cutscene.name == "emperor_hanged_man"
    assert "cutscene_start" in kinds(events)
