"""Caesar: bubbles that drift after the opponent, the lenses he leaves behind, the
Cat Stance, and Burn Black."""

from helpers import NONE, hold, kinds, make_duel, press, run_held, run_until

GHA = press("heart_heat", move=(1.0, 0.0))


def test_caesars_bubbles_drift_after_the_opponent():
    match = make_duel("caesar", "mannequin_red", p1=(100, 100), p2=(260, 130))
    dummy = match.fighters[1]
    match.step((press("special"), NONE))
    run_until(match, lambda m: m.projectiles, 30)
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 150, p2=hold(move=(0.0, 1.0)))


def test_the_lenses_are_left_behind_and_fire_when_crossed():
    match = make_duel("caesar", "mannequin_red", p1=(100, 100), p2=(260, 100))
    caesar, dummy = match.fighters
    caesar.hamon = match.rules.hamon_max
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_held(match, 30)
    assert match.traps, "the lenses should hang there waiting"
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 240, p2=hold(move=(-1.0, 0.0)))


def test_the_cat_stance_answers_whoever_strikes_him():
    match = make_duel("caesar", "mannequin_red", p1=(150, 100), p2=(172, 100))
    caesar, dummy = match.fighters
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_held(match, 6)
    assert caesar.countering
    events = match.step((NONE, press("light")))
    events += run_held(match, 20)
    assert "counter" in kinds(events)
    assert dummy.hp < dummy.max_hp


def test_burn_black_sets_him_alight_in_a_cutscene():
    match = make_duel("caesar", "mannequin_red", p1=(100, 100), p2=(124, 100))
    caesar, dummy = match.fighters
    caesar.hh = match.rules.hh_max
    events = run_held(match, match.rules.super_freeze_f + 40, p1=GHA)
    assert "cutscene_start" in kinds(events)
    assert match.cutscene is not None and match.cutscene.name == "burn_black"
    run_held(match, match.cutscene.frames_left + 4)
    assert dummy.max_hp - dummy.hp > 200
