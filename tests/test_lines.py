"""What two fighters say to each other: the data, the VS screen that plays it line by line
in the poses picked, and the winner's line and pose once the fight is over."""

import pygame
import pytest

from jojo_arena import controls
from jojo_arena.characters import load_roster
from jojo_arena.characters.lines import LINES_FILE, exchange_for, load_exchanges
from jojo_arena.combat.rounds import Phase
from jojo_arena.context import GameContext
from jojo_arena.engine import font, i18n
from jojo_arena.engine.data import load_toml
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.ui.fight_scene import WINNER_LINE_W, WINNER_POSE_AFTER_F, FightScene
from jojo_arena.ui.loadout import Loadout
from jojo_arena.ui.setup_scene import LINE_F, LINE_PAUSE_F, LINE_W, SetupScene


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


@pytest.fixture(autouse=True)
def french():
    i18n.set_language("fr")
    yield
    i18n.set_language("fr")


def start(ctx, scene):
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()
    return scene


def step(ctx, frames=1):
    for _ in range(frames):
        ctx.inputs.begin_step()
        ctx.scenes.current.update()
        ctx.scenes.apply_pending()


# The data ---------------------------------------------------------------------------------


def test_every_exchange_names_two_roster_fighters_its_speakers_and_its_source():
    roster = {f.id for f in load_roster()}
    entries = load_toml(LINES_FILE)["exchanges"]
    assert entries
    pairs = [frozenset(e["fighters"]) for e in entries]
    assert len(pairs) == len(set(pairs)), "one entry per pair"
    for entry in entries:
        a, b = entry["fighters"]
        assert a != b and {a, b} <= roster, entry["fighters"]
        assert entry["source"], entry["fighters"]  # nothing is made up: where it is from
        assert entry["intro"], entry["fighters"]
        assert {line["by"] for line in entry["intro"]} <= {a, b}
        assert set(entry.get("victory", {})) <= {a, b}


def test_every_line_exists_in_both_languages_and_can_be_drawn():
    strings = []
    for entry in load_toml(LINES_FILE)["exchanges"]:
        for line in [*entry["intro"], *entry.get("victory", {}).values()]:
            assert line["text"] and line["text_en"], entry["fighters"]
            strings += [line["text"], line["text_en"]]
    missing = {c for s in strings for c in s.upper() if c not in font.GLYPHS}
    assert missing == set()


@pytest.mark.parametrize("language", i18n.LANGUAGES)
def test_every_line_fits_where_it_is_shown(language):
    i18n.set_language(language)
    for exchange in load_exchanges().values():
        for _, line in exchange.intro:
            assert len(font.wrap(line, LINE_W)) <= 2, line  # two rows on the VS screen
        for line in exchange.victory.values():
            assert len(font.wrap(line, WINNER_LINE_W)) <= 2, line


def test_a_pair_says_the_same_whichever_side_each_is_on():
    one, other = exchange_for("jotaro_p3", "dio_p3"), exchange_for("dio_p3", "jotaro_p3")
    assert one is not None and one == other
    assert [who for who, _ in one.intro] == ["jotaro_p3", "dio_p3"]
    assert one.victory_line("jotaro_p3") and one.victory_line("dio_p3")
    assert one.victory_line("kakyoin") == ""


def test_a_pair_the_games_gave_nothing_to_says_nothing():
    assert exchange_for("jotaro_p3", "jotaro_p3") is None  # a mirror match
    assert exchange_for("bruford", "kakyoin") is None


def test_the_lines_follow_the_language():
    french_line = exchange_for("jotaro_p3", "dio_p3").intro[0][1]
    i18n.set_language("en")
    assert exchange_for("jotaro_p3", "dio_p3").intro[0][1] == "You bastard!"
    assert french_line != "You bastard!"


# The VS screen ----------------------------------------------------------------------------


