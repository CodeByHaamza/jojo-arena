import pygame
import pytest

from jojo_arena import controls
from jojo_arena.characters import load_roster
from jojo_arena.combat.rules import load_rules
from jojo_arena.combat.training import Dummy, Training
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.ui import text
from jojo_arena.ui.fight_scene import FightScene
from jojo_arena.ui.labels import keyboard_label, move_label, pad_label
from jojo_arena.ui.main_menu import MainMenuScene
from jojo_arena.ui.menu import Menu, MenuItem
from jojo_arena.ui.movelist import build_pages
from jojo_arena.ui.options_scene import OptionsScene
from jojo_arena.ui.select_scene import CharacterSelectScene
from jojo_arena.ui.setup_scene import SetupScene
from jojo_arena.ui.title_scene import TitleScene
from jojo_arena.ui.training_scene import TrainingScene


def test_every_ui_string_can_be_drawn():
    strings = [v for k, v in vars(text).items() if k.isupper() and isinstance(v, str)]
    strings += list(text.ACTION_NAMES.values())
    for fighter in load_roster():
        strings += [fighter.name, fighter.stand_name, fighter.role, fighter.blurb]
        strings += list(fighter.kit.stance_labels.values())
        for move in fighter.kit.all_moves():
            strings += [move.label, move.info]
    missing = {c for s in strings for c in s.upper() if c not in font.GLYPHS and c not in "{}"}
    assert missing == set()


def test_text_size_matches_render():
    image = font.render("K.O.", (255, 255, 255), scale=2, outline=None)
    assert image.get_width() == font.text_width("K.O.", 2)
    assert image.get_height() == font.HEIGHT * 2


def test_text_wraps_at_spaces():
    lines = font.wrap("ORA ORA ORA ORA", font.text_width("ORA ORA"))
    assert lines == ["ORA ORA", "ORA ORA"]


def test_menu_navigation_wraps_and_changes_values():
    menu = Menu([MenuItem("a", "A", ["1", "3", "5"]), MenuItem("b", "B")])
    assert menu.handle(InputFrame(press_counts={"up": 1})) is None
    assert menu.selected.key == "b"
    assert menu.handle(InputFrame(press_counts={"confirm": 1})) == ("confirm", "b")
    menu.handle(InputFrame(press_counts={"down": 1}))
    assert menu.handle(InputFrame(press_counts={"left": 1})) == ("change", "a")
    assert menu.selected.value == "5"
    assert menu.handle(InputFrame(press_counts={"back": 1})) == ("back", "")


def test_disabled_menu_items_are_locked():
    menu = Menu([MenuItem("soon", "SOON", enabled=False), MenuItem("ok", "OK")])
    assert menu.handle(InputFrame(press_counts={"confirm": 1})) == ("locked", "soon")
    menu.handle(InputFrame(press_counts={"down": 1}))
    assert menu.handle(InputFrame(press_counts={"confirm": 1})) == ("confirm", "ok")


def test_move_list_shows_every_move_of_every_character():
    rules = load_rules()
    config, _ = controls.parse_controls(None)
    player = config.presets["keyboard_gamepad"].players[0]
    for fighter in load_roster():
        if not fighter.selectable:
            continue
        pages = build_pages(fighter, player, rules)
        names = {entry.name for page in pages for entry in page.entries}
        for move in fighter.kit.all_moves():
            assert move.label and move.label in names, (fighter.id, move.name)
        alts = [e for p in pages for e in p.entries if e.keys[:1] == (text.DIRECTION,)]
        assert alts and all(e.keys[1] in ("L", "O") for e in alts)  # special or Heart Heat


def test_input_labels():
    assert keyboard_label("Space") == "ESPACE"
    assert keyboard_label("KP_4") == "PAVÉ 4"
    assert pad_label("rightshoulder") == "RB"
    assert pad_label("a", "playstation") == "CROIX"
    config, _ = controls.parse_controls(None)
    p1, p2 = config.presets["keyboard_gamepad"].players
    assert move_label(p2) == "STICK"
    assert len(move_label(p1)) == 4  # WASD, or ZQSD on an AZERTY keyboard


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


def keys(ctx, *names: str):
    for name in names:
        tap(ctx, name)
        steps(ctx)


def start(ctx, scene):
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()
    steps(ctx)
    return scene


