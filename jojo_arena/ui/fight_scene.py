"""The fight screen: reads both players, steps the rounds, draws them."""

from __future__ import annotations

import pygame

from jojo_arena.characters import get_fighter
from jojo_arena.combat.bot import SimpleBot
from jojo_arena.combat.rounds import Phase, Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.context import GameContext
from jojo_arena.engine.scene import Scene
from jojo_arena.stages import load_stage
from jojo_arena.ui.fight_view import FightView

RESTART_AFTER_MATCH_F = 240


class FightScene(Scene):
    def __init__(
        self,
        ctx: GameContext,
        fighter_ids: tuple[str, str] = ("mannequin_red", "mannequin_blue"),
        stage_id: str = "cairo_night",
        rounds_to_win: int = 2,
        bots: tuple[bool, bool] = (False, False),
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.fighter_defs = [get_fighter(i) for i in fighter_ids]
        self.stage = load_stage(stage_id)
        self.rules = load_rules()
        self.rounds_to_win = rounds_to_win
        self.sources = [p.build_source() for p in ctx.controls.active_preset.players]
        self.bots = [SimpleBot(seed=i + 1) if bot else None for i, bot in enumerate(bots)]
        self.view = FightView(self.stage, self.fighter_defs)
        self._new_rounds()

    def _new_rounds(self) -> None:
        kits = (self.fighter_defs[0].kit, self.fighter_defs[1].kit)
        self.rounds = Rounds(kits, self.rules, self.stage.build_arena, self.rounds_to_win)

    def update(self) -> None:
        match = self.rounds.match
        frames = []
        for i, source in enumerate(self.sources):
            frame = source.read(self.ctx.inputs)
            bot = self.bots[i]
            if bot is not None:
                me = match.fighters[i]
                frame = bot.think(me, match.opponent(me))
            frames.append(frame)
        events = self.rounds.step((frames[0], frames[1]))
        self.view.on_events(events)
        self.view.update()
        if self.rounds.phase == Phase.MATCH_OVER and self.rounds.phase_f >= RESTART_AFTER_MATCH_F:
            self._new_rounds()

    def draw(self, surface: pygame.Surface) -> None:
        match = self.rounds.match
        self.view.draw(surface, match)
        # Temporary life bars until the real HUD.
        for fighter in match.fighters:
            width = round(180 * fighter.hp / fighter.max_hp)
            x = 20 if fighter.index == 0 else 460 - width
            surface.fill((23, 18, 31), (19 if fighter.index == 0 else 279, 11, 182, 8))
            surface.fill(self.fighter_defs[fighter.index].color, (x, 12, width, 6))
