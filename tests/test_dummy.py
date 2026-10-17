"""The training dummy: the action it repeats, the delay between two, and recording one."""

from helpers import NONE, OPEN_BOUNDS, press

from jojo_arena.characters import get_fighter
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.dummy import After, Dummy, DummyPlayer, dummy_actions
from jojo_arena.combat.fighter import State
from jojo_arena.combat.rules import load_rules
from jojo_arena.combat.training import Training
from jojo_arena.engine.geometry import Vec2

RULES = load_rules()


def make_training(p1: str = "jotaro_p3", p2: str = "jotaro_p3", gap: float = 26.0) -> Training:
    kits = (get_fighter(p1).kit, get_fighter(p2).kit)

    def arena() -> Arena:
        return Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(150 + gap, 100)))

    return Training(kits, RULES, arena)


def make_player(training: Training, key: str = "", **plan) -> DummyPlayer:
    player = DummyPlayer(dummy_actions(training.kits[1]))
    player.plan.mode = Dummy.ACTION
    if key:
        player.select(key)
    for field, value in plan.items():
        setattr(player.plan, field, value)
    return player


def run(training: Training, player: DummyPlayer, frames: int, p1=NONE) -> list:
    """Step the fight with the dummy driven by `player`; p1 presses on the first step."""
    events = []
    for i in range(frames):
        me, foe = training.match.fighters[1], training.match.fighters[0]
        frame = player.think(me, foe)
        events += training.step((p1 if i == 0 else NONE, frame if frame is not None else NONE))
    return events


def attacks(training: Training, player: DummyPlayer, frames: int) -> list[int]:
    """The step numbers at which the dummy started a move."""
    starts, serial = [], -1
    for step in range(frames):
        me, foe = training.match.fighters[1], training.match.fighters[0]
        frame = player.think(me, foe)
        training.step((NONE, frame if frame is not None else NONE))
        attack = training.match.fighters[1].attack
        if attack is not None and attack.serial != serial:
            serial = attack.serial
            starts.append(step)
    return starts


# The catalog --------------------------------------------------------------------------


def test_the_catalog_lists_every_move_a_button_can_start():
    keys = [a.key for a in dummy_actions(get_fighter("jotaro_p3").kit)]
    assert "base/light" in keys  # the jab
    assert "stand/heavy" in keys  # ORA ORA ORA, with Star Platinum out
    assert "stand/special_alt" in keys  # Star Finger, a direction held
    assert "hha" in keys and "gha" in keys
    # The rest of a chain and a counter answer are not on a button of their own.
    assert not any(k.endswith(("light2", "light3", "counter_ora")) for k in keys)


def test_an_action_carries_its_move_and_its_label():
    action = next(a for a in dummy_actions(get_fighter("jotaro_p3").kit) if a.key == "stand/heavy")
    assert action.press == "heavy" and action.stance == "stand" and not action.direction
    assert action.move is not None and action.move.hits > 10  # the barrage, whatever its length
    assert "ORA ORA ORA" in action.label


def test_an_alt_move_holds_a_direction():
    action = next(
        a for a in dummy_actions(get_fighter("jotaro_p3").kit) if a.key == "stand/special_alt"
    )
    assert action.press == "special" and action.direction


# Repeating one action ------------------------------------------------------------------


def test_the_dummy_brings_its_stand_out_for_a_move_that_needs_it():
    training = make_training()
    player = make_player(training, "stand/heavy", delay_f=0)
    run(training, player, RULES.stance_switch_f + 6)
    assert training.match.fighters[1].stance == "stand"


def test_it_plays_the_chosen_move_and_nothing_else():
    training = make_training()
    player = make_player(training, "stand/heavy", delay_f=0)
    run(training, player, RULES.stance_switch_f + 20)
    attack = training.match.fighters[1].attack
    assert attack is not None and attack.move.label == "ORA ORA ORA"


