"""Entry point: parse command-line options and run the game."""

from __future__ import annotations

import argparse
from pathlib import Path

import pygame

from jojo_arena.context import GameContext
from jojo_arena.controls import controls_path, load_controls
from jojo_arena.engine import i18n
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import InputManager
from jojo_arena.engine.loop import FixedStep
from jojo_arena.engine.scene import Scene, SceneManager
from jojo_arena.settings import load_settings, settings_path

WINDOW_TITLE = "JoJo Arena"
INTERNAL_SIZE = (480, 270)
LOGIC_HZ = 60
SCENES = [
    "title",
    "menu",
    "select",
    "training",
    "setup",
    "fight",
    "options",
    "glossary",
    "test-pattern",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="jojo_arena", description=WINDOW_TITLE)
    parser.add_argument("--fullscreen", action="store_true", help="start in fullscreen")
    parser.add_argument(
        "--frames",
        type=int,
        default=0,
        help="run exactly this many frames, one logic step each, then quit (smoke tests)",
    )
    parser.add_argument(
        "--screenshot", type=Path, help="save the internal 480x270 image here when quitting"
    )
    parser.add_argument(
        "--scene",
        default="title",
        choices=SCENES,
        help="first screen (default: title)",
    )
    parser.add_argument(
        "--demo", action="store_true", help="jump into a fight played by the computer on both sides"
    )
    parser.add_argument(
        "--rounds", type=int, default=3, choices=[1, 3, 5], help="rounds to win (--scene fight)"
    )
    parser.add_argument(
        "--p1", default="jotaro_p3", help="player 1 fighter id (--scene fight/training/setup)"
    )
    parser.add_argument(
        "--p2", default="kakyoin", help="player 2 fighter id (--scene fight/training/setup)"
    )
    parser.add_argument(
        "--replay", type=Path, help="watch a recorded fight (a .json file from the replays folder)"
    )
    parser.add_argument(
        "--lang", choices=i18n.LANGUAGES, help="language of the texts (default: the saved one)"
    )
    parser.add_argument(
        "--mode",
        default="versus",
        choices=["versus", "training"],
        help="character select flavour (--scene select)",
    )
    return parser.parse_args(argv)


class Game:
    def __init__(self, fullscreen: bool, language: str | None = None) -> None:
        pygame.init()
        display = Display(WINDOW_TITLE, INTERNAL_SIZE, fullscreen=fullscreen)
        inputs = InputManager()
        inputs.start()
        path = controls_path()
        config, warnings = load_controls(path)
        print(f"Controls file: {path}")
        for warning in warnings:
            print(f"  ! {warning}")
        settings = load_settings(settings_path(path))
        if language:
            settings.language = language
        i18n.set_language(settings.language)
        self.ctx = GameContext(display, inputs, SceneManager(), config, path, settings)
        self.clock = pygame.time.Clock()
        self.fixed_step = FixedStep(LOGIC_HZ)

    def handle_global_event(self, event: pygame.event.Event) -> bool:
        """Window-level shortcuts. Return True when the event is consumed."""
        if event.type == pygame.QUIT:
            self.ctx.scenes.quit()
            return True
        if event.type == pygame.KEYDOWN:
            alt_enter = event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT
            if event.key == pygame.K_F11 or alt_enter:
                self.ctx.display.toggle_fullscreen()
                return True
        return False

    def run(self, first_scene: Scene, frame_limit: int = 0) -> None:
        scenes = self.ctx.scenes
        scenes.switch(first_scene)
        scenes.apply_pending()
        frame = 0
        while not scenes.quit_requested:
            elapsed_ms = self.clock.tick(LOGIC_HZ)
            for event in pygame.event.get():
                if not self.handle_global_event(event):
                    self.ctx.inputs.handle_event(event)
                    scenes.current.handle_event(event)
            steps = 1 if frame_limit else self.fixed_step.advance(elapsed_ms)
            for _ in range(steps):
                self.ctx.inputs.begin_step()
                scenes.current.update()
                scenes.apply_pending()
            scenes.current.draw(self.ctx.display.surface)
            self.ctx.display.present()
            frame += 1
            if frame_limit and frame >= frame_limit:
                break

    def save_screenshot(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(self.ctx.display.surface, str(path))


def build_first_scene(ctx: GameContext, args: argparse.Namespace) -> Scene:
    if args.replay:
        return replay_scene(ctx, args.replay)
    if args.demo or args.scene == "fight":
        from jojo_arena.ui.fight_scene import FightScene

        return FightScene(
            ctx,
            rounds_to_win=args.rounds,
            fighter_ids=(args.p1, args.p2),
            bots=(args.demo, args.demo),
        )
    if args.scene == "training":
        from jojo_arena.ui.training_scene import TrainingScene

        return TrainingScene(ctx, fighter_ids=(args.p1, args.p2))
    if args.scene == "setup":
        from jojo_arena.ui.setup_scene import SetupScene

        return SetupScene(ctx, fighter_ids=(args.p1, args.p2), rounds_to_win=args.rounds)
    if args.scene == "menu":
        from jojo_arena.ui.main_menu import MainMenuScene

        return MainMenuScene(ctx)
    if args.scene == "select":
        from jojo_arena.ui.select_scene import CharacterSelectScene

        return CharacterSelectScene(ctx, mode=args.mode)
    if args.scene == "options":
        from jojo_arena.ui.options_scene import OptionsScene

        return OptionsScene(ctx)
    if args.scene == "glossary":
        from jojo_arena.ui.glossary_scene import GlossaryScene

        return GlossaryScene(ctx)
    if args.scene == "test-pattern":
        from jojo_arena.ui.test_pattern import TestPatternScene

        return TestPatternScene()
    from jojo_arena.ui.title_scene import TitleScene

    return TitleScene(ctx)


def replay_scene(ctx: GameContext, path: Path) -> Scene:
    """The fight a replay was recorded in, fed with its recorded inputs."""
    from jojo_arena.combat.replay import load_replay

    replay = load_replay(path)
    meta = replay.meta
    fighters = tuple(meta["fighters"])
    if meta.get("mode") == "training":
        from jojo_arena.ui.training_scene import TrainingScene

        scene = TrainingScene(ctx, fighter_ids=fighters, stage_id=meta["stage"])
    else:
        from jojo_arena.ui.fight_scene import FightScene

        scene = FightScene(
            ctx,
            rounds_to_win=meta.get("rounds_to_win", 3),
            fighter_ids=fighters,
            stage_id=meta["stage"],
        )
    scene.playback = replay
    return scene


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    game = Game(fullscreen=args.fullscreen, language=args.lang)
    try:
        game.run(build_first_scene(game.ctx, args), frame_limit=args.frames)
        if args.screenshot:
            game.save_screenshot(args.screenshot)
    finally:
        pygame.quit()
