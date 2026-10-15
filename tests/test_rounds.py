from helpers import NONE, OPEN_BOUNDS, kinds, press

from jojo_arena.characters import get_fighter
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.fighter import State
from jojo_arena.combat.rounds import Phase, Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2

RULES = load_rules()


def make_rounds(rounds_to_win=2) -> Rounds:
    kit = get_fighter("mannequin_red").kit

    def arena():
        return Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(180, 100)))

    return Rounds((kit, kit), RULES, arena, rounds_to_win)


def step(rounds, frames, p1=NONE, p2=NONE):
    events = []
    for i in range(frames):
        events += rounds.step((p1, p2) if i == 0 else (NONE, NONE))
    return events


def skip_intro(rounds):
    return step(rounds, RULES.round_intro_f)


def ko(rounds, loser: int):
    """Knock `loser` out with one light attack from the other fighter."""
    rounds.match.fighters[loser].hp = 1
    attack = press("light")
    return step(rounds, 40, p1=attack if loser == 1 else NONE, p2=attack if loser == 0 else NONE)


def finish_round(rounds):
    return step(rounds, RULES.round_outro_f + 5)


def test_intro_freezes_players_then_says_fight():
    rounds = make_rounds()
    events = step(rounds, 1)
    assert "round_start" in kinds(events)
    step(rounds, 10, p1=press("light"))
    assert rounds.match.fighters[0].state == State.IDLE
    events = skip_intro(rounds)
    assert "fight" in kinds(events)
    assert rounds.phase == Phase.FIGHT


def test_timer_counts_down_only_while_fighting():
    rounds = make_rounds()
    skip_intro(rounds)
    assert rounds.timer_seconds == 99
    step(rounds, 60)
    assert rounds.timer_seconds == 98


def test_time_up_goes_to_the_higher_life_percentage():
    rounds = make_rounds()
    skip_intro(rounds)
    rounds.match.fighters[0].hp = 500
    rounds.timer_f = 1
    events = step(rounds, 1)
    assert "time_up" in kinds(events)
    assert rounds.result.winners == (1,) and rounds.result.reason == "time"


def test_equal_life_at_time_up_is_a_draw_for_both():
    rounds = make_rounds(rounds_to_win=3)
    skip_intro(rounds)
    rounds.timer_f = 1
    step(rounds, 1)
    assert rounds.result.draw
    finish_round(rounds)
    assert rounds.wins == [1, 1]
    assert not rounds.sudden_death


def test_ko_wins_the_round_and_starts_the_next_one_fresh():
    rounds = make_rounds()
    skip_intro(rounds)
    rounds.match.fighters[0].hh = 80
    events = ko(rounds, loser=1)
    assert "round_over" in kinds(events)
    assert rounds.phase == Phase.ROUND_OVER
    finish_round(rounds)
    assert rounds.wins == [1, 0]
    assert rounds.round_number == 2
    assert rounds.phase == Phase.INTRO
    assert all(f.hp == f.max_hp for f in rounds.match.fighters)
    assert rounds.match.fighters[0].hh >= 80  # Heart Heat carries over


def test_first_to_the_target_wins_the_match():
    rounds = make_rounds(rounds_to_win=2)
    for _ in range(2):
        skip_intro(rounds)
        ko(rounds, loser=0)
        events = finish_round(rounds)
    assert "match_over" in kinds(events)
    assert rounds.phase == Phase.MATCH_OVER
    assert rounds.winner == 1


def test_single_round_match():
    rounds = make_rounds(rounds_to_win=1)
    skip_intro(rounds)
    ko(rounds, loser=1)
    finish_round(rounds)
    assert rounds.winner == 0


def test_double_ko_is_a_draw():
    rounds = make_rounds()
    skip_intro(rounds)
    for fighter in rounds.match.fighters:
        fighter.hurt(fighter.hp)  # both drop on the same step
    step(rounds, 1)
    assert rounds.result is not None and rounds.result.reason == "double_ko"
    assert rounds.result.draw


def test_draw_on_match_point_leads_to_sudden_death():
    rounds = make_rounds(rounds_to_win=1)
    skip_intro(rounds)
    rounds.timer_f = 1
    step(rounds, 1)  # equal life: draw, both reach 1 win
    events = finish_round(rounds)
    assert rounds.sudden_death
    assert "sudden_death" in kinds(events)
    assert all(f.hp == 1 for f in rounds.match.fighters)
    assert rounds.timer_seconds is None
    skip_intro(rounds)
    step(rounds, 6000)
    assert rounds.phase == Phase.FIGHT  # no timer in sudden death


def test_sudden_death_first_hit_wins():
    rounds = make_rounds(rounds_to_win=1)
    skip_intro(rounds)
    rounds.timer_f = 1
    step(rounds, 1)
    finish_round(rounds)
    skip_intro(rounds)
    step(rounds, 40, p2=press("light"))
    finish_round(rounds)
    assert rounds.winner == 1


def test_timer_pauses_during_a_clash():
    rounds = make_rounds()
    skip_intro(rounds)
    events = step(rounds, 1, p1=press("light"), p2=press("light"))
    while "clash_start" not in kinds(events):
        events = step(rounds, 1)
    before = rounds.timer_f
    step(rounds, 60)
    assert rounds.timer_f == before