def test_the_vs_screen_types_each_line_on_its_speakers_side(ctx):
    setup = start(ctx, SetupScene(ctx, ("dio_p3", "jotaro_p3")))  # DIO on the left here
    step(ctx, 3)
    side, line, typed = setup.spoken()
    assert side == 1  # Jotaro speaks first, wherever he stands
    assert 0 < typed < len(line)
    step(ctx, LINE_F - 10)
    assert setup.spoken()[2] == len(line)  # typed out, and it stays
    step(ctx, 10 + LINE_PAUSE_F)
    side, second, _ = setup.spoken()
    assert side == 0 and second != line  # DIO answers
    setup.draw(pygame.Surface((480, 270)))


def test_the_exchange_starts_over_after_a_while(ctx):
    setup = start(ctx, SetupScene(ctx, ("jotaro_p3", "dio_p3")))
    seen = set()
    for _ in range(900):
        step(ctx)
        said = setup.spoken()
        seen.add(None if said is None else said[0])
    assert seen == {None, 0, 1}
    setup.tick = (LINE_F + LINE_PAUSE_F) * 2 + 5  # both said: a silence...
    assert setup.spoken() is None


def test_a_pair_without_lines_keeps_the_vs_screen_quiet(ctx):
    setup = start(ctx, SetupScene(ctx, ("bruford", "kakyoin")))
    step(ctx, 30)
    assert setup.exchange is None and setup.spoken() is None
    setup.draw(pygame.Surface((480, 270)))


def test_the_vs_screen_strikes_the_poses_picked(ctx):
    ctx.loadouts[0] = Loadout("garde_eoh", "")
    setup = start(ctx, SetupScene(ctx, ("jonathan", "jotaro_p3")))
    anim, with_stand, _ = setup.pose_of(0)
    assert anim == "pose_garde_eoh" and not with_stand  # no Stand: the pose alone
    anim, with_stand, offset = setup.pose_of(1)
    assert anim.startswith("pose_") and with_stand and offset is not None  # with the Stand
    setup.draw(pygame.Surface((480, 270)))


# The end of the fight ---------------------------------------------------------------------


def _win(ctx, ids, winner=0):
    fight = start(ctx, FightScene(ctx, rounds_to_win=1, fighter_ids=ids))
    step(ctx, 200)  # past the round's opening
    fight.rounds.match.fighters[1 - winner].hurt(5000)
    for _ in range(600):
        step(ctx)
        if fight.rounds.phase == Phase.MATCH_OVER:
            break
    assert fight.rounds.winner == winner
    return fight


def test_the_winner_says_its_line_to_that_opponent(ctx):
    fight = _win(ctx, ("jotaro_p3", "dio_p3"))
    assert fight.winner_line() == exchange_for("jotaro_p3", "dio_p3").victory_line("jotaro_p3")
    step(ctx, WINNER_POSE_AFTER_F + 2)
    fight.draw(pygame.Surface((480, 270)))


def test_the_winner_strikes_its_pose_once_the_last_blow_has_landed(ctx):
    fight = _win(ctx, ("jotaro_p3", "dio_p3"))
    views = fight.view.fighter_views
    assert not views[0].celebrating
    step(ctx, WINNER_POSE_AFTER_F + 2)
    assert views[0].celebrating and not views[1].celebrating
    assert views[0].posing(fight.rounds.match.fighters[0])


def test_a_winner_with_no_line_for_that_opponent_stays_silent(ctx):
    fight = _win(ctx, ("jotaro_p3", "avdol"), winner=1)  # the games give Avdol none here
    assert fight.winner_line() == ""
    step(ctx, WINNER_POSE_AFTER_F + 2)
    fight.draw(pygame.Surface((480, 270)))


def test_nothing_is_said_while_the_fight_is_on(ctx):
    fight = start(ctx, FightScene(ctx, rounds_to_win=1, fighter_ids=("jotaro_p3", "dio_p3")))
    step(ctx, 30)
    assert fight.winner_line() == ""
    assert not any(view.celebrating for view in fight.view.fighter_views)
