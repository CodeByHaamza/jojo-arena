"""Main menu: the game modes (several still to come), options and quit."""

from __future__ import annotations

import pygame

from jojo_arena.characters import load_roster
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import shade
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.labels import menu_key
from jojo_arena.ui.menu import Menu, MenuItem
from jojo_arena.ui.portraits import FighterLook
from jojo_arena.ui.widgets import (
    DIM,
    FAINT,
    GOLD,
    WHITE,
    draw_box,
    draw_hints,
    draw_toast,
    draw_wrapped,
)

# key, label, description, available yet
ENTRIES = (
    ("story", text.MENU_STORY, text.DESC_STORY, False),
    ("arcade", text.MENU_ARCADE, text.DESC_ARCADE, False),
    ("versus", text.MENU_VERSUS, text.DESC_VERSUS, True),
    ("vs_cpu", text.MENU_VS_CPU, text.DESC_VS_CPU, False),
    ("training", text.MENU_TRAINING, text.DESC_TRAINING, True),
    ("online", text.MENU_ONLINE, text.DESC_ONLINE, False),
    ("options", text.MENU_OPTIONS, text.DESC_OPTIONS, True),
    ("quit", text.QUIT, text.DESC_QUIT, True),
)
SHOWCASE_F = 300  # each fighter stays in the showcase this long
SLIDE_F = 14
TOAST_F = 90
MENU_BOX = pygame.Rect(14, 58, 196, len(ENTRIES) * 16 + 10)


class MainMenuScene(Scene):
    def __init__(self, ctx: GameContext, cursor: str = "training") -> None:
        super().__init__()
        self.ctx = ctx
        self.backdrop = MenuBackdrop()
        self.descriptions = {key: desc for key, _, desc, _ in ENTRIES}
        self.menu = Menu(
            [
                MenuItem(key, label, enabled=ready, tag="" if ready else text.SOON)
                for key, label, _, ready in ENTRIES
            ]
        )
        self.menu.select(cursor)
        self.looks = [FighterLook(f) for f in load_roster() if f.selectable]
        self.toast_f = 0
        self.tick = 0
        self.hints = [
            (menu_key("confirm", ctx.inputs), text.HINT_CONFIRM),
            (menu_key("back", ctx.inputs), text.HINT_BACK),
        ]

    def update(self) -> None:
        self.tick += 1
        self.toast_f = max(0, self.toast_f - 1)
        action = self.menu.handle(self.ctx.read_menu())
        if action is None:
            return
        kind, key = action
        if kind == "locked":
            self.toast_f = TOAST_F
        elif kind == "back":
            from jojo_arena.ui.title_scene import TitleScene

            self.ctx.scenes.switch(TitleScene(self.ctx))
        elif kind == "confirm":
            self._open(key)

    def _open(self, key: str) -> None:
        if key in ("training", "versus"):
            from jojo_arena.ui.select_scene import CharacterSelectScene

            self.ctx.scenes.switch(CharacterSelectScene(self.ctx, mode=key))
        elif key == "options":
            from jojo_arena.ui.options_scene import OptionsScene

            self.ctx.scenes.switch(OptionsScene(self.ctx))
        elif key == "quit":
            self.ctx.scenes.quit()

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        font.draw(surface, text.TITLE, (16, 12), GOLD, scale=3)
        font.draw(surface, text.DISCLAIMER, (16, 42), FAINT)

        draw_box(surface, MENU_BOX)
        self.menu.draw(surface, MENU_BOX.x + 14, MENU_BOX.y + 8, spacing=16, align="left")
        desc_box = draw_box(surface, (MENU_BOX.x, MENU_BOX.bottom + 6, MENU_BOX.width, 34))
        item = self.menu.selected
        color = WHITE if item.enabled else DIM
        draw_wrapped(
            surface,
            self.descriptions[item.key],
            (desc_box.x + 6, desc_box.y + 6),
            desc_box.width - 12,
            color,
        )

        self._draw_showcase(surface)
        draw_hints(surface, self.hints, (width // 2, height - 14))
        draw_toast(surface, text.SOON_TOAST, self.toast_f, y=130)

    def _draw_showcase(self, surface: pygame.Surface) -> None:
        """The roster takes turns on the right of the screen."""
        if not self.looks:
            return
        look = self.looks[(self.tick // SHOWCASE_F) % len(self.looks)]
        shown_f = self.tick % SHOWCASE_F
        slide = max(0, SLIDE_F - shown_f) * 5
        center = 352 + slide
        look.draw(surface, (center, 196), self.tick, scale=2, flip=True)
        fdef = look.fdef
        y = 206
        name_scale = 2 if font.text_width(fdef.name, 2) <= 230 else 1
        font.draw(surface, fdef.name, (center, y), shade(fdef.color, 60), name_scale, "center")
        y += 10 * name_scale + 2
        if fdef.stand_name:
            font.draw(surface, fdef.stand_name, (center, y), fdef.aura, align="center")
            y += 11
        if fdef.role:
            font.draw(surface, fdef.role, (center, y), DIM, align="center")
