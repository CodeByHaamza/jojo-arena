"""Costumes and colours in the game: an outfit goes from the roster to every screen, two
players on the same fighter never look the same, and the fight itself never knows."""

import random
from dataclasses import replace

import pygame
import pytest
from helpers import GREY, body, colored_sheet

from jojo_arena import controls
from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.context import GameContext
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.settings import Settings, parse_settings
from jojo_arena.ui import fight_scene
from jojo_arena.ui.fight_scene import FightScene
from jojo_arena.ui.fight_view import FighterView
from jojo_arena.ui.loadout import (
    Loadout,
    distinct,
    outfit_colors,
    outfit_sheet,
    random_outfit,
    settle,
)
from jojo_arena.ui.portraits import FighterLook


def sheet_id(tmp_path, name: str, colors: int) -> str:
    """A sheet built in tmp_path, named the way a roster names one (no extension). An
    absolute path: the game joins it to its sprites folder and gets it back as it is."""
    colored_sheet(tmp_path, colors, name)
    return str(tmp_path / name)


@pytest.fixture
def hero(tmp_path):
    """A fighter with two colours, a costume of three, a costume of one, and a Stand."""
    return replace(
        get_fighter("mannequin_red"),
        id="hero",
        palette={},
        sprite=sheet_id(tmp_path, "hero", 2),
        costumes={
            "alt": sheet_id(tmp_path, "hero_alt", 3),
            "mono": sheet_id(tmp_path, "hero_mono", 1),
        },
        stand_sprite=sheet_id(tmp_path, "hero_stand", 2),
    )


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


# From the roster to the sheet -----------------------------------------------------------------


def test_the_roster_lists_a_fighters_costumes_in_order(hero):
    assert list(hero.costumes) == ["alt", "mono"]
    assert all(f.costumes == {} or f.sprite for f in load_roster())  # a costume needs a base


def test_a_costume_is_its_own_sheet(hero):
    assert outfit_sheet(hero, Loadout()) == hero.sprite
    assert outfit_sheet(hero, Loadout(costume="alt")) == hero.costumes["alt"]
    assert outfit_sheet(hero, Loadout(costume="gone")) == hero.sprite
    assert outfit_colors(hero) == ["c0", "c1"]
    assert outfit_colors(hero, "alt") == ["c0", "c1", "c2"]
    assert outfit_colors(hero, "mono") == ["c0"]
    assert outfit_colors(get_fighter("mannequin_red")) == []  # a sheet with no colours


def test_a_colour_repaints_the_fighter_and_names_its_stands_colour(hero):
    plain = FighterView(hero, Loadout())
    assert body(plain.sprites) == GREY and body(plain.stand) == GREY
    painted = FighterView(hero, Loadout(color="c1"))
    assert body(painted.sprites) == (20, 10, 10)
    # The sheets' second colour says `stand = "s1"`: the Stand has none of that name here.
    assert body(painted.stand) == GREY
    assert painted.loadout.color == "c1" and painted.loadout.costume == ""


def test_the_stand_wears_the_colour_its_users_colour_names(hero, tmp_path):
    # A Stand sheet whose colours are named as the user's colour asks ("s1").
    png, spec = colored_sheet(tmp_path, 2, "hero_stand")
    spec.write_text(spec.read_text(encoding="utf-8").replace("colors.c1", "colors.s1"), "utf-8")
    assert body(FighterView(hero, Loadout(color="c1")).stand) == (20, 10, 10)
    assert body(FighterView(hero, Loadout()).stand) == GREY


def test_a_costume_is_worn_with_its_own_colours(hero):
    view = FighterView(hero, Loadout(costume="alt", color="c2"))
    assert body(view.sprites) == (40, 10, 10)
    assert view.loadout.costume == "alt" and view.loadout.color == "c2"
    look = FighterLook(hero, Loadout(costume="alt", color="c2"))
    assert body(look.sprites) == (40, 10, 10) and look.loadout.color == "c2"
    assert body(FighterLook(hero).sprites) == GREY  # nothing asked: the normal outfit


def test_an_outfit_that_is_gone_falls_back(hero):
    """An old settings file: a costume removed since, a colour the costume never had."""
    view = FighterView(hero, Loadout(costume="removed", color="c1"))
    assert view.loadout.costume == "" and view.loadout.color == "c1"  # normal costume, its c1
    view = FighterView(hero, Loadout(costume="alt", color="never"))
    assert view.loadout == Loadout(costume="alt") and body(view.sprites) == GREY
    assert settle([hero], [Loadout(costume="removed", color="never")]) == [Loadout()]


