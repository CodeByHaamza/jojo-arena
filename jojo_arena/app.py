"""Entry point: parse command-line options and run the game."""

from __future__ import annotations

import argparse
from pathlib import Path

import pygame

from jojo_arena.context import GameContext
from jojo_arena.controls import controls_path, load_controls
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import InputManager
from jojo_arena.engine.loop import FixedStep
from jojo_arena.engine.scene import Scene, SceneManager

WINDOW_TITLE = "JoJo Arena"
INTERNAL_SIZE = (480, 270)
LOGIC_HZ = 60


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
        "--scene", default="fight", choices=["fight", "test-pattern"], help="first scene"
    )
    parser.add_argument(
        "--demo", action="store_true", help="both fighters are played by the computer"
    )
    return parser.parse_args(argv)


class Game:
    def __init__(self, fullscreen: bool) -> None:
        pygame.init()
        display = Display(WINDOW_TITLE, INTERNAL_SIZE, fullscreen=fullscreen)
        inputs = InputManager()
        inputs.start()
        path = controls_path()
        config, warnings = load_controls(path)
        print(f"Controls file: {path}")
        for warning in warnings:
            print(f"  ! {warning}")
        self.ctx = GameContext(display, inputs, SceneManager(), config, path)
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
    if args.scene == "test-pattern":
        from jojo_arena.ui.test_pattern import TestPatternScene

        return TestPatternScene()
    from jojo_arena.ui.fight_scene import FightScene

    return FightScene(ctx, bots=(args.demo, args.demo))


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    game = Game(fullscreen=args.fullscreen)
    try:
        game.run(build_first_scene(game.ctx, args), frame_limit=args.frames)
        if args.screenshot:
            game.save_screenshot(args.screenshot)
    finally:
        pygame.quit()
