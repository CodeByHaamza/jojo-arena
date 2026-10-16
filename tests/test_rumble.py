"""Rumble and the pad's light bar: what a fight does to the hands, tested without a pad."""

import pytest

from jojo_arena import controls
from jojo_arena.combat.events import Event
from jojo_arena.engine.haptics import Haptics, Shake
from jojo_arena.engine.input import InputManager, PadState
from jojo_arena.ui.rumble import FELT, FightRumble, pad_slots


class FakeJoystick:
    """A pad that writes down what it was asked to do."""

    def __init__(self, rumbles: bool = True, lights: bool = True) -> None:
        self.asked: list[tuple[float, float, int]] = []
        self.colors: list[tuple[int, int, int]] = []
        self.stopped = 0
        self._rumbles, self._lights = rumbles, lights

    def rumble(self, low: float, high: float, ms: int) -> bool:
        self.asked.append((low, high, ms))
        return self._rumbles

    def set_led(self, color) -> bool:
        self.colors.append(tuple(color))
        return self._lights

    def stop_rumble(self) -> None:
        self.stopped += 1


def with_pads(count: int = 2) -> InputManager:
    inputs = InputManager()
    inputs.pads = [PadState(i, joystick=FakeJoystick()) for i in range(count)]
    return inputs


def pads(inputs: InputManager) -> list[FakeJoystick]:
    return [pad.joystick for pad in inputs.pads]


# The engine side -------------------------------------------------------------------------


def test_a_shake_reaches_the_right_pad():
    inputs = with_pads()
    haptics = Haptics(inputs)
    assert haptics.shake(1, Shake(0.5, 0.25, 100))
    assert pads(inputs)[0].asked == []
    assert pads(inputs)[1].asked == [(0.5, 0.25, 100)]


def test_nothing_happens_without_a_pad_or_when_it_is_off():
    inputs = with_pads(1)
    haptics = Haptics(inputs)
    assert not haptics.shake(None, Shake(1.0, 1.0, 100))  # that player is on a keyboard
    assert not haptics.shake(3, Shake(1.0, 1.0, 100))  # no such pad
    assert not haptics.shake(0, Shake(0.0, 0.0, 100))  # nothing to feel
    haptics.enabled = False
    assert not haptics.shake(0, Shake(1.0, 1.0, 100))
    assert pads(inputs)[0].asked == []


def test_the_strength_scales_every_shake():
    inputs = with_pads(1)
    haptics = Haptics(inputs)
    haptics.strength = 0.5
    haptics.shake(0, Shake(0.8, 0.4, 100))
    assert pads(inputs)[0].asked == [(0.4, 0.2, 100)]


def test_a_pad_that_refuses_is_not_an_error():
    inputs = with_pads(1)
    inputs.pads[0].joystick = FakeJoystick(rumbles=False, lights=False)
    haptics = Haptics(inputs)
    assert haptics.shake(0, Shake(0.5, 0.5, 80)) is False
    assert haptics.light(0, (255, 0, 0)) is False


def test_stopping_cuts_every_motor():
    inputs = with_pads()
    Haptics(inputs).stop()
    assert [pad.stopped for pad in pads(inputs)] == [1, 1]


# The fight side --------------------------------------------------------------------------


def test_a_blow_is_felt_by_both_sides_but_not_the_same_way():
    inputs = with_pads()
    rumble = FightRumble(inputs, (0, 1))
    rumble.on_events([Event("hit", None, 1, 40)])
    taken = pads(inputs)[1].asked[0]
    given = pads(inputs)[0].asked[0]
    assert taken[:2] == (FELT["hit"].low, FELT["hit"].high)
    assert given[0] < taken[0] and given[2] < taken[2]  # shorter and lighter


def test_the_fighter_doing_it_feels_their_own_super():
    inputs = with_pads()
    rumble = FightRumble(inputs, (0, 1))
    rumble.on_events([Event("gha", None, 0)])
    assert pads(inputs)[0].asked and not pads(inputs)[1].asked


def test_stopping_time_is_felt_by_everyone():
    inputs = with_pads()
    FightRumble(inputs, (0, 1)).on_events([Event("time_stop", None, 0)])
    assert len(pads(inputs)[0].asked) == 1 and len(pads(inputs)[1].asked) == 1


def test_an_event_with_no_fighter_or_no_pattern_does_nothing():
    inputs = with_pads()
    rumble = FightRumble(inputs, (0, 1))
    rumble.on_events([Event("hit", None, None), Event("prop_respawn", None, 0)])
    assert not pads(inputs)[0].asked and not pads(inputs)[1].asked


def test_a_player_on_the_keyboard_is_simply_skipped():
    inputs = with_pads(1)
    rumble = FightRumble(inputs, (None, 0))  # player 1 on the keyboard, player 2 on the pad
    rumble.on_events([Event("hit", None, 0), Event("ko", None, 0)])
    assert pads(inputs)[0].asked  # only the attacker's short one reached a pad
    rumble.on_events([Event("hit", None, 1)])


def test_the_light_bar_takes_the_colour_of_each_fighter():
    inputs = with_pads()
    FightRumble(inputs, (0, 1)).light_up(((160, 60, 220), (240, 200, 60)))
    assert pads(inputs)[0].colors == [(160, 60, 220)]
    assert pads(inputs)[1].colors == [(240, 200, 60)]


def test_turning_it_off_in_the_options_silences_everything():
    inputs = with_pads()
    rumble = FightRumble(inputs, (0, 1), enabled=False)
    rumble.on_events([Event("ko", None, 1)])
    assert not rumble.enabled and not pads(inputs)[1].asked


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("keyboard_gamepad", (None, 0)),  # the lone pad is the first one plugged in
        ("two_gamepads", (0, 1)),
        ("shared_keyboard", (None, None)),
    ],
)
def test_the_pad_slot_of_each_player_is_read_from_the_preset(key, expected):
    config, _ = controls.parse_controls(None)
    assert pad_slots(config.presets[key].players) == expected
