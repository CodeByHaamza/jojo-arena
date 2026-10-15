"""The fight screen: reads both players, steps the Match, draws it."""

from __future__ import annotations

import pygame

from jojo_arena.characters import get_fighter
from jojo_arena.combat.bot import SimpleBot
from jojo_arena.combat.fighter import State
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.context import GameContext
from jojo_arena.engine.scene import Scene
from jojo_arena.stages import load_stage
from jojo_arena.ui.fight_view import FightView

RESTART_AFTER_KO_F = 150


class FightScene(Scene):
    def __init__(
        self,
        ctx: GameContext,
        fighter_ids: tuple[str, str] = ("mannequin_red", "mannequin_blue"),
        stage_id: str = "cairo_night",
        bots: tuple[bool, bool] = (False, False),
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.fighter_defs = [get_fighter(i) for i in fighter_ids]
        self.stage = load_stage(stage_id)
        self.rules = load_rules()
        self.sources = [p.build_source() for p in ctx.controls.active_preset.players]
        self.bots = [SimpleBot(seed=i + 1) if bot else None for i, bot in enumerate(bots)]
        self.view = FightView(self.stage, self.fighter_defs)
        self._new_match()

    def _new_match(self) -> None:
        kits = (self.fighter_defs[0].kit, self.fighter_defs[1].kit)
        self.match = Match(kits, self.rules, self.stage.build_arena())
        self.ko_timer = 0

    def update(self) -> None:
        frames = []
        for i, source in enumerate(self.sources):
            frame = source.read(self.ctx.inputs)
            bot = self.bots[i]
            if bot is not None:
                me = self.match.fighters[i]
                frame = bot.think(me, self.match.opponent(me))
            frames.append(frame)
        events = self.match.step((frames[0], frames[1]))
        self.view.on_events(events)
        self.view.update()
        if any(f.state == State.KO for f in self.match.fighters):
            self.ko_timer += 1
            if self.ko_timer >= RESTART_AFTER_KO_F:
                self._new_match()

    def draw(self, surface: pygame.Surface) -> None:
        self.view.draw(surface, self.match)
        # Temporary life bars until the real HUD.
        for fighter in self.match.fighters:
            width = round(180 * fighter.hp / fighter.max_hp)
            x = 20 if fighter.index == 0 else 460 - width
            surface.fill((23, 18, 31), (19 if fighter.index == 0 else 279, 11, 182, 8))
            surface.fill(self.fighter_defs[fighter.index].color, (x, 12, width, 6))
