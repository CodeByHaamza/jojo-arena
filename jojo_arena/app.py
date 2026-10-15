"""Entry point: parse command-line options and run the game."""

from __future__ import annotations

import argparse
from pathlib import Path

import pygame

from jojo_arena.engine.display import Display
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
        "--scene", default="test-pattern", choices=["test-pattern"], help="first scene"
    )
    return parser.parse_args(argv)


class Game:
    def __init__(self, fullscreen: bool) -> None:
        pygame.init()
        self.display = Display(WINDOW_TITLE, INTERNAL_SIZE, fullscreen=fullscreen)
        self.scenes = SceneManager()
        self.clock = pygame.time.Clock()
        self.fixed_step = FixedStep(LOGIC_HZ)

    def handle_global_event(self, event: pygame.event.Event) -> bool:
        """Window-level shortcuts. Return True when the event is consumed."""
        if event.type == pygame.QUIT:
            self.scenes.quit()
            return True
        if event.type == pygame.KEYDOWN:
            alt_enter = event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT
            if event.key == pygame.K_F11 or alt_enter:
                self.display.toggle_fullscreen()
                return True
        return False

    def run(self, first_scene: Scene, frame_limit: int = 0) -> None:
        self.scenes.switch(first_scene)
        self.scenes.apply_pending()
        frame = 0
        while not self.scenes.quit_requested:
            elapsed_ms = self.clock.tick(LOGIC_HZ)
            scene = self.scenes.current
            for event in pygame.event.get():
                if not self.handle_global_event(event):
                    scene.handle_event(event)
            steps = 1 if frame_limit else self.fixed_step.advance(elapsed_ms)
            for _ in range(steps):
                self.scenes.current.update()
                self.scenes.apply_pending()
            self.scenes.current.draw(self.display.surface)
            self.display.present()
            frame += 1
            if frame_limit and frame >= frame_limit:
                break

    def save_screenshot(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(self.display.surface, str(path))


def build_first_scene(name: str) -> Scene:
    from jojo_arena.ui.test_pattern import TestPatternScene

    return TestPatternScene()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    game = Game(fullscreen=args.fullscreen)
    try:
        game.run(build_first_scene(args.scene), frame_limit=args.frames)
        if args.screenshot:
            game.save_screenshot(args.screenshot)
    finally:
        pygame.quit()
