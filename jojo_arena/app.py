"""Entry point: parse command-line options and run the game."""

from __future__ import annotations

import argparse

import pygame

WINDOW_TITLE = "JoJo Arena"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="jojo_arena", description=WINDOW_TITLE)
    parser.add_argument(
        "--frames",
        type=int,
        default=0,
        help="quit after this many frames (0 = run until closed); used for smoke tests",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    window = pygame.display.set_mode((1440, 810))
    clock = pygame.time.Clock()
    frame = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        window.fill((23, 18, 31))
        pygame.display.flip()
        clock.tick(60)
        frame += 1
        if args.frames and frame >= args.frames:
            running = False
    pygame.quit()
