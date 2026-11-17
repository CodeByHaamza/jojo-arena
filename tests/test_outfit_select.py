"""The select screen's outfit step: costume, colour and poses picked in one list, the
preview dressed as picked, and the second player kept off the first one's colour."""

from dataclasses import replace

import pygame
import pytest
from helpers import GREY, body, colored_sheet

from jojo_arena import controls
from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.context import GameContext
from jojo_arena.engine import font, i18n
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.engine.sprites import SheetSprites
from jojo_arena.paths import SPRITES_DIR
from jojo_arena.ui import select_scene, stage_scene
from jojo_arena.ui.loadout import Loadout
from jojo_arena.ui.select_scene import SIDE_W, CharacterSelectScene


def sheet_id(tmp_path, name: str, colors: int) -> str:
    colored_sheet(tmp_path, colors, name)
    return str(tmp_path / name)


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


@pytest.fixture
def roster(tmp_path, monkeypatch):
    """Two fighters on the select screen: `hero` (two colours, a costume of three and a
    costume of one) and `plain` (nothing to pick)."""
    dummy = get_fighter("mannequin_red")
    hero = replace(
        dummy,
        id="hero",
        selectable=True,
        part=3,
        palette={},
        sprite=sheet_id(tmp_path, "hero", 2),
        costumes={
            "alt": sheet_id(tmp_path, "hero_alt", 3),
            "mono": sheet_id(tmp_path, "hero_mono", 1),
        },
    )
    plain = replace(hero, id="plain", costumes={}, sprite=sheet_id(tmp_path, "plain", 0))
    found = {"hero": hero, "plain": plain}
    monkeypatch.setattr(select_scene, "load_roster", lambda: [hero, plain])
    monkeypatch.setattr(stage_scene, "get_fighter", lambda fighter_id: found[fighter_id])
    return found


def keys(ctx, *names: str):
    for name in names:
        code = KEY_SCANCODES[name]
        ctx.inputs.handle_event(pygame.event.Event(pygame.KEYDOWN, scancode=code, key=0, mod=0))
        ctx.inputs.handle_event(pygame.event.Event(pygame.KEYUP, scancode=code, key=0, mod=0))
        ctx.inputs.begin_step()
        ctx.scenes.current.update()
        ctx.scenes.apply_pending()
        ctx.scenes.current.draw(ctx.display.surface)


def select_on(ctx, mode="versus", fighter="hero") -> CharacterSelectScene:
    select = CharacterSelectScene(ctx, mode, cursor=fighter)
    ctx.scenes.switch(select)
    ctx.scenes.apply_pending()
    keys(ctx)  # one step, nothing pressed
    return select


def test_the_rows_are_only_those_with_a_choice(ctx, roster):
    select = select_on(ctx)
    keys(ctx, "Return")
    assert select.choosing == 0
    assert select.outfit_rows() == ["costume", "color"]  # these sheets have no pose
    assert select.choices("costume") == ["", "alt", "mono"]
    assert select.choices("color") == ["c0", "c1"]
    keys(ctx, "Left")  # around to the last costume: it has one colour
    assert select.loadout.costume == "mono"
    assert select.outfit_rows() == ["costume"]


def test_a_fighter_with_nothing_to_pick_is_picked_at_once(ctx, roster):
    select = select_on(ctx, fighter="plain")
    keys(ctx, "Return")
    assert select.choosing is None and select.fighter_ids == ("plain",)


def test_left_right_change_the_costume_and_the_colour_restarts(ctx, roster):
    select = select_on(ctx)
    keys(ctx, "Return", "Down", "Right")  # the colour row: the second colour
    assert select.loadout == Loadout(color="c1")
    keys(ctx, "Up", "Right")  # the costume row: the next costume, in its first colour
    assert (select.loadout.costume, select.loadout.color) == ("alt", "")
    assert select.choices("color") == ["c0", "c1", "c2"]
    keys(ctx, "Down", "Left")  # around the colours of that costume
    assert select.loadout.color == "c2"


def test_the_preview_wears_what_is_picked(ctx, roster):
    select = select_on(ctx)
    keys(ctx, "Return")
    assert body(select.step_look().sprites) == GREY
    keys(ctx, "Down", "Right")
    assert body(select.step_look().sprites) == (20, 10, 10)
    keys(ctx, "Up", "Right")  # another costume: its own sheet, as it is drawn
    assert list(select.step_look().sprites.colors) == ["c0", "c1", "c2"]
    assert body(select.step_look().sprites) == GREY


