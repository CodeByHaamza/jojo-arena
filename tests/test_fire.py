"""Fire that clings to a body: it burns after the blow, a dash beats it out, and it
never takes the last point of life."""

from __future__ import annotations

from helpers import make_match, press, run


def test_fire_keeps_burning_after_the_blow():
    match = make_match()
    victim = match.fighters[1]
    victim.ignite(120)
    before = victim.hp
    run(match, 120)
    rules = match.rules
    expected = round(rules.fire_damage_per_f * 120)
    assert before - victim.hp == expected
    assert victim.fire_f == 0


def test_more_fire_adds_up_to_the_cap():
    match = make_match()
    victim = match.fighters[1]
    victim.ignite(match.rules.fire_max_f - 10)
    victim.ignite(60)
    assert victim.fire_f == match.rules.fire_max_f


def test_fire_never_takes_the_last_point_of_life():
    match = make_match()
    victim = match.fighters[1]
    victim.hp = 3
    victim.ignite(match.rules.fire_max_f)
    run(match, match.rules.fire_max_f + 5)
    assert victim.hp == 1
    assert victim.alive


def test_a_dash_beats_the_fire_out():
    match = make_match()
    victim = match.fighters[1]
    victim.ignite(match.rules.fire_max_f)
    run(match, 1, p2=press("dash", move=(1.0, 0.0)))
    assert victim.fire_f <= match.rules.fire_max_f - match.rules.fire_dash_douse_f


def test_nothing_burns_in_stopped_time():
    match = make_match()
    victim = match.fighters[1]
    victim.ignite(60)
    victim.frozen = True
    hp = victim.hp
    run(match, 30)
    assert victim.hp == hp
    assert victim.fire_f == 60
