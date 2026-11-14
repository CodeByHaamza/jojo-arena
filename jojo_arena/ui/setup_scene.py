"""VS screen before a local fight: both fighters face off; rounds to win and controls."""

from __future__ import annotations

import pygame

from jojo_arena.characters import get_fighter
from jojo_arena.combat.rounds import ROUNDS_TO_WIN_CHOICES
from jojo_arena.context import GameContext
from jojo_arena.engine import font, music
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import shade
from jojo_arena.stages import load_stage, stage_for_part
from jojo_arena.stages.base import StageOptions
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.labels import menu_key, preset_label
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
        cpu: bool = False,
        stage_id: str | None = None,
        stage_options: StageOptions | None = None,
    ) -> None:
        super().__init__()
        music.request("menu")
        self.ctx = ctx
        self.fighter_ids = fighter_ids
        self.cpu = cpu
        self.defs = [get_fighter(i) for i in fighter_ids]
        self.looks = [FighterLook(f) for f in self.defs]
        self.backdrop = MenuBackdrop()
        self.preset_keys = list(ctx.controls.presets)
        rounds = [str(n) for n in ROUNDS_TO_WIN_CHOICES]
        labels = [preset_label(ctx.controls.presets[k]) for k in self.preset_keys]
        # The arena was picked on the screen before; this one only says which it is.
        self.stage_id = stage_id or stage_for_part(self.defs[0].part)
        self.stage = load_stage(self.stage_id)
        self.stage_options = stage_options or StageOptions()
        self.menu = Menu(
            [
                MenuItem("rounds", text.ROUNDS_TO_WIN, rounds, rounds.index(str(rounds_to_win))),
                *(
                    [MenuItem("level", text.DIFFICULTY, text.LEVEL_NAMES, ctx.settings.cpu_level)]
                    if cpu
                    else []
                ),
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
        if kind == "change" and key == "level":
            self.ctx.settings.cpu_level = self.menu.item("level").index
            self.ctx.save_settings()
        if kind == "change" and key == "controls":
            self.ctx.controls.active = self.preset_keys[self.menu.item("controls").index]
            self.ctx.save_controls()
        elif kind == "confirm" and key == "fight":
            from jojo_arena.ui.fight_scene import FightScene

            self.ctx.scenes.switch(
                FightScene(
                    self.ctx,
                    rounds_to_win=self.rounds_to_win,
                    fighter_ids=self.fighter_ids,
                    stage_id=self.stage_id,
                    bots=(False, self.cpu),
                    cpu_level=self.ctx.settings.cpu_level,
                    stage_options=self.stage_options,
                )
            )
        elif (kind == "confirm" and key == "back") or kind == "back":
            # Back one step: the arena select, with this arena still under the cursor.
            from jojo_arena.ui.stage_scene import StageSelectScene

            mode = "vs_cpu" if self.cpu else "versus"
            self.ctx.scenes.switch(
                StageSelectScene(
                    self.ctx,
                    mode,
                    self.fighter_ids,
                    cursor=self.stage_id,
                    options=self.stage_options,
                )
            )

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        center = width // 2
        title = text.MENU_VS_CPU if self.cpu else text.SETUP_TITLE
        font.draw(surface, title, (center, 8), GOLD, scale=2, align="center")
        for side, (look, fdef) in enumerate(zip(self.looks, self.defs, strict=True)):
            x = FEET_X[side]
            look.draw(surface, (x, FEET_Y), self.tick, scale=2, flip=side == 1)
            color = P1_COLOR if side == 0 else P2_COLOR
            tag = text.CPU if self.cpu and side == 1 else text.PLAYER_N.format(n=side + 1)
            font.draw(surface, tag, (x, 40), color, scale=2, align="center")
            font.draw(surface, fdef.name, (x, FEET_Y + 8), shade(fdef.color, 60), align="center")
            if fdef.stand_name:
                font.draw(surface, fdef.stand_name, (x, FEET_Y + 19), fdef.aura, align="center")
        font.draw(surface, text.VS, (center, 50), GOLD, scale=4, align="center")
        box = pygame.Rect(0, 0, 262, 69 + (15 if self.cpu else 0))
        box.midtop = (center, 104)
        draw_box(surface, box)
        self.menu.draw(surface, center, box.y + 9, spacing=15)
        arena = f"{text.STAGE} : {self.stage.name.upper()}"
        font.draw(surface, arena, (center, box.bottom + 6), GOLD, align="center")
        preset = self.ctx.controls.active_preset
        if preset.pads_needed() > len(self.ctx.inputs.pads):
            font.draw(surface, text.PADS_MISSING, (center, 222), WARNING, align="center")
        font.draw(surface, text.CONTROLS_FILE_HINT, (center, 236), DIM, align="center")
        draw_hints(surface, self.hints, (center, height - 14))
