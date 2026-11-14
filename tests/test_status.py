"""Status effects: fire, cold and a current, and what each one actually costs.

The glossary page (characters/lore/part0.toml) promises the player exactly what is
checked here, so these tests also keep that page honest.
"""

import pytest
from helpers import hold, make_duel, press, run, run_held

from jojo_arena.characters import load_roster
from jojo_arena.combat.rules import load_rules
from jojo_arena.combat.status import KINDS, Statuses

RULES = load_rules()


def flaming(gap: float = 24.0):
    """Esidisi in Flame Mode, in reach: everything he throws sets fire."""
    match = make_duel("esidisi", "joseph_p2", p2=(150 + gap, 100))
    esidisi = match.fighters[0]
    esidisi.begin_stance_switch("flame")
    run(match, 20)
    assert esidisi.stance == "flame"
    return match


# What the engine knows ----------------------------------------------------------------


def test_every_kind_the_engine_knows_is_described_in_the_rules():
    assert set(RULES.statuses) == set(KINDS)
    for defn in RULES.statuses.values():
        assert defn.max_f > 0


def test_every_kind_is_used_by_somebody():
    """A status nobody inflicts is a status nobody will ever see."""
    used = set()
    for entry in load_roster():
        for move in entry.kit.all_moves():
            used.add(move.status)
            if move.projectile is not None:
                used.add(move.projectile.status)
            if move.trap is not None:
                used.add(move.trap.projectile.status)
    assert set(KINDS) <= used


def test_a_status_refreshes_but_never_stacks():
    statuses = Statuses(RULES.statuses)
    assert statuses.apply("burn", 30)
    assert not statuses.apply("burn", 30)  # the second hit is not an announcement
    statuses.apply("burn", 10_000)
    assert statuses.frames("burn") == RULES.statuses["burn"].max_f


# Fire ---------------------------------------------------------------------------------


def test_boiling_blood_keeps_burning_after_the_move_is_over():
    match = flaming()
    joseph = match.fighters[1]
    events = run(match, 30, p1=press("heavy"))  # the jets of boiling blood
    assert any(e.kind == "status_burn" for e in events)
    assert "burn" in joseph.statuses
    run(match, 20)  # nothing is thrown any more
    hp = joseph.hp
    run(match, 30)
    assert joseph.hp < hp  # and he is still losing life


def test_a_guard_stops_the_fire_with_the_blow():
    match = flaming()
    joseph = match.fighters[1]
    run_held(match, 40, p1=press("heavy"), p2=hold("guard"))
    assert joseph.hp < joseph.max_hp  # chip damage came through
    assert not joseph.statuses.active  # the fire did not


def test_a_burning_wound_does_not_close():
    """A vampire heals what it is given time to heal. Fire does not give it any."""
    match = make_duel("esidisi", "dio_p1", p2=(174, 100))
    esidisi, dio = match.fighters
    esidisi.begin_stance_switch("flame")
    run(match, 20)
    dio.hp = dio.max_hp - 300
    dio.blood = RULES.blood_max
    run(match, 30, p1=press("heavy"))
    assert "burn" in dio.statuses
    hp = dio.hp
    run(match, RULES.statuses["burn"].max_f)
    assert dio.hp <= hp  # burning: no regeneration, whatever his blood says
    healing = dio.hp
    run(match, 90)
    assert dio.hp > healing  # out it goes, and the wounds start to close


# Cold ---------------------------------------------------------------------------------


def test_the_cold_stays_in_the_blood_after_the_thaw():
    match = make_duel("dio_p1", "lisa_lisa", p2=(172, 100))
    dio, lisa = match.fighters
    dio.begin_stance_switch("freeze")
    run(match, 20)
    walked = lisa.walk_speed()
    run(match, 30, p1=press("light"))  # the freezing touch
    assert "chill" in lisa.statuses
    assert lisa.walk_speed() == pytest.approx(walked * RULES.statuses["chill"].walk_mult)
    hamon = lisa.hamon
    run_held(match, 30, p2=press("stand", hold=("stand",)))  # she tries to breathe
    assert lisa.hamon == hamon  # too cold to breathe the Ripple
    run(match, RULES.statuses["chill"].max_f)  # and once it has worn off
    warm = lisa.hamon
    run_held(match, 30, p2=press("stand", hold=("stand",)))
    assert lisa.hamon > warm  # the Ripple comes back: the test above was not for nothing


# A current ----------------------------------------------------------------------------


def test_the_scarf_runs_a_current_through_him():
    match = make_duel("lisa_lisa", "wamuu", p2=(196, 100))
    lisa, wamuu = match.fighters
    run(match, 40, p1=press("heavy"))  # the binding scarf, wrapped round him
    assert "shock" in wamuu.statuses
    gauge, meter = wamuu.guard_gauge, wamuu.hh
    run(match, 40)
    assert wamuu.guard_gauge < gauge  # the guard comes apart on its own
    assert wamuu.hh == meter  # and he gains nothing while it lasts


# Stopped time -------------------------------------------------------------------------


def test_nothing_burns_in_stopped_time():
    match = flaming()
    joseph = match.fighters[1]
    run(match, 30, p1=press("heavy"))
    assert "burn" in joseph.statuses
    left, hp = joseph.statuses.frames("burn"), joseph.hp
    joseph.frozen = True
    run(match, 30)
    assert joseph.statuses.frames("burn") == left
    assert joseph.hp == hp
