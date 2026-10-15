"""Title screen: the logo over the roster lined up, "press start"."""

from __future__ import annotations

import pygame

from jojo_arena import __version__
from jojo_arena.characters import load_roster
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.scene import Scene
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.portraits import FighterLook
from jojo_arena.ui.widgets import DIM, GOLD, WHITE

LINEUP_Y = 236
LINEUP_SPACING = 92


class TitleScene(Scene):
    def __init__(self, ctx: GameContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.backdrop = MenuBackdrop()
        self.looks = [FighterLook(f) for f in load_roster() if f.selectable]
        self.tick = 0

    def update(self) -> None:
        self.tick += 1
        frame = self.ctx.read_menu()
        if frame.was_pressed("confirm"):
            from jojo_arena.ui.main_menu import MainMenuScene

            self.ctx.scenes.switch(MainMenuScene(self.ctx))
        elif frame.was_pressed("back"):
            self.ctx.scenes.quit()

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width = surface.get_width()
        count = len(self.looks)
        first = width // 2 - (count - 1) * LINEUP_SPACING // 2
        for i, look in enumerate(self.looks):
            # Each fighter turns towards the middle of the screen.
            x = first + i * LINEUP_SPACING
            look.draw(surface, (x, LINEUP_Y), self.tick + i * 7, flip=x > width // 2)
        font.draw(surface, text.TITLE, (width // 2, 30), GOLD, scale=5, align="center")
        font.draw(surface, text.DISCLAIMER, (width // 2, 82), DIM, align="center")
        if (self.tick // 30) % 2 == 0:
            font.draw(surface, text.PRESS_START, (width // 2, 104), WHITE, align="center")
        font.draw(surface, f"V{__version__}", (width - 6, 258), DIM, align="right")
