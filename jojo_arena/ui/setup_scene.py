"""Fight settings before a local match: rounds to win and control preset."""

from __future__ import annotations

import pygame

from jojo_arena.combat.rounds import ROUNDS_TO_WIN_CHOICES
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.scene import Scene
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.menu import Menu, MenuItem

GOLD = (255, 214, 90)
DIM = (150, 144, 170)
WARNING = (240, 90, 90)
DEFAULT_ROUNDS_TO_WIN = 3


class SetupScene(Scene):
    def __init__(self, ctx: GameContext, rounds_to_win: int = DEFAULT_ROUNDS_TO_WIN) -> None:
        super().__init__()
        self.ctx = ctx
        self.backdrop = MenuBackdrop()
        self.preset_keys = list(ctx.controls.presets)
        rounds = [str(n) for n in ROUNDS_TO_WIN_CHOICES]
        labels = [ctx.controls.presets[k].label for k in self.preset_keys]
        self.menu = Menu(
            [
                MenuItem("rounds", text.ROUNDS_TO_WIN, rounds, rounds.index(str(rounds_to_win))),
                MenuItem(
                    "controls", text.CONTROLS, labels, self.preset_keys.index(ctx.controls.active)
                ),
                MenuItem("fight", text.FIGHT),
                MenuItem("back", text.BACK),
            ]
        )
        self.menu.cursor = 2  # straight on "fight"
        self.tick = 0

    @property
    def rounds_to_win(self) -> int:
        return int(self.menu.item("rounds").value)

    def update(self) -> None:
        self.tick += 1
        action = self.menu.handle(self.ctx.read_menu())
        if action is None:
            return
        kind, key = action
        if kind == "change" and key == "controls":
            self.ctx.controls.active = self.preset_keys[self.menu.item("controls").index]
            self.ctx.save_controls()
        elif kind == "confirm" and key == "fight":
            from jojo_arena.ui.fight_scene import FightScene

            self.ctx.scenes.switch(FightScene(self.ctx, rounds_to_win=self.rounds_to_win))
        elif (kind == "confirm" and key == "back") or kind == "back":
            from jojo_arena.ui.title_scene import TitleScene

            self.ctx.scenes.switch(TitleScene(self.ctx))

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        center = surface.get_width() // 2
        font.draw(surface, text.SETUP_TITLE, (center, 50), GOLD, scale=3, align="center")
        self.menu.draw(surface, center, 110, spacing=16)
        preset = self.ctx.controls.active_preset
        if preset.pads_needed() > len(self.ctx.inputs.pads):
            font.draw(surface, text.PADS_MISSING, (center, 200), WARNING, align="center")
        font.draw(surface, text.CONTROLS_FILE_HINT, (center, 240), DIM, align="center")
