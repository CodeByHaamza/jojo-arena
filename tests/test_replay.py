"""Replays: recorded inputs play the very same fight again."""

import json
import random

import pygame
import pytest
from helpers import OPEN_BOUNDS

from jojo_arena import controls
from jojo_arena.characters import get_fighter
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.replay import Replay, frame_from_data, frame_to_data, load_replay
from jojo_arena.combat.rounds import Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.context import GameContext
from jojo_arena.engine.actions import NEUTRAL, InputFrame
from jojo_arena.engine.display import Display
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.input import KEY_SCANCODES, InputManager
from jojo_arena.engine.scene import SceneManager

ACTIONS = ("light", "heavy", "special", "stand", "dash", "guard", "heart_heat", "pose")
RULES = load_rules()


def random_frame(rng):
    pressed = {a: 1 for a in ACTIONS if rng.random() < 0.07}
    held = {a for a in ACTIONS if rng.random() < 0.08} | set(pressed)
    move = rng.choice(((0, 0), (1, 0), (-1, 0), (0, 1), (0.7071, -0.7071)))
    cursor = (rng.uniform(20, 460), rng.uniform(40, 250)) if rng.random() < 0.05 else None
    return InputFrame(move, frozenset(held), pressed, cursor)


def new_rounds():
    kits = (get_fighter("dio_p3").kit, get_fighter("kakyoin").kit)

    def arena():
        return Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(250, 100)))

    return Rounds(kits, RULES, arena, 2)


def snapshot(rounds):
    fighters = rounds.match.fighters
    return (
        rounds.round_number,
        tuple(rounds.wins),
        tuple((f.hp, round(f.pos.x, 6), round(f.pos.y, 6), f.state, f.stance) for f in fighters),
    )


def test_frames_survive_the_round_trip():
    rng = random.Random(3)
    for _ in range(200):
        frame = random_frame(rng)
        assert frame_from_data(json.loads(json.dumps(frame_to_data(frame)))) == frame
    assert frame_to_data(NEUTRAL) == 0


def test_a_replayed_fight_ends_exactly_the_same():
    rng = random.Random(11)
    rounds = new_rounds()
    replay = Replay({"fighters": ["dio_p3", "kakyoin"]})
    for step in range(1500):
        if step % 200 == 0:
            for f in rounds.match.fighters:
                f.hh = RULES.hh_max  # supers and cutscenes come into it too
        frames = (random_frame(rng), random_frame(rng))
        replay.record(frames)
        rounds.step(frames)
    played = snapshot(rounds)
    copy = Replay.from_data(json.loads(json.dumps(replay.to_data())))
    again = new_rounds()
    for step, frames in enumerate(copy.frames):
        if step % 200 == 0:
            for f in again.match.fighters:
                f.hh = RULES.hh_max
        again.step(frames)
    assert snapshot(again) == played


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


def steps(ctx, n=1):
    for _ in range(n):
        ctx.inputs.begin_step()
        ctx.scenes.current.update()
        ctx.scenes.apply_pending()
        ctx.scenes.current.draw(ctx.display.surface)


def test_leaving_a_training_session_saves_its_replay_and_it_plays_back(ctx):
    from jojo_arena.app import replay_scene
    from jojo_arena.ui.training_scene import TrainingScene

    scene = TrainingScene(ctx, fighter_ids=("jotaro_p3", "dio_p3"))
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()
    for key in ("J", "J", "K", "L"):
        tap(ctx, key)
        steps(ctx, 20)
    final = snapshot(scene.rounds)
    path = scene.save_replay()
    assert path is not None and path.exists()
    replay = load_replay(path)
    assert replay.meta["mode"] == "training" and len(replay.frames) == 80
    watch = replay_scene(ctx, path)
    ctx.scenes.switch(watch)
    ctx.scenes.apply_pending()
    steps(ctx, 80)
    assert snapshot(watch.rounds) == final
