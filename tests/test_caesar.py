"""Caesar: bubbles that drift after the opponent, Bubble Lens, and Bubble Barrier
closing in and bursting."""

from helpers import NONE, hold, kinds, make_duel, press, run_held, run_until

GHA = press("heart_heat", move=(1.0, 0.0))


def test_caesars_bubbles_drift_after_the_opponent():
    match = make_duel("caesar", "mannequin_red", p1=(100, 100), p2=(260, 130))
    dummy = match.fighters[1]
    match.step((press("special"), NONE))
    run_until(match, lambda m: m.projectiles, 30)
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 150, p2=hold(move=(0.0, 1.0)))


def test_bubble_lens_reaches_far():
    match = make_duel("caesar", "mannequin_red", p1=(100, 100), p2=(185, 100))
    dummy = match.fighters[1]
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 40)


def test_bubble_barrier_closes_in_and_bursts():
    match = make_duel("caesar", "mannequin_red", p1=(100, 100), p2=(240, 100))
    caesar, dummy = match.fighters
    caesar.hh = match.rules.hh_max
    match.step((GHA, NONE))
    events = run_held(match, match.rules.super_freeze_f + 80)
    assert kinds(events).count("burst") == 10
    assert dummy.max_hp - dummy.hp > 120
