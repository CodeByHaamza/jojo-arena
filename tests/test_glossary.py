"""The glossary: complete entries in both languages, pictures that exist, a scene to read it."""

import tomllib

import pygame
import pytest

from jojo_arena import controls
from jojo_arena.characters import load_roster
from jojo_arena.characters.glossary import KINDS, LORE_DIR, load_glossary
from jojo_arena.context import GameContext
from jojo_arena.engine import font, i18n
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.paths import SPRITES_DIR
from jojo_arena.ui.glossary_scene import DETAIL, LINE_H, TEXT_TOP, GlossaryScene
from jojo_arena.ui.icons import ICONS_DIR
from jojo_arena.ui.main_menu import MainMenuScene


@pytest.fixture(autouse=True)
def french_afterwards():
    yield
    i18n.set_language("fr")


def all_entries(glossary):
    return [e for part in glossary.values() for kind in KINDS for e in part[kind]]


def test_every_entry_is_complete_and_its_picture_exists():
    glossary = load_glossary()
    assert set(glossary) <= set(range(0, 10))  # 0 is the rules tab, not a part
    roster = {f.id for f in load_roster()}
    for part, sections in glossary.items():
        ids = [e.id for kind in KINDS for e in sections[kind]]
        assert len(ids) == len(set(ids)), part
    for entry in all_entries(glossary):
        assert entry.name and entry.text, entry.id
        if entry.kind == "terms":
            assert (ICONS_DIR / f"{entry.icon}.png").exists(), entry.icon
        elif entry.kind == "characters":
            assert entry.fighter in roster and entry.subtitle is not None, entry.id
        else:
            assert (SPRITES_DIR / f"{entry.sprite}.png").exists(), entry.sprite
            assert len(entry.stats) == 6 and set(entry.stats) <= set("ABCDE"), entry.id


def test_every_text_has_its_english_translation():
    for path in LORE_DIR.glob("part*.toml"):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        for kind in KINDS:
            for item in data.get(kind, []):
                for key in ("text", "family", "name_origin"):
                    if key in item:
                        assert f"{key}_en" in item, (path.stem, item["id"], key)


def test_every_fighter_and_stand_of_the_roster_has_its_entry():
    """Fill the glossary as characters come in: one entry for them, one for their Stand."""
    entries = all_entries(load_glossary())
    fighters = {e.fighter for e in entries if e.kind == "characters"}
    sprites = {e.sprite for e in entries if e.kind == "stands"}
    for fighter in load_roster():
        if fighter.selectable:
            assert fighter.id in fighters, f"add {fighter.id} to characters/lore/"
            if fighter.stand_sprite:
                assert fighter.stand_sprite in sprites, f"add {fighter.stand_name} to lore/"


def test_every_glossary_text_can_be_drawn_in_both_languages():
    strings = []
    for code in i18n.LANGUAGES:
        i18n.set_language(code)
        for e in all_entries(load_glossary()):
            strings += [e.name, e.text, e.family, e.name_origin, e.subtitle]
    missing = {c for s in strings for c in s.upper() if c not in font.GLYPHS}
    assert missing == set()


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


def test_the_glossary_opens_from_the_menu_and_is_browsed(ctx):
    menu = MainMenuScene(ctx, cursor="glossary")
    ctx.scenes.switch(menu)
    ctx.scenes.apply_pending()
    press(ctx, "Return")
    scene = ctx.scenes.current
    assert isinstance(scene, GlossaryScene)
    assert scene.part == 1 and scene.kind == "terms" and scene.entry.id == "stone_mask"
    press(ctx, "E", "E")  # part 3
    assert scene.part == 3 and scene.backdrop.part == 3
    press(ctx, "Right", "Down")  # characters, the second one
    assert scene.kind == "characters" and scene.entry.id == "kakyoin"
    pages = len(scene._pages())
    press(ctx, "Return")
    assert scene.page == (1 if pages > 1 else 0)
    press(ctx, "E", "E", "E")  # part 6: nothing yet, still drawn
    assert scene.part == 6 and scene.entry is None
    press(ctx, "Escape")
    assert isinstance(ctx.scenes.current, MainMenuScene)
    assert ctx.scenes.current.menu.selected.key == "glossary"


def test_long_texts_are_cut_into_pages_that_fit(ctx):
    per_page = (DETAIL.bottom - 4 - TEXT_TOP) // LINE_H
    for code in i18n.LANGUAGES:
        i18n.set_language(code)
        scene = GlossaryScene(ctx)
        for part, sections in scene.glossary.items():
            for kind in KINDS:
                for index in range(len(sections[kind])):
                    scene.part, scene.kind, scene.index = part, kind, index
                    pages = scene._pages()
                    assert all(len(page) <= per_page for page in pages)
                    assert all(page[0][0] for page in pages if page)  # no blank line on top
