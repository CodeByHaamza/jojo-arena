"""Training mode: the fight screen with no clock, refills, a dummy and a combo counter.

The pause menu holds the training settings: what the dummy does, infinite life and
Heart Heat, putting both fighters back in place.
"""

from __future__ import annotations

import pygame

from jojo_arena.combat.training import Dummy, Training, dummy_input
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.actions import InputFrame, merge_frames
from jojo_arena.ui import text
from jojo_arena.ui.fight_scene import FightScene
from jojo_arena.ui.input_display import ACTIONS, InputDisplay
from jojo_arena.ui.labels import action_label
from jojo_arena.ui.menu import MenuItem
from jojo_arena.ui.widgets import DIM, FAINT, GOLD, WHITE

DUMMY_LABELS = {
    Dummy.STAND: text.DUMMY_STAND,
    Dummy.GUARD: text.DUMMY_GUARD,
    Dummy.PLAYER: text.DUMMY_PLAYER,
}
SWITCH = [text.INFINITE, text.NORMAL]


class TrainingScene(FightScene):
    mode = "training"

    def __init__(
        self,
        ctx: GameContext,
        fighter_ids: tuple[str, str] = ("jotaro_p3", "dio_p3"),
        stage_id: str = "cairo_night",
    ) -> None:
        self.dummy = Dummy.STAND
        super().__init__(ctx, rounds_to_win=0, fighter_ids=fighter_ids, stage_id=stage_id)
        player = ctx.controls.active_preset.players[0]
        pause = action_label(player, "pause", ctx.inputs)
        self.hint = text.TRAINING_HINT.format(key=pause)
        self.inputs_shown = True
        self.input_display = InputDisplay({a: action_label(player, a, ctx.inputs) for a in ACTIONS})

    @property
    def training(self) -> Training:
        return self.rounds

    def _new_rounds(self) -> None:
        kits = (self.fighter_defs[0].kit, self.fighter_defs[1].kit)
        self.rounds = Training(kits, self.rules, self.stage.build_arena)
        self.pause_menu = None
        self.result_menu = None

    def _read_frames(self) -> list[InputFrame]:
        frames = super()._read_frames()
        dummy = dummy_input(self.dummy)
        if dummy is not None:
            # Alone at training: player 1 can use any device, keyboard or pad.
            frames = [merge_frames(*frames), dummy]
        self.input_display.update(frames[0])
        return frames

    def _pause_items(self) -> list[MenuItem]:
        dummies = list(Dummy)
        return [
            MenuItem("resume", text.RESUME),
            MenuItem("moves", text.MOVE_LIST),
            MenuItem(
                "dummy",
                text.DUMMY_MODE,
                [DUMMY_LABELS[d] for d in dummies],
                dummies.index(self.dummy),
            ),
            MenuItem("life", text.LIFE, SWITCH, 0 if self.training.infinite_life else 1),
            MenuItem("hh", text.HH_GAUGE, SWITCH, 0 if self.training.infinite_hh else 1),
            MenuItem(
                "inputs", text.INPUTS, [text.SHOWN, text.HIDDEN], 0 if self.inputs_shown else 1
            ),
            MenuItem("reset", text.RESET_POSITIONS),
            MenuItem("change", text.CHANGE_FIGHTERS),
            MenuItem("menu", text.MAIN_MENU),
        ]

    def _pause_action(self, kind: str, key: str) -> None:
        menu = self.pause_menu
        if kind == "change":
            index = menu.item(key).index
            if key == "dummy":
                self.dummy = list(Dummy)[index]
            elif key == "life":
                self.training.infinite_life = index == 0
            elif key == "hh":
                self.training.infinite_hh = index == 0
            elif key == "inputs":
                self.inputs_shown = index == 0
            self.training.apply_options()
        elif (kind, key) == ("confirm", "reset"):
            self.training.reset()
            self.pause_menu = None
        else:
            super()._pause_action(kind, key)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        font.draw(surface, text.TRAINING, (width // 2, 22), GOLD, align="center")
        dummy = f"{text.DUMMY_MODE} : {DUMMY_LABELS[self.dummy]}"
        font.draw(surface, dummy, (width - 26, 31), DIM, align="right")
        for attacker, combo in enumerate(self.training.combos):
            if not combo.visible:
                continue
            x, align = (26, "left") if attacker == 0 else (width - 26, "right")
            y = 44
            color = GOLD if combo.live else DIM
            hits = text.COMBO_HITS.format(n=combo.hits)
            font.draw(surface, hits, (x, y), color, scale=2, align=align)
            damage = text.COMBO_DAMAGE.format(n=combo.damage)
            font.draw(surface, damage, (x, y + 20), WHITE if combo.live else DIM, align=align)
        font.draw(surface, self.hint, (width // 2, height - 12), FAINT, align="center")
        if self.inputs_shown:
            self.input_display.draw(surface, 20, 226)
