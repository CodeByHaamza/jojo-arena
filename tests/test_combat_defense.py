import pytest
from helpers import NONE, hold, kinds, make_match, press, run, run_held, walk

from jojo_arena.combat.fighter import State
from jojo_arena.combat.projectile import Projectile
from jojo_arena.engine.geometry import Vec2

LIGHT = 35
HEAVY = 90


def guard_then(match, frames, p1=NONE):
    """P2 holds guard every step; P1 does `p1` on the first step."""
    events = []
    for i in range(frames):
        events += match.step((p1 if i == 0 else NONE, hold("guard")))
    return events


def test_guard_reduces_damage_by_80_percent():
    match = make_match()
    run_held(match, 2, p2=hold("guard"))
    events = guard_then(match, 30, p1=press("light"))
    defender = match.fighters[1]
    assert defender.hp == defender.max_hp - round(LIGHT * 0.2)
    assert "block" in kinds(events)
    assert defender.guard_gauge == pytest.approx(100 - LIGHT * 0.35)


def test_blockstun_returns_to_guard_while_held():
    match = make_match()
    run_held(match, 2, p2=hold("guard"))
    guard_then(match, 7, p1=press("light"))
    assert match.fighters[1].state == State.BLOCKSTUN
    guard_then(match, 40)
    assert match.fighters[1].state == State.GUARD


def test_guard_faces_the_opponent():
    match = make_match(p1=(150, 100), p2=(150, 130))
    match.fighters[1].facing = Vec2(1, 0)
    run_held(match, 2, p2=hold("guard"))
    assert match.fighters[1].facing == Vec2(0, -1)


def test_hit_from_behind_goes_through_the_guard():
    match = make_match(p1=(100, 100), p2=(300, 100))
    run_held(match, 2, p2=hold("guard"))  # P2 guards facing left, toward P1
    special = match.fighters[0].kit.move("base", "special").projectile
    # A projectile from P1 coming from the right, into P2's back.
    match.projectiles.append(Projectile(0, Vec2(330, 100), Vec2(-special.speed, 0), special, 60))
    events = guard_then(match, 20)
    assert "hit" in kinds(events)
    assert match.fighters[1].hp == match.fighters[1].max_hp - special.damage


def test_guard_break_stuns_then_refills_the_gauge():
    match = make_match()
    defender = match.fighters[1]
    run_held(match, 2, p2=hold("guard"))
    defender.guard_gauge = 10
    events = guard_then(match, 1, p1=press("heavy"))
    while "guard_break" not in kinds(events):
        events = guard_then(match, 1)
    assert defender.state == State.GUARD_BROKEN
    run(match, match.hitstop + 88)
    assert defender.state == State.GUARD_BROKEN  # 1.5 s = 90 frames, impact frame included
    run(match, 2)
    assert defender.state == State.IDLE
    assert defender.guard_gauge == 100


def test_guard_gauge_regenerates_after_a_delay():
    match = make_match(p1=(100, 100), p2=(300, 100))
    fighter = match.fighters[0]
    fighter.guard_gauge = 50
    fighter.guard_regen_wait = 60
    run(match, 60)
    assert fighter.guard_gauge == pytest.approx(50)
    run(match, 60)
    assert fighter.guard_gauge == pytest.approx(75)  # 25 per second


def test_blocked_hits_cannot_finish_a_round():
    # Under 25 % life (Résolution) the guard takes no chip damage at all.
    match = make_match()
    run_held(match, 2, p2=hold("guard"))
    match.fighters[1].hp = 5
    events = guard_then(match, 20, p1=press("light"))
    assert match.fighters[1].hp == 5
    assert "block" in kinds(events)


def test_dash_moves_fast_then_recovers():
    match = make_match(p1=(100, 100), p2=(300, 100))
    run(match, 1, p1=press("dash", move=(0.0, 1.0)))
    fighter = match.fighters[0]
    assert fighter.state == State.DASH
    run(match, 13)
    assert fighter.pos.y == pytest.approx(100 + 14 * 5.5)  # 14 frames at 330 px/s
    run(match, 8)
    assert fighter.state == State.IDLE


def test_neutral_dash_steps_away_from_the_opponent():
    match = make_match(p1=(100, 100), p2=(200, 100))
    run(match, 20, p1=press("dash"))
    fighter = match.fighters[0]
    assert fighter.pos.x < 100
    assert fighter.facing == Vec2(1, 0)


def test_dash_invincibility_dodges_a_hit():
    match = make_match()
    events = run(match, 30, p1=press("light"), p2=press("dash", move=(0.0, 1.0)))
    assert match.fighters[1].hp == match.fighters[1].max_hp
    assert "hit" not in kinds(events)


def test_last_moment_dodge_is_a_stylish_evade():
    match = make_match()
    run(match, 5, p1=press("light"))  # light becomes active on its 6th step
    events = run(match, 1, p2=press("dash", move=(0.0, 1.0)))  # dodge on that very step
    assert "stylish" in kinds(events)
    assert match.slowmo > 0
    assert match.fighters[1].hp == match.fighters[1].max_hp


def test_early_dodge_is_not_stylish():
    match = make_match(p1=(150, 100), p2=(175, 100))
    match.step((NONE, press("dash", move=(0.0, 1.0))))
    events = run(match, 7, p1=press("heavy"))  # dash window long gone when it would hit
    assert "stylish" not in kinds(events)


def test_slowmo_halves_the_game_speed():
    match = make_match(p1=(100, 100), p2=(300, 100))
    match.slowmo = 60
    run_held(match, 60, p1=walk(1, 0))
    assert match.fighters[0].pos.x == pytest.approx(100 + 30 * 1.6)


def test_dash_goes_through_the_opponent():
    match = make_match(p1=(100, 100), p2=(130, 100))
    run(match, 22, p1=press("dash", move=(1.0, 0.0)))
    assert match.fighters[0].pos.x > match.fighters[1].pos.x


def test_attack_can_come_out_of_guard():
    match = make_match()
    match.step((hold("guard"), NONE))
    match.step((press("light", hold=("guard",)), NONE))
    assert match.fighters[0].state == State.ATTACK
