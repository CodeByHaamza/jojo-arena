"""The computer opponent and the modes it opens: versus the computer, Arcade."""

import pygame
import pytest
from helpers import make_duel

from jojo_arena import controls
from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.combat.ai import LEVELS, CpuPlayer, move_reach
from jojo_arena.combat.bot import SimpleBot
from jojo_arena.combat.fighter import State
from jojo_arena.combat.rounds import Phase, Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.context import GameContext
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager
from jojo_arena.stages import load_stage, stage_for_part
from jojo_arena.ui.arcade_scene import (
    BOSS,
    LADDER_LENGTH,
    ArcadeClearScene,
    ArcadeFight,
    ArcadeScene,
    build_ladder,
    ladder_levels,
)
from jojo_arena.ui.fight_scene import FightScene
from jojo_arena.ui.main_menu import MainMenuScene
from jojo_arena.ui.select_scene import CharacterSelectScene
from jojo_arena.ui.setup_scene import SetupScene


def test_harder_levels_see_faster_and_defend_more():
    reactions = [level.reaction_f for level in LEVELS]
    defenses = [level.defend for level in LEVELS]
    assert reactions == sorted(reactions, reverse=True)
    assert defenses == sorted(defenses)


def test_the_computer_knows_how_far_its_moves_reach():
    jotaro = get_fighter("jotaro_p3").kit
    assert move_reach(jotaro.move("stand", "special_alt")) > 60  # Star Finger
    assert move_reach(jotaro.move("base", "light")) < 40
    assert move_reach(jotaro.move("stand", "special")) == 0  # time stop: not a blow


def test_the_computer_guards_or_dodges_what_it_sees_coming():
    match = make_duel("jotaro_p3", "jonathan", p2=(170, 100))
    jotaro, jonathan = match.fighters
    cpu = CpuPlayer(3, seed=4)
    jotaro.start_attack(jotaro.kit.move("base", "heavy"), jonathan.pos)  # a headbutt starts
    answers = [cpu.think(jonathan, jotaro) for _ in range(LEVELS[3].reaction_f + 4)]
    assert any("guard" in a.held or a.was_pressed("dash") for a in answers)
    calm = CpuPlayer(3, seed=4)  # nothing coming: no reason to guard
    jotaro.set_state(State.IDLE)
    answers = [calm.think(jonathan, jotaro) for _ in range(LEVELS[3].reaction_f + 4)]
    assert not any("guard" in a.held for a in answers)


def test_the_top_level_beats_the_simple_bot():
    kit = get_fighter("jotaro_p3").kit
    rounds = Rounds((kit, kit), load_rules(), load_stage("cairo_night").build_arena, 1)
    players = (CpuPlayer(3, seed=2), SimpleBot(7))
    for _ in range(60 * 120):
        match = rounds.match
        frames = tuple(players[i].think(f, match.opponent(f)) for i, f in enumerate(match.fighters))
        rounds.step(frames)
        if rounds.phase == Phase.MATCH_OVER:
            break
    assert rounds.winner == 0


def test_the_arcade_ladder_ends_with_the_boss():
    ladder = build_ladder("jonathan", seed=3)
    assert len(ladder) == LADDER_LENGTH and ladder[-1] == BOSS
    assert "jonathan" not in ladder and len(set(ladder)) == len(ladder)
    selectable = {f.id for f in load_roster() if f.selectable}
    assert set(ladder) <= selectable
    assert build_ladder(BOSS, seed=3)[-1] != BOSS  # DIO does not fight himself
    assert ladder_levels(1, 6) == [0, 0, 1, 1, 2, 2]
    assert ladder_levels(3, 6) == [2, 2, 3, 3, 3, 3]


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


def start(ctx, scene):
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()
    return scene


def test_versus_the_computer_from_the_menu(ctx):
    start(ctx, MainMenuScene(ctx, cursor="vs_cpu"))
    keys(ctx, "Return")
    select = ctx.scenes.current
    assert isinstance(select, CharacterSelectScene) and select.mode == "vs_cpu"
    assert select.side_label(1) == "IA"
    keys(ctx, "Return", "Right", "Return")
    keys(ctx, "Return")  # the arena
    setup = ctx.scenes.current
    assert isinstance(setup, SetupScene) and setup.cpu
    setup.menu.select("level")
    keys(ctx, "Right")  # a level up, remembered
    assert ctx.settings.cpu_level == 2
    setup.menu.select("fight")
    keys(ctx, "Return")
    fight = ctx.scenes.current
    assert isinstance(fight, FightScene) and fight.mode == "vs_cpu"
    assert fight.bots[0] is None and isinstance(fight.bots[1], CpuPlayer)
    assert fight.bots[1].level == LEVELS[2]


def test_arcade_from_the_menu_to_the_ending(ctx):
    start(ctx, MainMenuScene(ctx, cursor="arcade"))
    keys(ctx, "Return", "Return")  # Arcade, then pick the first fighter
    ladder = ctx.scenes.current
    assert isinstance(ladder, ArcadeScene) and ladder.index == 0
    keys(ctx, "Return")
    fight = ctx.scenes.current
    assert isinstance(fight, ArcadeFight) and fight.rounds_to_win == 2
    opponent = get_fighter(ladder.ladder[0])
    assert fight.stage_id == stage_for_part(opponent.part)
    fight.rounds.winner = 1
    assert [i.key for i in fight._result_items()] == ["retry", "menu"]
    fight.rounds.winner = 0
    assert [i.key for i in fight._result_items()] == ["next", "menu"]
    following = ladder.advanced()
    assert isinstance(following, ArcadeScene) and following.index == 1
    last = ArcadeScene(ctx, ladder.player_id, ladder.ladder, LADDER_LENGTH - 1)
    assert last.final and isinstance(last.advanced(), ArcadeClearScene)
    start(ctx, last.advanced())
    keys(ctx, "Return")
    assert isinstance(ctx.scenes.current, MainMenuScene)
