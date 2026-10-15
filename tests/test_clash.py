import dataclasses

from helpers import kinds, make_match, press, run

from jojo_arena.combat.fighter import State
from jojo_arena.combat.kit import Kit, Stance
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.actions import InputFrame

CLASH_F = load_rules().clash_duration_f


def step_mash(match, p1: int, p2: int):
    """One step where P1 and P2 hit attack buttons p1 and p2 times."""
    return match.step(
        (InputFrame(press_counts={"light": p1}), InputFrame(press_counts={"heavy": p2}))
    )


def start_clash(match):
    events = run(match, 1, p1=press("light"), p2=press("light"))
    while "clash_start" not in kinds(events):
        events = run(match, 1)
    return events


def test_attacks_meeting_at_the_same_instant_clash():
    match = make_match()
    start_clash(match)
    assert match.clash is not None
    assert all(f.state == State.CLASH for f in match.fighters)
    assert all(f.hp == f.max_hp for f in match.fighters)


def test_attacks_far_apart_in_time_do_not_clash():
    match = make_match()
    run(match, 1, p1=press("light"))
    events = run(match, 3)
    events += run(match, 30, p2=press("light"))
    assert "clash_start" not in kinds(events)
    assert match.fighters[1].hp < match.fighters[1].max_hp


def test_clash_window_allows_a_few_frames_of_difference():
    match = make_match()
    run(match, 1, p1=press("light"))
    events = run(match, 1)
    events += run(match, 10, p2=press("light"))  # P2 two frames late: still a clash
    assert "clash_start" in kinds(events)


def test_mashing_more_wins_the_clash():
    match = make_match()
    start_clash(match)
    events = []
    for _ in range(CLASH_F):
        events += step_mash(match, 3, 1)
    loser = match.fighters[1]
    assert "clash_win" in kinds(events)
    assert loser.hp == loser.max_hp - match.rules.clash_loser_damage
    assert loser.state == State.HITSTUN
    assert match.fighters[0].state == State.IDLE


def test_duel_bar_leans_toward_whoever_mashes_more():
    match = make_match()
    start_clash(match)
    for _ in range(10):
        step_mash(match, 2, 1)
    assert match.clash.balance < 0  # negative = player 1 ahead


def test_clash_lasts_three_seconds():
    match = make_match()
    start_clash(match)
    for _ in range(CLASH_F - 1):
        step_mash(match, 1, 0)
    assert match.clash is not None
    step_mash(match, 1, 0)
    assert match.clash is None


def test_even_clash_pushes_both_back_without_damage():
    match = make_match()
    start_clash(match)
    before = match.fighters[0].pos.distance_to(match.fighters[1].pos)
    events = []
    for _ in range(CLASH_F):
        events += step_mash(match, 2, 2)
    events += run(match, 20)
    assert "clash_tie" in kinds(events)
    assert all(f.hp == f.max_hp for f in match.fighters)
    assert match.fighters[0].pos.distance_to(match.fighters[1].pos) > before


def test_mashing_does_not_leak_into_attacks_after_the_clash():
    match = make_match()
    start_clash(match)
    for _ in range(CLASH_F):
        step_mash(match, 3, 1)
    run(match, 2)
    assert match.fighters[0].state == State.IDLE


def test_non_clashable_attacks_trade_instead():
    match = make_match()
    kit: Kit = match.fighters[0].kit
    base = kit.stances["base"]
    light = dataclasses.replace(base.moves["light"], clashable=False)
    stances = dict(kit.stances, base=Stance(dict(base.moves, light=light)))
    no_clash = dataclasses.replace(kit, stances=stances)
    for fighter in match.fighters:
        fighter.kit = no_clash
    events = run(match, 30, p1=press("light"), p2=press("light"))
    assert "clash_start" not in kinds(events)
    assert all(f.hp == f.max_hp - 35 for f in match.fighters)
