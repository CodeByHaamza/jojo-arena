"""What two fighters say to each other: the data, the VS screen that plays it line by line
in the poses picked, the entrance they make on the arena before the first round, and the
winner's moment (its pose, its Stand, its line) before the summary."""

import pygame
import pytest

from jojo_arena import controls
from jojo_arena.characters import load_roster
from jojo_arena.characters.lines import LINES_FILE, exchange_for, load_exchanges, load_solo
from jojo_arena.combat.fighter import State
from jojo_arena.combat.rounds import Phase
from jojo_arena.context import GameContext
from jojo_arena.engine import font, i18n
from jojo_arena.engine.data import load_toml
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.ui.fight_scene import (
    RESULT_MENU_AFTER_F,
    WINNER_LINE_W,
    WINNER_POSE_AFTER_F,
    FightScene,
)
from jojo_arena.ui.loadout import Loadout
from jojo_arena.ui.setup_scene import LINE_F, LINE_PAUSE_F, LINE_W, SetupScene
from jojo_arena.ui.staging import GAP_F, POSE_F, WALK_F, Entrance


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
    data = load_toml(LINES_FILE)
    for entry in data["exchanges"]:
        for line in [*entry["intro"], *entry.get("victory", {}).values()]:
            assert line["text"] and line["text_en"], entry["fighters"]
            strings += [line["text"], line["text_en"]]
    roster = {fighter.id for fighter in load_roster()}
    for fighter, entry in data.get("solo", {}).items():
        assert fighter in roster and entry.get("source"), fighter
        for line in (entry.get("intro"), entry.get("victory")):
            if line is not None:
                assert line["text"] and line["text_en"], fighter
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
    for own in load_solo().values():
        assert len(font.wrap(own.intro, LINE_W)) <= 2, own.intro
        assert len(font.wrap(own.victory, WINNER_LINE_W)) <= 2, own.victory


def test_a_pair_with_nothing_of_its_own_says_each_fighters_own_lines(tmp_path):
    lines = tmp_path / "lines.toml"
    lines.write_text(
        """
[[exchanges]]
fighters = ["a", "b"]
source = "test"

[[exchanges.intro]]
by = "a"
text = "A to B"
text_en = "A to B"

[exchanges.victory.a]
text = "A beat B"
text_en = "A beat B"

[solo.a]
source = "test"
intro = { text = "A, alone", text_en = "A, alone" }
victory = { text = "A won", text_en = "A won" }

[solo.b]
source = "test"
victory = { text = "B won", text_en = "B won" }
""",
        encoding="utf-8",
    )
    pair = exchange_for("b", "a", lines)
    assert [line for _, line in pair.intro] == ["A to B"]  # the pair's own lines first
    assert pair.victory_line("a") == "A beat B" and pair.victory_line("b") == "B won"
    alone = exchange_for("a", "c", lines)  # no pair: each says its own
    assert alone.intro == (("a", "A, alone"),) and alone.victory_line("a") == "A won"
    mirror = exchange_for("a", "a", lines)
    assert len(mirror.intro) == 1  # said once, not twice
    assert exchange_for("c", "d", lines) is None


def test_a_pair_says_the_same_whichever_side_each_is_on():
    one, other = exchange_for("jotaro_p3", "dio_p3"), exchange_for("dio_p3", "jotaro_p3")
    assert one is not None and one == other
    assert [who for who, _ in one.intro] == ["jotaro_p3", "dio_p3"]
    assert one.victory_line("jotaro_p3") and one.victory_line("dio_p3")
    assert one.victory_line("kakyoin") == ""


def test_a_pair_the_games_gave_nothing_to_says_nothing():
    # Bruford and Tarkus are in no game: no pair lines, no lines of their own.
    assert exchange_for("bruford", "tarkus") is None
    assert exchange_for("tarkus", "tarkus") is None  # a mirror match


def test_with_no_pair_lines_each_says_its_own():
    alone = exchange_for("kakyoin", "bruford")
    assert [who for who, _ in alone.intro] == ["kakyoin"]
    assert alone.victory_line("kakyoin") and alone.victory_line("bruford") == ""
    mirror = exchange_for("jotaro_p3", "jotaro_p3")
    assert len(mirror.intro) == 1  # said once


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
    setup = start(ctx, SetupScene(ctx, ("bruford", "tarkus")))
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


def test_a_winner_with_no_line_for_that_opponent_says_its_own(ctx):
    fight = _win(ctx, ("jotaro_p3", "avdol"), winner=1)  # the games give Avdol none here
    assert fight.winner_line() == "Je n'avais même pas besoin de le prédire."
    step(ctx, WINNER_POSE_AFTER_F + 2)
    fight.draw(pygame.Surface((480, 270)))


def test_a_winner_with_no_line_at_all_stays_silent(ctx):
    fight = _win(ctx, ("bruford", "tarkus"), winner=0)
    assert fight.winner_line() == ""


def test_nothing_is_said_while_the_fight_is_on(ctx):
    fight = start(ctx, FightScene(ctx, rounds_to_win=1, fighter_ids=("jotaro_p3", "dio_p3")))
    step(ctx, 30)
    assert fight.winner_line() == ""
    assert not any(view.celebrating for view in fight.view.fighter_views)


# The entrance, on the arena, before the first round -----------------------------------------


def tap(ctx, key: str):
    code = KEY_SCANCODES[key]
    ctx.inputs.handle_event(pygame.event.Event(pygame.KEYDOWN, scancode=code, key=0, mod=0))
    ctx.inputs.handle_event(pygame.event.Event(pygame.KEYUP, scancode=code, key=0, mod=0))