def test_confirm_commits_the_outfit_and_keeps_it_for_next_time(ctx, roster):
    select = select_on(ctx)
    keys(ctx, "Return", "Right", "Down", "Right", "Return")  # alt, its second colour
    assert select.choosing is None and select.fighter_ids == ("hero",)
    assert ctx.loadouts[0] == Loadout(costume="alt", color="c1")
    assert ctx.settings.outfits["hero"] == ["alt", "c1"]
    again = select_on(ctx)
    keys(ctx, "Return")
    assert (again.loadout.costume, again.loadout.color) == ("alt", "c1")  # offered first


def test_back_leaves_the_step_and_wears_nothing_new(ctx, roster):
    select = select_on(ctx)
    keys(ctx, "Return", "Right", "Escape")
    assert select.choosing is None and select.picks == []
    assert "hero" not in ctx.settings.outfits


def test_player_two_cannot_take_player_ones_colour(ctx, roster):
    select = select_on(ctx)
    keys(ctx, "Return", "Right", "Return")  # player 1: alt, in its first colour
    assert ctx.loadouts[0] == Loadout(costume="alt")
    keys(ctx, "Return")  # player 2 on the same fighter: offered the same costume...
    assert select.choosing == 1
    assert (select.loadout.costume, select.loadout.color) == ("alt", "c1")  # ...moved off c0
    assert select.choices("color") == ["c1", "c2"]
    keys(ctx, "Down", "Right", "Right")
    assert select.loadout.color == "c1"  # around, never through player 1's colour
    keys(ctx, "Up", "Right")  # the costume of one colour: nobody wears it, it is free
    assert (select.loadout.costume, select.loadout.color) == ("mono", "")
    keys(ctx, "Right")  # on to the normal costume: player 1 is not in it either
    assert (select.loadout.costume, select.loadout.color) == ("", "")
    assert select.choices("color") == ["c0", "c1"]


def test_the_picked_side_keeps_wearing_its_outfit_on_the_screen(ctx, roster):
    select = select_on(ctx)
    keys(ctx, "Return", "Down", "Right", "Return")  # player 1: the second colour
    assert body(select.worn[0].sprites) == (20, 10, 10)
    keys(ctx, "Escape")  # back: player 1 picks again
    assert select.picks == [] and select.worn == {}


def test_the_computer_picks_its_outfit_on_the_select_screen(ctx, roster):
    select = select_on(ctx, mode="vs_cpu")
    keys(ctx, "Return", "Return")  # player 1, as it is
    assert select.picking == 1
    keys(ctx, "Return")  # the computer gets the same fighter: no step, it picks by itself
    assert select.choosing is None and len(select.picks) == 2
    worn = ctx.loadouts[1]
    assert worn.costume in ("", "alt", "mono") and worn.color in ("c0", "c1", "c2")


@pytest.mark.parametrize("language", i18n.LANGUAGES)
def test_every_costume_colour_and_pose_name_fits_the_panel(language):
    """The active choice is written under the list, on two lines at most."""
    i18n.set_language(language)
    try:
        english = language == "en"
        names = []
        for fighter in load_roster():
            for sheet in filter(None, (fighter.sprite, *fighter.costumes.values())):
                base = SPRITES_DIR / sheet
                sprites = SheetSprites.load(base.with_suffix(".png"), base.with_suffix(".toml"))
                names.append(sprites.costume[1 if english else 0])
                names += [c.label_en if english else c.label for c in sprites.colors.values()]
                names += [p.label_en if english else p.label for p in sprites.poses.values()]
        for name in filter(None, names):
            assert len(font.wrap(f"< {name} >", SIDE_W - 10)) <= 2, name
    finally:
        i18n.set_language("fr")


def test_coming_back_to_the_screen_the_picked_side_still_wears_its_outfit(ctx, roster):
    """Back from the arena screen: player 1 is already picked, in what was chosen."""
    ctx.loadouts[0] = Loadout(color="c1")
    select = CharacterSelectScene(ctx, "versus", picks=("hero",), cursor="hero")
    assert select.picks == [0]
    assert body(select.worn[0].sprites) == (20, 10, 10)
    ctx.loadouts[0] = Loadout()
    plain = CharacterSelectScene(ctx, "versus", picks=("hero",), cursor="hero")
    assert plain.worn == {}  # the normal outfit: the look every screen already has