# Two players on the same fighter ---------------------------------------------------------------


def test_a_mirror_match_never_shows_twice_the_same(hero):
    colors = ["c0", "c1", "c2"]
    assert distinct(Loadout(), Loadout(), colors) == Loadout(color="c1")
    assert distinct(Loadout(color="c1"), Loadout(color="c1"), colors) == Loadout(color="c2")
    assert distinct(Loadout(color="c2"), Loadout(color="c2"), colors) == Loadout(color="c0")
    assert distinct(Loadout(), Loadout(color="c0"), colors) == Loadout(color="c1")  # "" is c0
    assert distinct(Loadout(color="c1"), Loadout(), colors) == Loadout()  # already different
    first, second = settle([hero, hero], [Loadout(), Loadout()])
    assert (first.color, second.color) == ("", "c1")
    views = [FighterView(hero, first), FighterView(hero, second)]
    assert body(views[0].sprites) != body(views[1].sprites)


def test_the_poses_survive_the_change_of_colour(hero):
    moved = distinct(Loadout("p", "sp"), Loadout("q", "sq"), ["c0", "c1"])
    assert moved == Loadout("q", "sq", color="c1")


def test_a_mirror_match_with_one_colour_stays_as_it_is(hero):
    mono = Loadout(costume="mono")
    assert distinct(mono, mono, ["c0"]) == mono
    assert distinct(Loadout(), Loadout(), []) == Loadout()  # a sheet with no colours at all
    assert settle([hero, hero], [mono, mono]) == [mono, mono]
    plain = get_fighter("jotaro_p3")
    assert settle([plain, plain], [Loadout(), Loadout()])[0] == Loadout()


def test_different_costumes_keep_the_colour_each_picked(hero):
    first, second = Loadout(color="c1"), Loadout(costume="alt", color="c1")
    assert settle([hero, hero], [first, second]) == [first, second]


def test_two_different_fighters_may_wear_the_same_colour(hero):
    other = replace(hero, id="other")
    assert settle([hero, other], [Loadout(color="c1"), Loadout(color="c1")]) == [
        Loadout(color="c1"),
        Loadout(color="c1"),
    ]


# The computer -----------------------------------------------------------------------------


def test_the_computer_picks_an_outfit_too(hero):
    picks = {random_outfit(hero, random.Random(seed)) for seed in range(60)}
    assert {(p.costume, p.color) for p in picks} == {
        ("", "c0"),
        ("", "c1"),
        ("alt", "c0"),
        ("alt", "c1"),
        ("alt", "c2"),
        ("mono", "c0"),
    }
    assert random_outfit(get_fighter("jotaro_p3"), random.Random(1)) in (
        Loadout(),
        *(Loadout(color=c) for c in outfit_colors(get_fighter("jotaro_p3"))),
    )


# Kept between sessions ----------------------------------------------------------------------


def test_the_settings_keep_the_outfits():
    settings = Settings()
    settings.outfits["hero"] = ["alt", "c2"]
    data = settings.to_json()
    assert data["outfits"] == {"hero": ["alt", "c2"]}
    assert parse_settings(data).outfits == {"hero": ["alt", "c2"]}
    broken = {"outfits": {"a": ["x"], "b": "nope", "c": ["alt", 3], "d": ["", "c1"]}}
    assert parse_settings(broken).outfits == {"d": ["", "c1"]}
    assert parse_settings({}).outfits == {}


# In a fight ---------------------------------------------------------------------------------


def _fight(ctx, monkeypatch, hero, loadouts):
    monkeypatch.setattr(fight_scene, "get_fighter", lambda fighter_id: hero)
    ctx.loadouts[:] = loadouts
    scene = FightScene(ctx, rounds_to_win=1, fighter_ids=("hero", "hero"), bots=(False, True))
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()
    for _ in range(240):
        ctx.inputs.begin_step()
        scene.update()
    return scene


def test_a_fight_dresses_both_sides_and_keeps_them_apart(ctx, monkeypatch, hero):
    scene = _fight(ctx, monkeypatch, hero, [Loadout(costume="alt", color="c1"), Loadout()])
    one, two = scene.view.fighter_views
    assert (one.loadout.costume, one.loadout.color) == ("alt", "c1")
    assert body(one.sprites) == (20, 10, 10)
    assert two.loadout.costume in ("", "alt", "mono")  # the computer picked its own
    assert (two.loadout.costume, two.loadout.color or "c0") != ("alt", "c1")
    scene.draw(pygame.Surface((480, 270)))


