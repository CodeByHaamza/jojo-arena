"""Record a short animated PNG of the game playing itself, for the README.

    python tools/record_clip.py docs/media/fight.png --p1 wamuu --p2 joseph_p2

Both sides are the computer, their gauges are kept full so the big moves come out, and
one frame out of `--every` is kept. The result is an animated PNG written by
`tools/make_apng.py` - no library, like everything else here.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402

from jojo_arena.combat.dummy import Dummy  # noqa: E402
from jojo_arena.combat.rounds import Phase  # noqa: E402
from jojo_arena.context import GameContext  # noqa: E402
from jojo_arena.engine.display import Display  # noqa: E402
from jojo_arena.engine.input import InputManager  # noqa: E402
from jojo_arena.engine.scene import SceneManager  # noqa: E402
from jojo_arena.ui.fight_scene import FightScene  # noqa: E402
from tools.make_apng import write_apng  # noqa: E402


def showcase(
    out: Path,
    fighter: str,
    action: str,
    stage: str,
    frames: int,
    every: int,
    scale: int,
    gap: float,
    skip: int,
) -> Path:
    """One move, over and over, on a mannequin: for a clip of a signature technique.

    `fighter` performs `action` (a dummy action key, `stance/slot`, `hha` or `gha`) with
    the training room's own dummy, which knows how to take out its Stand or switch
    stance first.
    """
    from jojo_arena import controls
    from jojo_arena.ui.training_scene import TrainingScene

    pygame.init()
    config, _ = controls.parse_controls(None)
    ctx = GameContext(
        Display("clip", (480, 270)), InputManager(), SceneManager(), config, Path(os.devnull)
    )
    scene = TrainingScene(ctx, fighter_ids=("mannequin_red", fighter), stage_id=stage)
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()
    scene.training.infinite_hh = True  # the ultimates come out every time
    scene.training.infinite_life = True
    scene.training.apply_options()
    scene.dummy.plan.mode = Dummy.ACTION
    scene.dummy.plan.delay_f = 40
    scene.dummy.plan.approach = False
    scene.dummy.select(action)
    scene.inputs_shown = False  # a clip of a move, not of a keyboard
    scene.frames_shown = False
    scene.meter_shown = False
    scene.draw_overlay = lambda surface: None  # nor of the training room's own writing

    def tick() -> None:
        ctx.inputs.begin_step()
        scene.update()
        ctx.scenes.apply_pending()
        a, b = scene.rounds.match.fighters
        a.pos.x = b.pos.x - gap  # the mannequin stays where the move can reach it
        a.pos.y = b.pos.y
        scene.draw(ctx.display.surface)

    for _ in range(skip):
        tick()
    shots: list[pygame.Surface] = []
    for step in range(frames):
        tick()
        if step % every:
            continue
        picture = ctx.display.surface
        if scale != 1:
            picture = pygame.transform.scale_by(picture, scale)
        shots.append(picture.copy())
    pygame.quit()
    return write_apng(out, shots, delay_ms=every * 1000 // 60)


def record(
    out: Path,
    p1: str,
    p2: str,
    stage: str,
    frames: int,
    every: int,
    scale: int,
    meter: bool,
    skip: int,
) -> Path:
    from jojo_arena import controls

    pygame.init()
    config, _ = controls.parse_controls(None)
    ctx = GameContext(
        Display("clip", (480, 270)),
        InputManager(),
        SceneManager(),
        config,
        Path(os.devnull),
    )
    scene = FightScene(
        ctx, rounds_to_win=1, fighter_ids=(p1, p2), stage_id=stage, bots=(True, True)
    )
    ctx.scenes.switch(scene)
    ctx.scenes.apply_pending()

    def tick() -> None:
        ctx.inputs.begin_step()
        scene.update()
        ctx.scenes.apply_pending()
        scene.draw(ctx.display.surface)
        if meter and scene.rounds.phase == Phase.FIGHT:
            for fighter in scene.rounds.match.fighters:
                fighter.hh = scene.rules.hh_max  # so the ultimates come out in three seconds

    # Past the round intro and the first steps: a clip of two fighters standing still
    # says nothing about the game.
    while not (scene.rounds.phase == Phase.FIGHT and scene.rounds.phase_f > skip):
        tick()
    shots: list[pygame.Surface] = []
    for step in range(frames):
        tick()
        if step % every:
            continue
        picture = ctx.display.surface
        if scale != 1:
            picture = pygame.transform.scale_by(picture, scale)  # nearest: it stays crisp
        shots.append(picture.copy())
    pygame.quit()
    return write_apng(out, shots, delay_ms=every * 1000 // 60)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    parser.add_argument("--p1", default="wamuu")
    parser.add_argument("--p2", default="joseph_p2")
    parser.add_argument("--stage", default="swiss_castle")
    parser.add_argument("--frames", type=int, default=200, help="game frames to run through")
    parser.add_argument("--every", type=int, default=4, help="keep one frame out of this many")
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--skip", type=int, default=90, help="frames of fight to let pass first")
    parser.add_argument("--no-meter", action="store_true", help="do not keep their gauges full")
    parser.add_argument(
        "--action",
        help="show one move instead of a fight: a dummy action key (base/heavy, gha...)",
    )
    parser.add_argument("--gap", type=float, default=34.0, help="distance for --action")
    args = parser.parse_args(argv)
    if args.action:
        path = showcase(
            args.out,
            args.p2,
            args.action,
            args.stage,
            args.frames,
            args.every,
            args.scale,
            args.gap,
            args.skip,
        )
        print(f"{path} ({path.stat().st_size // 1024} KB)")
        return
    path = record(
        args.out,
        args.p1,
        args.p2,
        args.stage,
        args.frames,
        args.every,
        args.scale,
        not args.no_meter,
        args.skip,
    )
    print(f"{path} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
