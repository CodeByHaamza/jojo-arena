"""The fight screen: reads both players, steps the rounds, draws them; pause and results."""

from __future__ import annotations

import pygame

from jojo_arena.characters import get_fighter
from jojo_arena.combat.bot import SimpleBot
from jojo_arena.combat.rounds import Phase, Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.scene import Scene
from jojo_arena.stages import load_stage
from jojo_arena.ui import text
from jojo_arena.ui.fight_view import FightView
from jojo_arena.ui.hud import Hud
from jojo_arena.ui.menu import Menu, MenuItem

RESULT_MENU_AFTER_F = 120  # let the victory sink in before offering a rematch


class FightScene(Scene):
    def __init__(
        self,
        ctx: GameContext,
        rounds_to_win: int = 3,
        fighter_ids: tuple[str, str] = ("mannequin_red", "mannequin_blue"),
        stage_id: str = "cairo_night",
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
        self.demo = all(bots)
        self.view = FightView(self.stage, self.fighter_defs)
        self.hud = Hud(self.fighter_defs)
        self.pause_menu: Menu | None = None
        self.result_menu: Menu | None = None
        self._veil: pygame.Surface | None = None
        self._new_rounds()

    def _new_rounds(self) -> None:
        kits = (self.fighter_defs[0].kit, self.fighter_defs[1].kit)
        self.rounds = Rounds(kits, self.rules, self.stage.build_arena, self.rounds_to_win)
        self.pause_menu = None
        self.result_menu = None

    # Update -----------------------------------------------------------------------------

    def update(self) -> None:
        if self.pause_menu is not None:
            self._update_pause()
            return
        if self.result_menu is not None:
            self._update_result()
            return
        match = self.rounds.match
        frames = []
        for i, source in enumerate(self.sources):
            frame = source.read(self.ctx.inputs)
            bot = self.bots[i]
            if bot is not None:
                me = match.fighters[i]
                frame = bot.think(me, match.opponent(me))
            frames.append(frame)
        if not self.demo and any(f.was_pressed("pause") for f in frames):
            self._open_pause()
            return
        events = self.rounds.step((frames[0], frames[1]))
        self.view.on_events(events)
        self.hud.on_events(events, self.rounds)
        self.view.update()
        self.hud.update(self.rounds)
        if self.rounds.phase == Phase.MATCH_OVER and self.rounds.phase_f >= RESULT_MENU_AFTER_F:
            if self.demo:
                self._new_rounds()
            else:
                self.result_menu = Menu(
                    [
                        MenuItem("rematch", text.REMATCH),
                        MenuItem("settings", text.SETTINGS),
                        MenuItem("title", text.TO_TITLE),
                    ]
                )

    def _open_pause(self) -> None:
        self.pause_menu = Menu(
            [
                MenuItem("resume", text.RESUME),
                MenuItem("restart", text.RESTART),
                MenuItem("leave", text.LEAVE_FIGHT),
            ]
        )

    def _update_pause(self) -> None:
        frame = self.ctx.read_menu()
        action = self.pause_menu.handle(frame)
        if action in (("confirm", "resume"), ("back", "")) or frame.was_pressed("pause"):
            self.pause_menu = None
        elif action == ("confirm", "restart"):
            self._new_rounds()
        elif action == ("confirm", "leave"):
            self._go_to_title()

    def _update_result(self) -> None:
        action = self.result_menu.handle(self.ctx.read_menu())
        if action == ("confirm", "rematch"):
            self._new_rounds()
        elif action == ("confirm", "settings"):
            from jojo_arena.ui.setup_scene import SetupScene

            self.ctx.scenes.switch(SetupScene(self.ctx, self.rounds_to_win))
        elif action == ("confirm", "title"):
            self._go_to_title()

    def _go_to_title(self) -> None:
        from jojo_arena.ui.title_scene import TitleScene

        self.ctx.scenes.switch(TitleScene(self.ctx))

    # Draw -------------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        self.view.draw(surface, self.rounds.match)
        self.hud.draw(surface, self.rounds, announcements=self.pause_menu is None)
        center = surface.get_width() // 2
        if self.pause_menu is not None:
            surface.blit(self._dim(surface.get_size()), (0, 0))
            font.draw(surface, text.PAUSE, (center, 80), (255, 214, 90), scale=3, align="center")
            self.pause_menu.draw(surface, center, 130, spacing=16)
        elif self.result_menu is not None:
            self.result_menu.draw(surface, center, 170, spacing=16)

    def _dim(self, size: tuple[int, int]) -> pygame.Surface:
        if self._veil is None or self._veil.get_size() != size:
            self._veil = pygame.Surface(size, pygame.SRCALPHA)
            self._veil.fill((10, 8, 24, 160))
        return self._veil