def test_title_to_local_fight_to_pause_and_back(ctx):
    start(ctx, TitleScene(ctx))
    keys(ctx, "Return")
    assert isinstance(ctx.scenes.current, MainMenuScene)
    keys(ctx, "Up", "Up", "Return")  # from "training", up twice is "local fight"
    select = ctx.scenes.current
    assert isinstance(select, CharacterSelectScene) and select.mode == "versus"
    keys(ctx, "Return", "Right", "Return")  # J1 and J2 pick
    setup = ctx.scenes.current
    assert isinstance(setup, SetupScene)
    assert setup.fighter_ids == (select.roster[0].id, select.roster[1].id)
    keys(ctx, "Return")  # cursor starts on "fight"
    fight = ctx.scenes.current
    assert isinstance(fight, FightScene)
    assert fight.rounds_to_win == 3 and fight.fighter_ids == setup.fighter_ids
    steps(ctx, 150)
    keys(ctx, "Escape")
    assert fight.pause_menu is not None
    frozen = fight.rounds.phase_f
    steps(ctx, 30)
    assert fight.rounds.phase_f == frozen  # the fight waits while paused
    keys(ctx, "Down", "Return")  # move list of the player who paused
    assert fight.move_list is not None and fight.move_list.fdef == fight.fighter_defs[0]
    keys(ctx, "Escape")
    assert fight.move_list is None and fight.pause_menu is not None
    keys(ctx, "Down", "Down", "Down", "Return")  # last item: main menu
    assert isinstance(ctx.scenes.current, MainMenuScene)
    assert ctx.scenes.current.menu.selected.key == "versus"


def test_soon_modes_cannot_be_opened(ctx):
    menu = start(ctx, MainMenuScene(ctx))
    keys(ctx, "Up", "Return")  # "versus the computer": not there yet
    assert ctx.scenes.current is menu
    assert menu.toast_f > 0
    assert not menu.menu.selected.enabled and menu.menu.selected.tag == text.SOON


def test_training_flow(ctx):
    start(ctx, MainMenuScene(ctx))
    keys(ctx, "Return")
    select = ctx.scenes.current
    assert isinstance(select, CharacterSelectScene) and select.mode == "training"
    keys(ctx, "Return")  # player 1
    keys(ctx, "Escape")  # changed my mind
    assert select.picks == []
    keys(ctx, "Return", "Right", "Right", "Return")  # player 1, then the dummy
    training = ctx.scenes.current
    assert isinstance(training, TrainingScene)
    assert isinstance(training.rounds, Training)
    assert training.fighter_ids == (select.roster[0].id, select.roster[2].id)
    steps(ctx, 10)
    keys(ctx, "Escape")
    keys(ctx, "Down", "Down", "Right")  # dummy: stand still -> guard
    assert training.dummy == Dummy.GUARD
    keys(ctx, "Down", "Right")  # life: infinite -> normal
    assert training.rounds.infinite_life is False
    keys(ctx, "Escape")
    steps(ctx, 10)
    assert training.rounds.match.fighters[1].state.name == "GUARD"
    keys(ctx, "Escape")
    while training.pause_menu.selected.key != "change":  # "change fighters"
        keys(ctx, "Down")
    keys(ctx, "Return")
    assert isinstance(ctx.scenes.current, CharacterSelectScene)


def test_locked_cells_and_the_move_list_in_the_select_screen(ctx):
    select = start(ctx, CharacterSelectScene(ctx, "versus"))
    keys(ctx, "Tab")
    assert select.move_list is not None
    keys(ctx, "Right")
    assert select.move_list.page == 1
    keys(ctx, "Escape")
    assert select.move_list is None
    keys(ctx, "Down", "Return")  # an empty cell
    assert select.picks == [] and select.toast_f > 0
    keys(ctx, "Escape")
    assert isinstance(ctx.scenes.current, MainMenuScene)


def test_options_change_the_preset(ctx):
    start(ctx, OptionsScene(ctx))
    keys(ctx, "Right")
    assert ctx.controls.active == "shared_keyboard"
    keys(ctx, "Escape")
    assert isinstance(ctx.scenes.current, MainMenuScene)


def test_setup_changes_and_saves_the_control_preset(ctx):
    start(ctx, SetupScene(ctx))
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


def hold_key(ctx, key: str, frames: int):
    code = KEY_SCANCODES[key]
    ctx.inputs.handle_event(pygame.event.Event(pygame.KEYDOWN, scancode=code, key=0, mod=0))
    steps(ctx, frames)
    ctx.inputs.handle_event(pygame.event.Event(pygame.KEYUP, scancode=code, key=0, mod=0))


@pytest.mark.parametrize("preset", ["keyboard_gamepad", "two_gamepads", "shared_keyboard"])
def test_player_one_always_moves_with_the_keyboard_without_pads(ctx, preset):
    ctx.controls.active = preset
    scene = start(ctx, TrainingScene(ctx, fighter_ids=("jotaro_p3", "kakyoin")))
    x = scene.rounds.match.fighters[0].pos.x
    hold_key(ctx, "D", 30)  # D on QWERTY, the same key as D on AZERTY
    assert scene.rounds.match.fighters[0].pos.x > x + 10


def test_a_lone_pad_plays_player_one_in_training(ctx):
    from jojo_arena.engine.input import PadState

    pad = PadState(instance_id=7)
    ctx.inputs.pads.append(pad)  # "J1 keyboard, J2 pad": the pad is player 2's...
    scene = start(ctx, TrainingScene(ctx, fighter_ids=("jotaro_p3", "kakyoin")))
    x = scene.rounds.match.fighters[0].pos.x
    pad.held.add("dpad_right")
    steps(ctx, 30)
    assert scene.rounds.match.fighters[0].pos.x > x + 10  # ...but alone, it moves player 1
