from helpers import NONE, OPEN_BOUNDS, press

from jojo_arena.characters import get_fighter
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.dummy import Dummy, dummy_input
from jojo_arena.combat.fighter import State
from jojo_arena.combat.rounds import Phase
from jojo_arena.combat.rules import load_rules
from jojo_arena.combat.training import Training
from jojo_arena.engine.geometry import Vec2

RULES = load_rules()


def make_training() -> Training:
    kit = get_fighter("mannequin_red").kit

    def arena():
        return Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(170, 100)))

    return Training((kit, kit), RULES, arena)


def step(training, frames, p1=NONE, p2=NONE):
    events = []
    for i in range(frames):
        events += training.step((p1, p2) if i == 0 else (NONE, NONE))
    return events


def punch(training, frames=30):
    return step(training, frames, p1=press("light"))


def test_training_starts_at_once_with_no_clock_and_full_gauges():
    training = make_training()
    assert training.phase == Phase.FIGHT
    assert training.timer_seconds is None and training.rounds_to_win == 0
    step(training, 1, p1=press("light"))
    assert training.match.fighters[0].state == State.ATTACK  # no intro to wait for
    assert all(f.hh == RULES.hh_max for f in training.match.fighters)


def test_infinite_life_never_knocks_out_and_refills_after_the_combo():
    training = make_training()
    dummy = training.match.fighters[1]
    dummy.hurt(dummy.max_hp * 10)
    assert dummy.hp == 1 and dummy.state != State.KO
    punch(training)
    assert dummy.hp < dummy.max_hp
    step(training, RULES.training_refill_f + 40)
    assert dummy.hp == dummy.max_hp


def test_normal_life_ko_puts_both_back_without_a_score():
    training = make_training()
    training.infinite_life = False
    training.apply_options()
    dummy = training.match.fighters[1]
    dummy.hp = 1
    punch(training)
    assert training.phase == Phase.ROUND_OVER
    old_match = training.match
    step(training, RULES.round_outro_f + 1)
    assert training.phase == Phase.FIGHT
    assert training.match is not old_match
    assert training.match.fighters[1].hp == training.match.fighters[1].max_hp
    assert training.wins == [0, 0] and training.winner is None


def test_normal_heart_heat_is_spent():
    training = make_training()
    training.infinite_hh = False
    training.apply_options()
    step(training, 1, p1=press("heart_heat"))
    assert training.match.fighters[0].hh < RULES.hh_max


def test_combo_counter_adds_hits_and_damage_then_ends():
    training = make_training()
    combo = training.combos[0]
    events = []
    for _ in range(2):
        events += punch(training, 12)  # light cancels into light on hit
    hits = [e for e in events if e.kind == "hit" and e.fighter == 1]
    assert combo.hits == len(hits) >= 2
    assert combo.damage == sum(round(e.value) for e in hits)
    step(training, 60)
    assert not combo.live and combo.visible  # over, still shown for a moment
    punch(training)
    assert combo.hits == 1  # a fresh combo starts from zero


def test_dummy_modes():
    assert dummy_input(Dummy.STAND) == NONE
    assert dummy_input(Dummy.PLAYER) is None
    training = make_training()
    guarding = dummy_input(Dummy.GUARD)
    step(training, 2, p2=guarding)
    for _ in range(3):
        training.step((NONE, guarding))
    assert training.match.fighters[1].state == State.GUARD


def test_reset_puts_fighters_back_and_keeps_the_options():
    training = make_training()
    training.infinite_hh = False
    step(training, 20, p1=press("dash", move=(1.0, 0.0)))
    training.reset()
    assert training.match.fighters[0].pos == Vec2(150, 100)
    assert training.infinite_hh is False
    assert training.match.fighters[0].hh == 0


def test_the_dummy_setup_is_saved_and_read_back():
    """Setting the dummy up takes a dozen presses: it survives leaving the room."""
    from jojo_arena.characters import get_fighter
    from jojo_arena.combat.dummy import After, Dummy, DummyPlayer, dummy_actions
    from jojo_arena.settings import parse_settings

    dummy = DummyPlayer(dummy_actions(get_fighter("jotaro_p3").kit))
    dummy.select("base/heavy")
    dummy.plan.delay_f = 12
    dummy.plan.approach = True
    dummy.plan.mode = Dummy.ACTION
    dummy.plan.after = After.GUARD
    saved = dummy.to_json()

    # The same setup put back on another character: the action is kept by name.
    other = DummyPlayer(dummy_actions(get_fighter("kakyoin").kit))
    other.load_json(saved)
    assert other.action.key == "base/heavy"
    assert other.plan.delay_f == 12 and other.plan.approach
    assert other.plan.mode is Dummy.ACTION and other.plan.after is After.GUARD

    # And it goes through settings.json without losing anything.
    assert parse_settings({"training": saved}).training == saved
    nonsense = DummyPlayer(dummy_actions(get_fighter("jotaro_p3").kit))
    nonsense.load_json({"action": "no/such/move", "delay_f": 9999, "mode": "nope"})
    assert nonsense.plan.delay_f != 9999  # a delay that is not on the dial is ignored
