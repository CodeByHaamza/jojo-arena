import pygame
import pytest

from jojo_arena import controls
from jojo_arena.characters import load_roster
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.ui import text
from jojo_arena.ui.fight_scene import FightScene
from jojo_arena.ui.menu import Menu, MenuItem
from jojo_arena.ui.setup_scene import SetupScene
from jojo_arena.ui.title_scene import TitleScene


def test_every_ui_string_can_be_drawn():
    strings = [v for k, v in vars(text).items() if k.isupper() and isinstance(v, str)]
    strings += [f.name for f in load_roster()]
    missing = {c for s in strings for c in s.upper() if c not in font.GLYPHS and c not in "{}"}
    assert missing == set()


def test_text_size_matches_render():
    image = font.render("K.O.", (255, 255, 255), scale=2, outline=None)
    assert image.get_width() == font.text_width("K.O.", 2)
    assert image.get_height() == font.HEIGHT * 2


def test_menu_navigation_wraps_and_changes_values():
    menu = Menu([MenuItem("a", "A", ["1", "3", "5"]), MenuItem("b", "B")])
    assert menu.handle(InputFrame(press_counts={"up": 1})) is None
    assert menu.selected.key == "b"
    assert menu.handle(InputFrame(press_counts={"confirm": 1})) == ("confirm", "b")
    menu.handle(InputFrame(press_counts={"down": 1}))
    assert menu.handle(InputFrame(press_counts={"left": 1})) == ("change", "a")
    assert menu.selected.value == "5"
    assert menu.handle(InputFrame(press_counts={"back": 1})) == ("back", "")


# Whole-screen flow, with a hidden window --------------------------------------------------


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


def tap(ctx, key: str):
    code = KEY_SCANCODES[key]
    ctx.inputs.handle_event(pygame.event.Event(pygame.KEYDOWN, scancode=code, key=0, mod=0))
    ctx.inputs.handle_event(pygame.event.Event(pygame.KEYUP, scancode=code, key=0, mod=0))


def steps(ctx, n: int = 1):
    for _ in range(n):
        ctx.inputs.begin_step()
        ctx.scenes.current.update()
        ctx.scenes.apply_pending()
        ctx.scenes.current.draw(ctx.display.surface)


def test_title_to_fight_to_pause_and_back(ctx):
    ctx.scenes.switch(TitleScene(ctx))
    ctx.scenes.apply_pending()
    steps(ctx, 5)
    tap(ctx, "Return")
    steps(ctx)
    assert isinstance(ctx.scenes.current, SetupScene)
    tap(ctx, "Return")  # cursor starts on "fight"
    steps(ctx)
    fight = ctx.scenes.current
    assert isinstance(fight, FightScene)
    assert fight.rounds_to_win == 3
    steps(ctx, 150)
    tap(ctx, "Escape")
    steps(ctx)
    assert fight.pause_menu is not None
    frozen = fight.rounds.phase_f
    steps(ctx, 30)
    assert fight.rounds.phase_f == frozen  # the fight waits while paused
    for key in ("Down", "Down", "Return"):  # "quit the fight"
        tap(ctx, key)
        steps(ctx)
    assert isinstance(ctx.scenes.current, TitleScene)


def test_setup_changes_and_saves_the_control_preset(ctx):
    ctx.scenes.switch(SetupScene(ctx))
    ctx.scenes.apply_pending()
    for key in ("Up", "Right"):  # from "fight", one up is "controls"
        tap(ctx, key)
        steps(ctx)
    assert ctx.controls.active == "shared_keyboard"
    saved, _ = controls.load_controls(ctx.controls_path)
    assert saved.active == "shared_keyboard"


def test_result_menu_offers_a_rematch(ctx):
    scene = FightScene(ctx, rounds_to_win=1)
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()
    steps(ctx, ctx.scenes.current.rules.round_intro_f + 1)
    scene.rounds.match.fighters[1].hurt(10_000)
    steps(ctx, scene.rules.round_outro_f + 130)
    assert scene.result_menu is not None
    tap(ctx, "Return")
    steps(ctx)
    assert scene.result_menu is None and scene.rounds.round_number == 1
