"""French and English: every text exists in both, data files translate, the choice is saved."""

import json
import string
import tomllib
from pathlib import Path

import pygame
import pytest

from jojo_arena import controls
from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.context import GameContext
from jojo_arena.engine import font, i18n
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.settings import Settings, load_settings, save_settings, settings_path
from jojo_arena.stages import load_stage
from jojo_arena.ui import text
from jojo_arena.ui.labels import keyboard_label, pad_label
from jojo_arena.ui.options_scene import OptionsScene

ROOT = Path(__file__).resolve().parents[1]
NOT_KITS = ("roster", "parts")
KITS = [p for p in (ROOT / "jojo_arena" / "characters").glob("*.toml") if p.stem not in NOT_KITS]


@pytest.fixture(autouse=True)
def french_afterwards():
    yield
    i18n.set_language("fr")


def placeholders(value: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(value) if name}


def flatten(value) -> list[str]:
    if isinstance(value, dict):
        return [s for v in value.values() for s in flatten(v)]
    if isinstance(value, list):
        return [s for v in value for s in flatten(v)]
    return [value]


def test_every_text_exists_in_english_with_the_same_placeholders():
    assert set(text.EN) == set(text.FR)
    for key, french in text.FR.items():
        english = text.EN[key]
        if isinstance(french, dict):
            assert set(english) == set(french), key
        elif isinstance(french, list):
            assert len(english) == len(french), key
        else:
            assert placeholders(english) == placeholders(french), key


def test_text_follows_the_current_language():
    assert text.FIGHT == "COMBATTRE"
    i18n.set_language("en")
    assert text.FIGHT == "FIGHT" and text.PLAYER_N.format(n=2) == "P2"
    assert keyboard_label("Space") == "SPACE" and pad_label("a", "playstation") == "CROSS"
    with pytest.raises(ValueError):
        i18n.set_language("xx")


def test_localized_takes_the_translation_or_the_original():
    data = {"label": "DIRECT", "label_en": "JAB", "info": "Rapide"}
    assert i18n.localized(data, "label") == "DIRECT"
    i18n.set_language("en")
    assert i18n.localized(data, "label") == "JAB"
    assert i18n.localized(data, "info") == "Rapide"
    assert i18n.localized(data, "shout", "-") == "-"


def test_characters_and_stages_load_in_the_current_language():
    jab = get_fighter("jotaro_p3").kit.move("base", "light")
    assert jab.label == "DIRECT DE DÉLINQUANT"
    i18n.set_language("en")
    jotaro = get_fighter("jotaro_p3")
    assert jotaro.kit.move("base", "light").label == "DELINQUENT'S JAB"
    assert jotaro.role == "BRAWLER - SHORT RANGE"
    assert jotaro.kit.stance_labels["base"] == "NO STAND"
    assert load_stage("cairo_night").name == "Cairo, a street at night"


def test_every_described_move_is_translated():
    for path in KITS:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        moves = [m for s in data.get("stances", {}).values() for m in s.get("moves", {}).values()]
        moves += list(data.get("moves", {}).values())
        for move in moves:
            if "info" in move:
                assert "info_en" in move, (path.stem, move.get("label"))


def test_every_text_can_be_drawn_in_both_languages():
    strings = []
    for code in i18n.LANGUAGES:
        i18n.set_language(code)
        strings += [s for table in text.TABLES.values() for s in flatten(table)]
        for fighter in load_roster():
            strings += [fighter.name, fighter.stand_name, fighter.role, fighter.blurb]
            strings += list(fighter.kit.stance_labels.values())
            for move in fighter.kit.all_moves():
                strings += [move.label, move.info, move.shout]
    missing = {c for s in strings for c in s.upper() if c not in font.GLYPHS and c not in "{}"}
    assert missing == set()


def test_settings_are_saved_and_read_back(tmp_path):
    path = settings_path(tmp_path / "controls.json")
    save_settings(Settings(language="en"), path)
    assert load_settings(path).language == "en"
    path.write_text("{not json", encoding="utf-8")
    assert load_settings(path).language in i18n.LANGUAGES
    path.write_text(json.dumps({"language": "klingon"}), encoding="utf-8")
    assert load_settings(path).language in i18n.LANGUAGES


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


def test_the_options_switch_the_language_and_save_it(ctx):
    scene = OptionsScene(ctx)
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()
    scene.menu.select("language")
    code = KEY_SCANCODES["Right"]
    ctx.inputs.handle_event(pygame.event.Event(pygame.KEYDOWN, scancode=code, key=0, mod=0))
    ctx.inputs.handle_event(pygame.event.Event(pygame.KEYUP, scancode=code, key=0, mod=0))
    ctx.inputs.begin_step()
    ctx.scenes.current.update()
    ctx.scenes.apply_pending()
    assert i18n.language() == "en"
    assert load_settings(settings_path(ctx.controls_path)).language == "en"
    rebuilt = ctx.scenes.current
    assert rebuilt is not scene and rebuilt.menu.selected.key == "language"
    assert rebuilt.menu.item("back").label == "BACK"