def test_no_action_leaves_the_dummy_still():
    training = make_training()
    player = make_player(training, delay_f=0)  # the catalog's first entry: none
    run(training, player, 60)
    assert training.match.fighters[1].state == State.IDLE
    assert training.match.fighters[1].attack is None


def test_the_delay_is_the_frames_waited_between_two_repetitions():
    # Out of reach, so no hit and no hitstop: the loop is pure timing.
    training = make_training(gap=200)
    player = make_player(training, "base/heavy", delay_f=30)  # headbutt: no Stand needed
    starts = attacks(training, player, 400)
    assert len(starts) >= 3
    gaps = [b - a for a, b in zip(starts, starts[1:], strict=False)]
    assert len(set(gaps)) == 1, gaps  # always the same, frame for frame
    assert gaps[0] == player.action.move.total_f + 30, gaps


def test_a_delay_of_zero_strikes_back_on_the_first_frame_it_can():
    training = make_training(gap=200)
    player = make_player(training, "base/heavy", delay_f=0)
    starts = attacks(training, player, 300)
    gaps = [b - a for a, b in zip(starts, starts[1:], strict=False)]
    assert gaps and set(gaps) == {player.action.move.total_f}, gaps


def test_it_holds_guard_between_two_actions():
    training = make_training()
    player = make_player(training, "base/heavy", delay_f=120, after=After.GUARD)
    run(training, player, 40)
    assert training.match.fighters[1].state == State.GUARD
    # Guarding does not stop it from attacking when the delay is over.
    assert len(attacks(training, player, 200)) >= 1


def test_without_the_guard_option_it_waits_doing_nothing():
    training = make_training()
    player = make_player(training, "base/heavy", delay_f=120)
    run(training, player, 40)
    assert training.match.fighters[1].state == State.IDLE


def test_it_walks_in_when_the_move_cannot_reach():
    training = make_training(gap=140)
    player = make_player(training, "base/heavy", delay_f=60, approach=True)
    before = training.match.fighters[1].pos.distance_to(training.match.fighters[0].pos)
    run(training, player, 50)
    after = training.match.fighters[1].pos.distance_to(training.match.fighters[0].pos)
    assert after < before - 10


def test_it_stays_put_without_the_approach_option():
    training = make_training(gap=140)
    player = make_player(training, "base/heavy", delay_f=60)
    before = training.match.fighters[1].pos.copy()
    run(training, player, 50)
    assert training.match.fighters[1].pos == before


def test_the_chain_option_follows_the_chain_to_its_end():
    training = make_training()
    player = make_player(training, "base/light", delay_f=0, chain=True)
    run(training, player, 120)
    played = [move.name for move in player.played]
    assert "light2" in played and "light3" in played  # it followed the chain through


def test_without_the_chain_option_it_only_plays_the_first_blow():
    training = make_training()
    player = make_player(training, "base/light", delay_f=0, chain=False)
    run(training, player, 120)
    assert {move.name for move in player.played} == {"light"}  # the first blow only


# Recording -----------------------------------------------------------------------------


def test_a_recorded_action_is_played_back_in_a_loop():
    training = make_training()
    player = make_player(training)
    player.start_recording()
    assert player.think(training.match.fighters[1], training.match.fighters[0]) is None
    for frame in (press("heavy"), NONE, NONE, NONE):
        player.record(frame)
    player.stop_recording()
    assert player.plan.mode == Dummy.PLAYBACK and player.recorded
    player.plan.delay_f = 0
    starts = attacks(training, player, 300)
    assert len(starts) >= 2  # the recording loops
    assert {move.name for move in player.played} == {"heavy"}  # what was recorded


def test_stopping_an_empty_recording_leaves_the_dummy_still():
    training = make_training()
    player = make_player(training)
    player.start_recording()
    player.stop_recording()
    assert player.plan.mode == Dummy.STAND and not player.recorded
