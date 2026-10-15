"""Wave 1 mechanics with the real kits: Stands, rushes, time stop, traps, disarm, buffs."""

import pytest
from helpers import NONE, kinds, make_duel, press, run, run_held, run_until, walk

from jojo_arena.combat.fighter import State
from jojo_arena.combat.projectile import Projectile
from jojo_arena.engine.geometry import Vec2


def stand_out(fighter):
    fighter.stance = "stand"


# The Stand's body --------------------------------------------------------------------------


def test_a_hit_on_the_stand_hurts_its_user():
    match = make_duel("jotaro_p3", "dio_p3", p1=(150, 100), p2=(300, 100))
    jotaro = match.fighters[0]
    stand_out(jotaro)
    stand = jotaro.stand_pos()
    assert stand is not None and stand.distance_to(jotaro.pos) > 8
    knife = match.fighters[1].kit.move("base", "special").projectile
    # A knife flying at the Stand only, away from Jotaro's body.
    match.projectiles.append(Projectile(1, stand + Vec2(20, 0), Vec2(-knife.speed, 0), knife, 30))
    run(match, 10)
    assert jotaro.hp < jotaro.max_hp


def test_no_stand_body_while_it_is_called_back():
    match = make_duel("jotaro_p3", "dio_p3")
    assert match.fighters[0].stand_pos() is None
    assert len(match.fighters[0].hurtboxes()) == 1


# Moves -----------------------------------------------------------------------------------


def test_ora_rush_hits_six_times_and_sends_flying():
    match = make_duel("jotaro_p3", "mannequin_red")
    stand_out(match.fighters[0])
    events = run(match, 90, p1=press("heavy"))
    defender = match.fighters[1]
    assert kinds(events).count("hit") == 6
    assert defender.max_hp - defender.hp >= 6 * 18
    assert defender.pos.x > 230  # the last hit launched him


def test_special_with_a_direction_is_the_alternate_move():
    match = make_duel("jotaro_p3", "mannequin_red", p2=(300, 100))
    stand_out(match.fighters[0])
    match.step((press("special", move=(1.0, 0.0)), NONE))
    assert match.fighters[0].attack.move.name == "special_alt"  # Star Finger


def test_star_finger_reaches_mid_range():
    match = make_duel("jotaro_p3", "mannequin_red", p1=(150, 100), p2=(195, 100))
    stand_out(match.fighters[0])
    run(match, 30, p1=press("special", move=(1.0, 0.0)))
    assert match.fighters[1].hp == match.fighters[1].max_hp - 70


def test_lunge_carries_the_body_forward():
    match = make_duel("polnareff", "mannequin_red", p1=(100, 100), p2=(300, 100))
    run(match, 20, p1=press("special"))
    assert match.fighters[0].pos.x > 140


def test_vampire_grab_ignores_guard_and_drains_blood():
    match = make_duel("dio_p3", "mannequin_red")
    dio, victim = match.fighters
    dio.hp = 500
    run_held(match, 2, p2=walk(0, 0))
    for i in range(40):
        match.step((press("heavy") if i == 0 else NONE, press(hold=("guard",))))
    assert victim.hp == victim.max_hp - 70
    assert dio.hp == 500 + 35


def test_gha_takes_two_bars_and_hha_one():
    match = make_duel("jotaro_p3", "mannequin_red", p2=(300, 100))
    jotaro = match.fighters[0]
    jotaro.hh = 150
    run(match, 1, p1=press("heart_heat"))
    assert jotaro.attack.move.name == "hha" and jotaro.hh == pytest.approx(50)
    match = make_duel("jotaro_p3", "mannequin_red", p2=(300, 100))
    jotaro = match.fighters[0]
    jotaro.hh = 210
    events = run(match, 1, p1=press("heart_heat"))
    assert jotaro.attack.move.name == "gha" and "gha" in kinds(events)
    assert jotaro.hh == pytest.approx(10)


# Time stop ---------------------------------------------------------------------------------


def stop_time(match, who=0):
    """Press the time stop and run until stopped time has begun (flash included)."""
    stand_out(match.fighters[who])
    frames = [NONE, NONE]
    frames[who] = press("special")
    match.step(tuple(frames))
    run_until(match, lambda m: m.time_stop is not None and m.super_freeze == 0)


