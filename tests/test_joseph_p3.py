"""Old Joseph: Hermit Purple on a tap and the Ripple on a hold, the Overdrive that is paid
for, the drum of coal tar and its puddle, the vines that answer a blow, the yank, the throw
through a guard, the vine that drags from afar, Solar Energy Ripple, the pull to the aimed
point, Years of Experience, and Hermit Purple and Ripple."""

from helpers import NONE, hold, kinds, make_duel, press, run, run_held, run_until

from jojo_arena.combat.fighter import State
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Vec2


def _stand(match) -> None:
    joseph = match.fighters[0]
    match.step((press("stand"), NONE))
    run_until(match, lambda m: joseph.stance == "stand" and joseph.can_act(), 60)


def test_a_tap_brings_hermit_purple_out_and_a_hold_breathes():
    match = make_duel("joseph_p3", "mannequin_red", p1=(80, 100), p2=(320, 100))
    joseph = match.fighters[0]
    assert joseph.kit.breathes and joseph.hamon == match.rules.hamon_start
    # Held: he breathes, the gauge fills, and Hermit Purple stays where it was.
    before = joseph.hamon
    events = run_held(match, match.rules.hamon_hold_f + 30, p1=hold("stand"))
    assert joseph.breathing and joseph.stance == "base"
    assert joseph.hamon > before
    assert "breath" in kinds(events)
    run_held(match, 3)
    assert not joseph.breathing and joseph.stance == "base"
    # Tapped: Hermit Purple.
    _stand(match)
    assert joseph.stance == "stand"


def test_a_short_hold_is_still_a_tap():
    match = make_duel("joseph_p3", "mannequin_red", p1=(80, 100), p2=(320, 100))
    joseph = match.fighters[0]
    held = InputFrame((0.0, 0.0), frozenset({"stand"}), {"stand": 1})
    match.step((held, NONE))
    run_held(match, 4, p1=hold("stand"))
    assert joseph.stance == "base"  # still held: not decided yet
    run_until(match, lambda m: joseph.stance == "stand", 60)


def test_the_overdrive_is_paid_for_in_hamon_and_hits_harder():
    def chop(hamon: float) -> int:
        match = make_duel("joseph_p3", "mannequin_red", p1=(150, 100), p2=(176, 100))
        joseph, dummy = match.fighters
        joseph.hamon = hamon
        run(match, 60, p1=press("heavy"))
        return dummy.max_hp - dummy.hp

    plain, paid = chop(0), chop(100)
    assert 0 < plain < paid


def test_the_ripple_burns_a_vampire_twice_as_much():
    def chop(victim: str) -> int:
        match = make_duel("joseph_p3", victim, p1=(150, 100), p2=(176, 100))
        joseph, other = match.fighters
        joseph.hamon = 100
        run(match, 60, p1=press("heavy"))
        return other.max_hp - other.hp

    assert chop("dio_p3") > chop("jotaro_p3")


def test_coal_tar_leaves_a_puddle_that_trips_whoever_steps_in():
    match = make_duel("joseph_p3", "mannequin_red", p1=(80, 100), p2=(320, 100))
    joseph, dummy = match.fighters
    run(match, 60, p1=press("special"))
    assert len(match.traps) == 1
    dummy.pos = match.traps[0].pos.copy()
    events = run_held(match, 12)
    assert "trap_triggered" in kinds(events)
    assert dummy.hp < dummy.max_hp and dummy.state == State.HITSTUN


def test_cunning_tactician_catches_a_blow_and_the_vines_answer():
    match = make_duel("joseph_p3", "mannequin_red", p1=(150, 100), p2=(172, 100))
    joseph, dummy = match.fighters
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_held(match, 6)
    assert joseph.countering
    events = match.step((NONE, press("light")))
    events += run_held(match, 24)
    assert "counter" in kinds(events)
    assert joseph.hp == joseph.max_hp and dummy.hp < dummy.max_hp


def test_the_yank_brings_the_opponent_to_him():
    match = make_duel("joseph_p3", "mannequin_red", p1=(150, 100), p2=(184, 100))
    joseph, dummy = match.fighters
    _stand(match)
    before = dummy.pos.x
    match.step((press("light"), NONE))
    run_held(match, 12)
    match.step((press("light"), NONE))  # the yank
    run_held(match, 20)
    assert dummy.hp < dummy.max_hp
    assert dummy.pos.x < before


def test_take_a_stand_for_it_goes_through_a_guard():
    match = make_duel("joseph_p3", "mannequin_red", p1=(150, 100), p2=(186, 100))
    dummy = match.fighters[1]
    _stand(match)
    match.step((press("heavy"), hold("guard")))
    run_held(match, 40, p2=hold("guard"))
    assert dummy.hp < dummy.max_hp


def test_the_low_vine_drags_the_opponent_in_from_afar():
    match = make_duel("joseph_p3", "mannequin_red", p1=(100, 100), p2=(160, 100))
    joseph, dummy = match.fighters
    _stand(match)
    move = joseph.kit.move("stand", "heavy_alt")
    assert move.shape == "line" and not move.unblockable
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_held(match, 50)
    assert dummy.hp < dummy.max_hp
    assert dummy.pos.x < 150  # 60 px away when it caught: now at his feet


def test_hermit_purple_goes_on_into_solar_energy_ripple():
    match = make_duel("joseph_p3", "mannequin_red", p1=(150, 100), p2=(178, 100))
    joseph, dummy = match.fighters
    _stand(match)
    joseph.hamon = 100
    names = []
    for _ in range(70):
        match.step((press("special"), NONE))
        if joseph.attack is not None and (not names or names[-1] != joseph.attack.move.name):
            names.append(joseph.attack.move.name)
    assert names[:2] == ["special", "solar_energy"]
    assert "shock" in dummy.statuses
    assert joseph.hamon < 100  # the Ripple ran down the vines


def test_panic_is_not_in_his_vocabulary_he_is_pulled_to_the_aimed_point():
    match = make_duel("joseph_p3", "mannequin_red", p1=(150, 100), p2=(320, 100))
    joseph = match.fighters[0]
    _stand(match)
    aim = InputFrame((0.0, 1.0), press_counts={"special": 1}, cursor=(150.0, 190.0))
    match.step((aim, NONE))
    run(match, 30)
    assert joseph.pos.y > 170


def test_years_of_experience_is_a_counter():
    match = make_duel("joseph_p3", "mannequin_red", p1=(150, 100), p2=(172, 100))
    joseph, dummy = match.fighters
    joseph.hh = match.rules.hh_bar
    match.step((press("heart_heat"), NONE))
    run_until(match, lambda m: joseph.countering, 60)  # past the flash of the super
    events = match.step((NONE, press("light")))
    events += run_held(match, 30)
    assert "counter" in kinds(events)
    assert dummy.max_hp - dummy.hp >= 150


def test_hermit_purple_and_ripple_catches_across_the_arena():
    match = make_duel("joseph_p3", "mannequin_red", p1=(60, 100), p2=(250, 100))
    joseph = match.fighters[0]
    gha = joseph.kit.move("base", "gha")
    assert gha.shape == "line" and gha.reach >= 200 and gha.hamon
    joseph.hh = match.rules.hh_max
    events = run(match, 60, p1=press("heart_heat", move=(1.0, 0.0)))
    assert match.cutscene is not None and match.cutscene.name == "hermit_overdrive"
    assert "cutscene_start" in kinds(events)
    events = run(match, match.cutscene.frames_left + 2)
    assert "cutscene_end" in kinds(events)
    assert joseph.pos.distance_to(Vec2(60, 100)) < 200
