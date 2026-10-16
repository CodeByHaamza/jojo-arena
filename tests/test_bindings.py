"""Changing the keys in the game: swaps, the second key kept, saved, cancelled, reset."""

import pygame
import pytest

from jojo_arena import controls
from jojo_arena.context import GameContext
from jojo_arena.controls import PlayerControls, load_controls
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.ui.bindings_scene import ACTIONS, BindingsScene, rebind
from jojo_arena.ui.options_scene import OptionsScene


def test_a_key_taken_by_another_action_swaps_with_it():
    player = PlayerControls("keyboard", {"light": ["J"], "heavy": ["K"]})
    changed = rebind(player, "light", "K")
    assert changed.bindings["light"] == ["K"] and changed.bindings["heavy"] == ["J"]


def test_the_second_key_of_an_action_stays():
    player = PlayerControls("keyboard", {"up": ["W", "Up"], "stand": ["I"]})
    changed = rebind(player, "up", "I")
    assert changed.bindings["up"] == ["I", "Up"] and changed.bindings["stand"] == ["W"]


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    config, _ = controls.parse_controls(None)
    context = GameContext(
        Display("test", (480, 270)), InputManager(), SceneManager(), config, tmp_path / "c.json"
    )
    yield context
    pygame.display.quit()


def keys(ctx, *names: str):
    for name in names:
        code = KEY_SCANCODES[name]
        ctx.inputs.handle_event(pygame.event.Event(pygame.KEYDOWN, scancode=code, key=0, mod=0))
        ctx.inputs.handle_event(pygame.event.Event(pygame.KEYUP, scancode=code, key=0, mod=0))
        ctx.inputs.begin_step()
        ctx.scenes.current.update()
        ctx.scenes.apply_pending()
        ctx.scenes.current.draw(ctx.display.surface)


def test_a_new_key_from_options_to_the_saved_file(ctx):
    options = OptionsScene(ctx)
    ctx.scenes.switch(options)
    ctx.scenes.apply_pending()
    options.menu.select("keys")
    keys(ctx, "Return")
    scene = ctx.scenes.current
    assert isinstance(scene, BindingsScene)
    scene.row = ACTIONS.index("light")
    keys(ctx, "Return")
    assert scene.waiting
    keys(ctx, "M")
    assert not scene.waiting
    assert ctx.controls.active_preset.players[0].bindings["light"][0] == "M"
    saved, _ = load_controls(ctx.controls_path)
    assert saved.active_preset.players[0].bindings["light"][0] == "M"


def test_escape_cancels_and_the_defaults_come_back(ctx):
    scene = BindingsScene(ctx)
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()
    scene.row = ACTIONS.index("heavy")
    keys(ctx, "Return", "Escape")
    assert not scene.waiting
    assert ctx.controls.active_preset.players[0].bindings["heavy"][0] == "K"
    scene.row = ACTIONS.index("heavy")
    keys(ctx, "Return", "N")
    assert ctx.controls.active_preset.players[0].bindings["heavy"][0] == "N"
    scene.row = len(ACTIONS)  # default keys
    keys(ctx, "Return")
    assert ctx.controls.active_preset.players[0].bindings["heavy"][0] == "K"