def test_time_stop_freezes_the_opponent_but_not_the_user():
    match = make_duel("jotaro_p3", "mannequin_red", p1=(100, 100), p2=(300, 100))
    stop_time(match)
    jotaro, victim = match.fighters
    assert victim.frozen and not jotaro.frozen
    start_victim, start_jotaro = victim.pos.copy(), jotaro.pos.copy()
    run_held(match, 60, p1=walk(1, 0), p2=walk(0, 1))
    assert victim.pos == start_victim
    assert jotaro.pos.x > start_jotaro.x + 40


def test_time_resumes_after_its_duration():
    match = make_duel("jotaro_p3", "mannequin_red", p1=(100, 100), p2=(300, 100))
    stop_time(match)
    events = run(match, 179)
    assert match.time_stop is not None
    events = run(match, 2)
    assert match.time_stop is None and "time_resume" in kinds(events)
    assert not match.fighters[1].frozen


def test_hits_in_stopped_time_land_when_time_resumes():
    match = make_duel("jotaro_p3", "mannequin_red", p1=(150, 100), p2=(175, 100))
    stop_time(match)
    victim = match.fighters[1]
    run_until(match, lambda m: m.fighters[0].can_act())  # end of the time stop pose
    run(match, 20, p1=press("light"))
    assert victim.hp < victim.max_hp  # the damage is already dealt...
    assert victim.state != State.HITSTUN and victim.velocity.length() == 0  # ...not the impact
    run_until(match, lambda m: m.time_stop is None)
    assert victim.state == State.HITSTUN and victim.velocity.length() > 0


def test_the_round_clock_waits_in_stopped_time():
    from helpers import OPEN_BOUNDS

    from jojo_arena.characters import get_fighter
    from jojo_arena.combat.arena import Arena
    from jojo_arena.combat.rounds import Rounds
    from jojo_arena.combat.rules import load_rules

    kits = (get_fighter("jotaro_p3").kit, get_fighter("mannequin_red").kit)
    rounds = Rounds(
        kits, load_rules(), lambda: Arena(OPEN_BOUNDS, (Vec2(100, 100), Vec2(300, 100))), 1
    )
    for _ in range(rounds.rules.round_intro_f + 1):
        rounds.step((NONE, NONE))
    stand_out(rounds.match.fighters[0])
    rounds.step((press("special"), NONE))
    while rounds.match.time_stop is None:
        rounds.step((NONE, NONE))
    before = rounds.timer_f
    for _ in range(60):
        rounds.step((NONE, NONE))
    assert rounds.timer_f == before


def test_a_time_stopper_can_move_a_moment_in_the_other_stopped_time():
    match = make_duel("dio_p3", "jotaro_p3", p1=(100, 100), p2=(300, 100))
    stop_time(match, who=0)
    jotaro = match.fighters[1]
    assert not jotaro.frozen  # 1 s the first time
    run(match, 59)
    assert not jotaro.frozen
    run(match, 2)
    assert jotaro.frozen


def test_the_moment_grows_each_time():
    match = make_duel("dio_p3", "jotaro_p3", p1=(100, 100), p2=(300, 100))
    stop_time(match, who=0)
    first = match.time_stop.allowance[1]
    run_until(match, lambda m: m.time_stop is None)
    match.fighters[0].cooldowns.clear()
    run(match, 40)
    stop_time(match, who=0)
    assert match.time_stop.allowance[1] > first


def test_two_time_stoppers_both_move():
    match = make_duel("dio_p3", "jotaro_p3", p1=(100, 100), p2=(300, 100))
    stop_time(match, who=0)
    # Jotaro answers with his own time stop while he can still move.
    stand_out(match.fighters[1])
    match.step((NONE, press("special")))
    run_until(match, lambda m: 1 in m.time_stop.casters)
    run(match, 100)
    assert not match.fighters[0].frozen and not match.fighters[1].frozen


def test_knives_thrown_in_stopped_time_hang_then_fly_on():
    match = make_duel("dio_p3", "mannequin_red", p1=(100, 100), p2=(300, 100))
    stop_time(match, who=0)
    run_until(match, lambda m: m.fighters[0].can_act())  # end of the time stop pose
    run(match, 30, p1=press("special", move=(1.0, 0.0)))
    assert len(match.projectiles) == 5
    hanging = [p.pos.copy() for p in match.projectiles]
    run(match, 30)
    assert [p.pos for p in match.projectiles] == hanging
    run_until(match, lambda m: m.time_stop is None)
    run(match, 5)
    assert any(p.pos != h for p, h in zip(match.projectiles, hanging, strict=False)) or (
        match.fighters[1].hp < match.fighters[1].max_hp
    )


