"""Title screen."""

from __future__ import annotations

import pygame

from jojo_arena import __version__
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.scene import Scene
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop

GOLD = (255, 214, 90)
DIM = (150, 144, 170)


class TitleScene(Scene):
    def __init__(self, ctx: GameContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.backdrop = MenuBackdrop()
        self.tick = 0

    def update(self) -> None:
        self.tick += 1
        frame = self.ctx.read_menu()
        if frame.was_pressed("confirm"):
            from jojo_arena.ui.setup_scene import SetupScene

            self.ctx.scenes.switch(SetupScene(self.ctx))
        elif frame.was_pressed("back"):
            self.ctx.scenes.quit()

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width = surface.get_width()
        font.draw(surface, text.TITLE, (width // 2, 70), GOLD, scale=5, align="center")
        font.draw(surface, text.DISCLAIMER, (width // 2, 124), DIM, align="center")
        if (self.tick // 30) % 2 == 0:
            font.draw(surface, text.PRESS_START, (width // 2, 180), (255, 255, 255), align="center")
        font.draw(surface, f"V{__version__}", (width - 6, 258), DIM, align="right")