def test_a_replay_plays_the_same_fight_whatever_is_worn(ctx, monkeypatch, hero):
    """What is worn never reaches the fight: same moves, same positions, same recording."""

    def played(loadouts):
        scene = _fight(ctx, monkeypatch, hero, loadouts)
        fighters = scene.rounds.match.fighters
        state = [(f.pos.x, f.pos.y, f.hp, f.state, f.facing.x) for f in fighters]
        return state, list(scene.replay.frames), scene.replay_meta()

    plain = played([Loadout(), Loadout()])
    dressed = played([Loadout(costume="alt", color="c2"), Loadout(costume="mono")])
    assert plain == dressed
    assert not {"outfits", "costume", "color", "loadouts"} & set(plain[2])


def test_an_arcade_opponent_does_not_inherit_what_player_two_last_wore(ctx):
    from jojo_arena.ui.arcade_scene import ArcadeFight, ArcadeScene

    arcade = ArcadeScene(ctx, "jotaro_p3")
    ctx.loadouts[1] = Loadout("some_pose", "", costume="alt", color="c2")
    ArcadeFight(ctx, arcade)
    assert ctx.loadouts[1] == Loadout()


# The first costumes -------------------------------------------------------------------------


def _sheet(name: str):
    from jojo_arena.engine.sprites import SheetSprites
    from jojo_arena.paths import SPRITES_DIR

    base = SPRITES_DIR / name
    return SheetSprites.load(base.with_suffix(".png"), base.with_suffix(".toml"))


def test_every_roster_costume_has_its_sheet_two_colours_and_its_sources():
    """A fighter with costumes: every outfit, the normal one included, is named and
    sourced, and comes in two colours at least (so a mirror match can be told apart)."""
    for fighter in load_roster():
        if not fighter.costumes:
            continue
        for sheet_name in (fighter.sprite, *fighter.costumes.values()):
            sheet = _sheet(sheet_name)
            assert sheet is not None, sheet_name
            assert all(sheet.costume), f"{sheet_name}: [costume] label, label_en, source"
            assert len(sheet.colors) >= 2, f"{sheet_name}: two colours at least"
            for color in sheet.colors.values():
                assert color.label and color.label_en and color.source, (sheet_name, color.id)


def test_jonathan_wears_what_asbr_and_eoh_give_him():
    jonathan = get_fighter("jonathan")
    assert list(jonathan.costumes) == ["shirtless", "inherited_soul"]
    assert outfit_colors(jonathan) == ["anime", "tome4", "tome3", "j534"]
    assert outfit_colors(jonathan, "shirtless") == ["anime", "inverse"]
    assert outfit_colors(jonathan, "inherited_soul") == ["blanc", "noir"]
    # Shirtless is another body, not another colour: no top on that sheet.
    assert _sheet(jonathan.costumes["shirtless"]).costume[0]


def test_the_crusaders_and_dio_wear_what_the_games_give_them():
    jotaro, dio, avdol = (get_fighter(i) for i in ("jotaro_p3", "dio_p3", "avdol"))
    assert list(jotaro.costumes) == ["coatless", "inherited_soul"]
    assert outfit_colors(jotaro) == ["anime", "tome16", "tome26", "tome24"]
    assert outfit_colors(jotaro, "coatless") == ["anime", "manga"]
    assert list(dio.costumes) == ["shadow"]
    assert outfit_colors(dio) == ["anime", "jump7", "asb", "j367"]
    assert outfit_colors(dio, "shadow") == ["apparition", "statue"]
    assert list(avdol.costumes) == ["father"]
    assert outfit_colors(avdol) == ["anime", "chapitre136", "asbr", "j039"]
    assert outfit_colors(avdol, "father") == ["anime", "manga"]


def test_a_stand_follows_the_colour_its_user_names():
    """Each Stand has the two tints of the games; one colour of its user calls the second."""
    for fighter_id, color, stand_color in (
        ("jotaro_p3", "tome16", "tome17"),
        ("dio_p3", "jump7", "sas"),
        ("avdol", "j039", "j083"),
    ):
        fighter = get_fighter(fighter_id)
        stand = _sheet(fighter.stand_sprite)
        assert list(stand.colors)[1] == stand_color, fighter_id
        assert _sheet(fighter.sprite).colors[color].stand == stand_color
        plain, dressed = FighterView(fighter, Loadout()), FighterView(fighter, Loadout(color=color))
        assert dressed.stand is not plain.stand  # another sheet: repainted
        assert FighterView(fighter, Loadout(color="anime")).stand is plain.stand