def test_time_stop_has_a_long_cooldown():
    match = make_duel("jotaro_p3", "mannequin_red", p1=(100, 100), p2=(300, 100))
    stop_time(match)
    run_until(match, lambda m: m.time_stop is None)
    run(match, 30)
    match.step((press("special"), NONE))
    assert match.fighters[0].state != State.ATTACK
    assert match.fighters[0].time_stop_ready() is False


def test_road_roller_lands_where_the_opponent_stood():
    match = make_duel("dio_p3", "mannequin_red", p1=(100, 100), p2=(200, 100))
    match.fighters[0].hh = 200
    events = run(match, 150, p1=press("heart_heat"))
    victim = match.fighters[1]
    assert "time_stop" in kinds(events)
    assert victim.max_hp - victim.hp >= 220


def test_jotaro_great_heat_rushes_in_stopped_time():
    match = make_duel("jotaro_p3", "mannequin_red", p1=(100, 100), p2=(160, 100))
    match.fighters[0].hh = 200
    events = run(match, 200, p1=press("heart_heat"))
    assert "time_stop" in kinds(events)
    assert match.fighters[1].max_hp - match.fighters[1].hp >= 8 * 25


# Kakyoin -----------------------------------------------------------------------------------


def test_emerald_splash_is_a_fan_of_six():
    match = make_duel("kakyoin", "mannequin_red", p1=(100, 100), p2=(300, 100))
    stand_out(match.fighters[0])
    run(match, 16, p1=press("special"))
    assert len(match.projectiles) == 6


def test_threads_fire_on_their_own_when_touched():
    match = make_duel("kakyoin", "mannequin_red", p1=(100, 100), p2=(300, 100))
    stand_out(match.fighters[0])
    run(match, 20, p1=press("special", move=(1.0, 0.0)))
    assert len(match.traps) == 1
    trap = match.traps[0]
    match.fighters[1].pos = trap.pos + Vec2(30, 0)
    events = run_held(match, 30, p2=walk(-1, 0))
    assert "trap_triggered" in kinds(events)
    assert match.fighters[1].hp < match.fighters[1].max_hp


def test_at_most_three_threads():
    match = make_duel("kakyoin", "mannequin_red", p1=(100, 100), p2=(380, 100))
    stand_out(match.fighters[0])
    for _ in range(4):
        run(match, 30, p1=press("special", move=(0.0, 1.0)))
    assert len(match.traps) == 3


def test_twenty_metre_emerald_splash_closes_in_from_every_side():
    match = make_duel("kakyoin", "mannequin_red", p1=(100, 100), p2=(220, 100))
    match.fighters[0].hh = 200
    run(match, 30 + match.rules.super_freeze_f + 2, p1=press("heart_heat"))
    target = match.fighters[1].pos
    assert len(match.projectiles) >= 12
    xs = [p.pos.x - target.x for p in match.projectiles]
    assert min(xs) < 0 < max(xs)


# Polnareff ---------------------------------------------------------------------------------


def test_shooting_the_blade_disarms_silver_chariot():
    match = make_duel("polnareff", "mannequin_red", p1=(100, 100), p2=(300, 100))
    pol = match.fighters[0]
    stand_out(pol)
    run(match, 30, p1=press("special"))
    assert pol.disarmed_f > 0
    run(match, 1, p1=press("light"))
    assert pol.attack.move is pol.kit.stances["base"].moves["light"]
    run(match, 130)
    assert pol.disarmed_f == 0


def test_armor_off_is_faster_but_frailer():
    match = make_duel("polnareff", "mannequin_red", p1=(100, 100), p2=(380, 100))
    pol = match.fighters[0]
    stand_out(pol)
    base_speed = pol.walk_speed()
    run(match, 30, p1=press("special", move=(0.0, 1.0)))
    assert pol.buff is not None
    assert pol.walk_speed() == pytest.approx(base_speed * 1.5)
    assert pol.damage_taken_mult == pytest.approx(1.35)
    run(match, 8 * 60)
    assert pol.buff is None