def _enter(ctx, ids=("jotaro_p3", "dio_p3")):
    fight = start(ctx, FightScene(ctx, rounds_to_win=1, fighter_ids=ids, entrance=True))
    step(ctx)
    assert fight.entrance is not None
    return fight


def test_a_fight_goes_straight_to_the_round_unless_asked_for_an_entrance(ctx):
    fight = start(ctx, FightScene(ctx, rounds_to_win=1, fighter_ids=("jotaro_p3", "dio_p3")))
    step(ctx, 5)
    assert fight.entrance is None and fight.rounds.phase_f == 5


def test_they_walk_in_then_each_strikes_its_pose_and_says_its_line(ctx):
    fight = _enter(ctx)
    entrance, views = fight.entrance, fight.view.fighter_views
    jotaro, dio = fight.rounds.match.fighters
    marks = [mark.copy() for mark in entrance.marks]
    assert jotaro.pos.distance_to(marks[0]) > 30 and jotaro.state == State.WALK  # walking in
    step(ctx, WALK_F + 5)
    assert jotaro.pos.distance_to(marks[0]) < 0.01 and dio.pos.distance_to(marks[1]) < 0.01
    who, line, _ = entrance.beat()
    assert who == 0 and line == fight.exchange.intro[0][1]  # Jotaro first
    assert views[0].celebrating and not views[1].celebrating
    assert views[0].posing(jotaro) and views[0].pose_anim(jotaro).startswith("pose_")
    step(ctx, POSE_F + GAP_F)
    who, line, _ = entrance.beat()
    assert who == 1 and line == fight.exchange.intro[1][1]  # DIO answers
    assert views[1].celebrating and not views[0].celebrating
    fight.draw(pygame.Surface((480, 270)))


def test_the_stand_comes_out_to_pose_even_though_it_was_called_back(ctx):
    fight = _enter(ctx)
    jotaro = fight.rounds.match.fighters[0]
    view = fight.view.fighter_views[0]
    step(ctx, WALK_F + 30)
    assert not jotaro.aura_active  # the simulation still has it called back...
    assert view.stand_presence(jotaro) == 1.0  # ...but it is there, on screen, posing
    assert view.sprites.poses[view.pose_anim(jotaro).removeprefix("pose_")].stand


def test_nothing_of_the_entrance_reaches_the_fight_or_its_replay(ctx):
    fight = _enter(ctx)
    played_on = fight.rounds
    assert fight.rounds.phase_f == 0  # the rounds wait while they make their entrance
    step(ctx, fight.entrance.length + 2)
    assert fight.entrance is None
    assert fight.rounds is not played_on  # that match was a stage: a fresh one starts
    plain = start(ctx, FightScene(ctx, rounds_to_win=1, fighter_ids=("jotaro_p3", "dio_p3")))
    step(ctx, fight.rounds.phase_f)
    assert not any(view.celebrating for view in fight.view.fighter_views)
    for staged, fresh in zip(fight.rounds.match.fighters, plain.rounds.match.fighters, strict=True):
        assert staged.pos == fresh.pos and staged.state == fresh.state
        assert staged.facing == fresh.facing and staged.state_f == fresh.state_f
    assert len(fight.replay.frames) == len(plain.replay.frames)


def test_confirm_skips_the_entrance(ctx):
    fight = _enter(ctx)
    step(ctx, 10)
    tap(ctx, "Return")
    step(ctx, 2)
    assert fight.entrance is None and fight.rounds.phase_f <= 2


def test_a_pair_with_nothing_to_say_poses_together_and_briefly(ctx):
    silent = _enter(ctx, ("bruford", "tarkus"))
    spoken = Entrance([], [], ("jotaro_p3", "dio_p3"), exchange_for("jotaro_p3", "dio_p3"))
    assert silent.entrance.length < spoken.length
    step(ctx, WALK_F + 10)
    who, line, _ = silent.entrance.beat()
    assert who is None and line == ""
    assert all(view.celebrating for view in silent.view.fighter_views)
    silent.draw(pygame.Surface((480, 270)))


def test_a_replay_and_a_demo_have_no_entrance(ctx):
    demo = FightScene(ctx, fighter_ids=("jotaro_p3", "dio_p3"), bots=(True, True), entrance=True)
    start(ctx, demo)
    step(ctx, 3)
    assert demo.entrance is None and demo.rounds.phase_f == 3


# The winner's moment, before the summary --------------------------------------------------------


def test_the_summary_waits_for_the_winner_to_have_said_its_line(ctx):
    fight = _win(ctx, ("jotaro_p3", "dio_p3"))
    line = fight.winner_line()
    assert fight.winner_moment_f() > WINNER_POSE_AFTER_F + len(line) // 2  # typed, then read
    step(ctx, fight.winner_moment_f() - fight.rounds.phase_f - 2)
    assert fight.result_menu is None
    fight.draw(pygame.Surface((480, 270)))
    step(ctx, 4)
    assert fight.result_menu is not None
    fight.draw(pygame.Surface((480, 270)))


def test_confirm_cuts_the_winners_moment_short(ctx):
    fight = _win(ctx, ("jotaro_p3", "dio_p3"))
    step(ctx, RESULT_MENU_AFTER_F + 5 - fight.rounds.phase_f)
    assert fight.result_menu is None
    tap(ctx, "Return")
    step(ctx, 2)
    assert fight.result_menu is not None
