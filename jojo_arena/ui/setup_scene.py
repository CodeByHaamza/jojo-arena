"""VS screen before a local fight: both fighters face off; rounds to win and controls."""

from __future__ import annotations

import pygame

from jojo_arena.characters import get_fighter
from jojo_arena.combat.rounds import ROUNDS_TO_WIN_CHOICES
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import shade
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.labels import menu_key
from jojo_arena.ui.menu import Menu, MenuItem
from jojo_arena.ui.portraits import FighterLook
from jojo_arena.ui.widgets import DIM, GOLD, P1_COLOR, P2_COLOR, draw_box, draw_hints

WARNING = (240, 90, 90)
DEFAULT_ROUNDS_TO_WIN = 3
DEFAULT_FIGHTERS = ("jotaro_p3", "kakyoin")
FEET_Y = 178
FEET_X = (78, 402)


class SetupScene(Scene):
    def __init__(
        self,
        ctx: GameContext,
        fighter_ids: tuple[str, str] = DEFAULT_FIGHTERS,
        rounds_to_win: int = DEFAULT_ROUNDS_TO_WIN,
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.fighter_ids = fighter_ids
        self.defs = [get_fighter(i) for i in fighter_ids]
        self.looks = [FighterLook(f) for f in self.defs]
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
        self.menu.select("fight")
        self.tick = 0
        self.hints = [
            (menu_key("confirm", ctx.inputs), text.HINT_CONFIRM),
            (menu_key("back", ctx.inputs), text.HINT_BACK),
        ]

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

            self.ctx.scenes.switch(
                FightScene(self.ctx, rounds_to_win=self.rounds_to_win, fighter_ids=self.fighter_ids)
            )
        elif (kind == "confirm" and key == "back") or kind == "back":
            # Back to the character select, player 2 choosing again.
            from jojo_arena.ui.select_scene import CharacterSelectScene

            p1, p2 = self.fighter_ids
            self.ctx.scenes.switch(CharacterSelectScene(self.ctx, "versus", picks=(p1,), cursor=p2))

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        center = width // 2
        font.draw(surface, text.SETUP_TITLE, (center, 8), GOLD, scale=2, align="center")
        for side, (look, fdef) in enumerate(zip(self.looks, self.defs, strict=True)):
            x = FEET_X[side]
            look.draw(surface, (x, FEET_Y), self.tick, scale=2, flip=side == 1)
            color = P1_COLOR if side == 0 else P2_COLOR
            font.draw(surface, f"J{side + 1}", (x, 40), color, scale=2, align="center")
            font.draw(surface, fdef.name, (x, FEET_Y + 8), shade(fdef.color, 60), align="center")
            if fdef.stand_name:
                font.draw(surface, fdef.stand_name, (x, FEET_Y + 19), fdef.aura, align="center")
        font.draw(surface, text.VS, (center, 50), GOLD, scale=4, align="center")
        box = pygame.Rect(0, 0, 236, 70)
        box.midtop = (center, 104)
        draw_box(surface, box)
        self.menu.draw(surface, center, box.y + 9, spacing=15)
        preset = self.ctx.controls.active_preset
        if preset.pads_needed() > len(self.ctx.inputs.pads):
            font.draw(surface, text.PADS_MISSING, (center, 222), WARNING, align="center")
        font.draw(surface, text.CONTROLS_FILE_HINT, (center, 236), DIM, align="center")
        draw_hints(surface, self.hints, (center, height - 14))
