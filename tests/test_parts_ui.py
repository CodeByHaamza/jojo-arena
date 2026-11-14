"""The whole saga in the menus: nine parts, their emblems, the character select tabs."""

import pygame
import pytest
from make_icons import drawings, render_icon

from jojo_arena import controls
from jojo_arena.characters import load_parts, load_roster
from jojo_arena.context import GameContext
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.ui.backdrop import CYCLE_F, MenuBackdrop
from jojo_arena.ui.icons import ICONS_DIR
from jojo_arena.ui.select_scene import CharacterSelectScene
from jojo_arena.ui.title_scene import GROUP_F, TitleScene


def test_nine_parts_each_with_an_emblem_that_exists():
    parts = load_parts()
    assert [p.number for p in parts] == list(range(1, 10))
    for part in parts:
        assert part.title and part.setting
        assert (ICONS_DIR / f"{part.emblem}.png").exists(), part.emblem


def test_every_selectable_fighter_belongs_to_a_part():
    for fighter in load_roster():
        if fighter.selectable:
            assert 1 <= fighter.part <= 9, fighter.id


def test_icons_are_up_to_date_with_their_drawings():
    """The PNG in assets must match its drawing (run tools/make_icons.py)."""
    for path in drawings():
        drawn = render_icon(path)
        on_disk = pygame.image.load(str(ICONS_DIR / f"{path.stem}.png"))
        assert pygame.image.tobytes(drawn, "RGBA") == pygame.image.tobytes(on_disk, "RGBA"), (
            f"{path.stem}: run python tools/make_icons.py"
        )


def test_the_backdrop_takes_turns_through_the_parts_unless_one_is_chosen():
    backdrop = MenuBackdrop()
    parts = {p.number: p for p in load_parts()}
    assert backdrop.colors(0) == parts[1].colors
    assert backdrop.colors(CYCLE_F) == parts[2].colors
    backdrop.part = 5
    assert backdrop.colors(CYCLE_F * 3) == parts[5].colors
    surface = pygame.Surface((480, 270))
    backdrop.draw(surface, 10)  # draws without a window


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


def press(ctx, *names: str):
    for name in names:
        code = KEY_SCANCODES[name]
        ctx.inputs.handle_event(pygame.event.Event(pygame.KEYDOWN, scancode=code, key=0, mod=0))
        ctx.inputs.handle_event(pygame.event.Event(pygame.KEYUP, scancode=code, key=0, mod=0))
        ctx.inputs.begin_step()
        ctx.scenes.current.update()
        ctx.scenes.apply_pending()
        ctx.scenes.current.draw(ctx.display.surface)


def test_the_select_screen_has_a_tab_per_part(ctx):
    select = CharacterSelectScene(ctx, "versus", cursor="kakyoin")
    ctx.scenes.switch(select)
    ctx.scenes.apply_pending()
    assert select.tab == 3 and select.roster[select.cursor].id == "kakyoin"
    assert select.backdrop.part == 3
    press(ctx, "E")  # next tab: part 4, nobody yet
    assert select.tab == 4 and select.cursor is None and select.backdrop.part == 4
    press(ctx, "Return")
    assert select.picks == [] and select.toast_f > 0
    press(ctx, "Q", "Return")  # back to part 3, pick Kakyoin
    assert select.fighter_ids == ("kakyoin",)
    press(ctx, "Q", "Q")  # part 1, then the picked fighter is not on screen
    assert select.tab == 1
    press(ctx, "Escape")  # undo the pick: back on Kakyoin's tab and cell
    assert select.picks == [] and select.tab == 3 and select.roster[select.cursor].id == "kakyoin"


def test_the_title_screen_shows_one_part_at_a_time(ctx):
    title = TitleScene(ctx)
    ctx.scenes.switch(title)
    ctx.scenes.apply_pending()
    parts_with_fighters = {f.part for f in load_roster() if f.selectable}
    assert [number for number, _ in title.groups] == sorted(parts_with_fighters)
    for _ in range(GROUP_F + 1):
        title.update()
    title.draw(ctx.display.surface)
    assert title.backdrop.part == title.group[0]


def test_every_fighter_stands_in_one_camp_or_the_other():
    """The title screen faces the two camps off; nobody may be missing from it."""
    for fighter in load_roster():
        if fighter.selectable:
            assert fighter.side in ("hero", "villain"), fighter.id


def test_each_part_brings_both_camps_to_the_title_screen():
    """A part with only heroes on screen would not be that part's fight."""
    for part in {f.part for f in load_roster() if f.selectable}:
        cast = [f for f in load_roster() if f.selectable and f.part == part]
        assert {f.side for f in cast} == {"hero", "villain"}, part
