import json
import math

import pygame
import pytest

from jojo_arena import controls
from jojo_arena.engine.actions import (
    InputFrame,
    direction_from_flags,
    merge_frames,
    quantize_8,
)
from jojo_arena.engine.input import (
    KEY_SCANCODES,
    PAD_BUTTON_NAMES,
    GamepadSource,
    InputManager,
    KeyboardSource,
    PadState,
)

DIAG = math.sqrt(0.5)


def key_down(name):
    return pygame.event.Event(pygame.KEYDOWN, scancode=KEY_SCANCODES[name], key=0, mod=0)


def key_up(name):
    return pygame.event.Event(pygame.KEYUP, scancode=KEY_SCANCODES[name], key=0, mod=0)


def test_diagonal_keys_give_unit_vector():
    assert direction_from_flags(True, False, False, True) == pytest.approx((DIAG, -DIAG))
    assert direction_from_flags(True, True, False, False) == (0.0, 0.0)


def test_stick_snaps_to_eight_directions_with_deadzone():
    assert quantize_8(0.1, 0.1, 0.35) == (0.0, 0.0)
    assert quantize_8(0.9, 0.2, 0.35) == (1.0, 0.0)
    assert quantize_8(0.6, 0.55, 0.35) == pytest.approx((DIAG, DIAG))
    assert quantize_8(0.0, -1.0, 0.35) == pytest.approx((0.0, -1.0))


def test_keyboard_source_tracks_held_and_presses_per_step():
    inputs = InputManager()
    source = KeyboardSource({"up": ["W"], "light": ["J"]})
    inputs.handle_event(key_down("W"))
    for _ in range(3):  # mashing: three presses before the step
        inputs.handle_event(key_down("J"))
        inputs.handle_event(key_up("J"))
    inputs.begin_step()
    frame = source.read(inputs)
    assert frame.move == (0.0, -1.0)
    assert frame.is_held("up")
    assert frame.presses("light") == 3
    assert not frame.is_held("light")
    inputs.begin_step()
    frame = source.read(inputs)
    assert frame.presses("light") == 0
    assert frame.is_held("up")


def test_presses_wait_for_the_next_logic_step():
    inputs = InputManager()
    source = KeyboardSource({"light": ["J"]})
    inputs.handle_event(key_down("J"))
    # No begin_step yet: a frame rendered without logic must not lose the press.
    assert source.read(inputs).presses("light") == 0
    inputs.begin_step()
    assert source.read(inputs).presses("light") == 1


def test_focus_loss_releases_keys():
    inputs = InputManager()
    inputs.handle_event(key_down("D"))
    inputs.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    inputs.begin_step()
    assert KeyboardSource({"right": ["D"]}).read(inputs).move == (0.0, 0.0)


def test_gamepad_stick_creates_direction_edges_for_menus():
    inputs = InputManager()
    pad = PadState(instance_id=7)
    inputs.pads.append(pad)
    source = GamepadSource({"confirm": ["a"]}, slot=0)
    pad.axes[pygame.CONTROLLER_AXIS_LEFTY] = 0.9
    inputs.begin_step()
    first = source.read(inputs)
    assert first.was_pressed("down") and first.move == (0.0, 1.0)
    inputs.begin_step()
    assert not source.read(inputs).was_pressed("down")  # still held, no new edge


def test_gamepad_buttons_and_triggers():
    inputs = InputManager()
    inputs.pads.append(PadState(instance_id=3))
    source = GamepadSource({"light": ["x"], "heart_heat": ["righttrigger"]}, slot=0)
    button = pygame.event.Event(
        pygame.CONTROLLERBUTTONDOWN, instance_id=3, button=pygame.CONTROLLER_BUTTON_X
    )
    trigger = pygame.event.Event(
        pygame.CONTROLLERAXISMOTION,
        instance_id=3,
        axis=pygame.CONTROLLER_AXIS_TRIGGERRIGHT,
        value=30000,
    )
    inputs.handle_event(button)
    inputs.handle_event(trigger)
    inputs.handle_event(trigger)  # staying pressed is not a second press
    inputs.begin_step()
    frame = source.read(inputs)
    assert frame.presses("light") == 1
    assert frame.presses("heart_heat") == 1


def test_missing_pad_reads_neutral():
    source = GamepadSource({"light": ["x"]}, slot=1)
    inputs = InputManager()
    inputs.pads.append(PadState(instance_id=1))
    inputs.begin_step()
    assert source.read(inputs) == InputFrame()


def test_merge_frames_sums_presses():
    a = InputFrame((1.0, 0.0), frozenset({"up"}), {"confirm": 1})
    b = InputFrame((0.0, 0.0), frozenset({"back"}), {"confirm": 2})
    merged = merge_frames(a, b)
    assert merged.presses("confirm") == 3
    assert merged.held == {"up", "back"}
    assert merged.move == (1.0, 0.0)


def test_default_presets_only_use_known_keys():
    config, warnings = controls.parse_controls(None)
    assert warnings == []
    for preset in config.presets.values():
        for player in preset.players:
            known = KEY_SCANCODES if player.device == "keyboard" else PAD_BUTTON_NAMES
            for action in controls.ACTIONS:
                assert player.bindings[action], f"{preset.key} {action} unbound"
                assert all(name in known for name in player.bindings[action])


def test_user_file_overrides_one_action_and_keeps_the_rest():
    data = {
        "active_preset": "shared_keyboard",
        "presets": {"shared_keyboard": {"players": [{"bindings": {"light": ["E"]}}]}},
    }
    config, warnings = controls.parse_controls(data)
    assert warnings == []
    left = config.active_preset.players[0]
    assert left.bindings["light"] == ["E"]
    assert left.bindings["heavy"] == controls.SHARED_LEFT["heavy"]
    assert config.active_preset.players[1].bindings == {
        a: controls.SHARED_RIGHT[a] for a in controls.ACTIONS
    }


def test_unknown_keys_are_reported_not_fatal():
    data = {"presets": {"keyboard_gamepad": {"players": [{"bindings": {"light": ["Nope"]}}]}}}
    config, warnings = controls.parse_controls(data)
    assert any("Nope" in w for w in warnings)
    assert config.presets["keyboard_gamepad"].players[0].bindings["light"] == []


def test_load_creates_file_then_survives_corruption(tmp_path):
    path = tmp_path / "controls.json"
    config, _ = controls.load_controls(path)
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["active_preset"] == config.active
    path.write_text("{ not json", encoding="utf-8")
    config, warnings = controls.load_controls(path)
    assert config.active == controls.DEFAULT_ACTIVE
    assert warnings
    assert path.read_text(encoding="utf-8") == "{ not json"  # user file left untouched


def test_round_trip_and_cycle(tmp_path):
    path = tmp_path / "controls.json"
    config, _ = controls.parse_controls(None)
    config.cycle(1)
    controls.save_controls(config, path)
    loaded, warnings = controls.load_controls(path)
    assert warnings == []
    assert loaded.active == config.active
    assert loaded.presets == config.presets


def test_controls_file_keeps_key_lists_on_one_line(tmp_path):
    path = tmp_path / "controls.json"
    controls.load_controls(path)
    text = path.read_text(encoding="utf-8")
    assert '"up": ["W", "Up"]' in text
    assert "J1 CLAVIER  J2 MANETTE" in text  # strings with spaces are untouched


def test_pads_needed():
    config, _ = controls.parse_controls(None)
    assert config.presets["keyboard_gamepad"].pads_needed() == 1
    assert config.presets["shared_keyboard"].pads_needed() == 0
    assert config.presets["two_gamepads"].pads_needed() == 2
