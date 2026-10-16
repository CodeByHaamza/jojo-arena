"""Arcade: a ladder of fights against the computer, each one a little harder, in the
opponent's own arena, up to a final boss. Losing offers to continue."""

from __future__ import annotations

import random

import pygame

from jojo_arena.characters import FighterDef, get_fighter, load_parts, load_roster
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import shade
from jojo_arena.stages import load_stage, stage_for_part
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.fight_scene import FightScene
from jojo_arena.ui.icons import draw_icon
from jojo_arena.ui.labels import menu_key
from jojo_arena.ui.menu import MenuItem
from jojo_arena.ui.portraits import FighterLook
from jojo_arena.ui.widgets import DIM, FAINT, GOLD, P1_COLOR, P2_COLOR, WHITE, draw_hints

LADDER_LENGTH = 6
BOSS = "dio_p3"
BOSS_STANDIN = "dio_p1"  # the boss when the player is DIO himself
ROUNDS_TO_WIN = 2
CELL = 30


def build_ladder(player_id: str, seed: int) -> list[str]:
    """The opponents in order: the others shuffled, then the final boss."""
    boss = BOSS if player_id != BOSS else BOSS_STANDIN
    others = [f.id for f in load_roster() if f.selectable and f.id not in (player_id, boss)]
    random.Random(seed).shuffle(others)
    return others[: LADDER_LENGTH - 1] + [boss]


def ladder_levels(base: int, count: int) -> list[int]:
    """The computer's level for each fight: a step easier at first, harder at the end."""
    levels = []
    for i in range(count):
        step = -1 if i < count // 3 else (1 if i >= count - count // 3 else 0)
        levels.append(max(0, min(3, base + step)))
    return levels


class ArcadeScene(Scene):
    def __init__(
        self,
        ctx: GameContext,
        player_id: str,
        ladder: list[str] | None = None,
        index: int = 0,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.player_id = player_id
        seed = seed if seed is not None else random.randrange(1 << 30)
        self.ladder = ladder or build_ladder(player_id, seed)
        self.levels = ladder_levels(ctx.settings.cpu_level, len(self.ladder))
        self.index = index
        self.parts = {p.number: p for p in load_parts()}
        self.player = get_fighter(player_id)
        self.player_look = FighterLook(self.player)
        self.opponents: list[FighterDef] = [get_fighter(i) for i in self.ladder]
        self.opponent_looks = [FighterLook(f) for f in self.opponents]
        self.backdrop = MenuBackdrop(part=self.opponent.part or None)
        self.tick = 0
        self.hints = [
            (menu_key("confirm", ctx.inputs), text.FIGHT),
            (menu_key("back", ctx.inputs), text.GIVE_UP),
        ]

    @property
    def opponent(self) -> FighterDef:
        return self.opponents[min(self.index, len(self.opponents) - 1)]

    @property
    def level(self) -> int:
        return self.levels[min(self.index, len(self.levels) - 1)]

    @property
    def final(self) -> bool:
        return self.index == len(self.ladder) - 1

    def advanced(self) -> Scene:
        """After a win: the next rung of the ladder, or the ending."""
        if self.final:
            return ArcadeClearScene(self.ctx, self.player_id)
        return ArcadeScene(self.ctx, self.player_id, self.ladder, self.index + 1)

    def update(self) -> None:
        self.tick += 1
        frame = self.ctx.read_menu()
        if frame.was_pressed("confirm"):
            self.ctx.scenes.switch(ArcadeFight(self.ctx, self))
        elif frame.was_pressed("back"):
            from jojo_arena.ui.main_menu import MainMenuScene

            self.ctx.scenes.switch(MainMenuScene(self.ctx, cursor="arcade"))

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        font.draw(surface, text.MENU_ARCADE, (width // 2, 8), GOLD, scale=2, align="center")
        stage = (
            text.FINAL_BOSS
            if self.final
            else text.ARCADE_STAGE.format(n=self.index + 1, total=len(self.ladder))
        )
        font.draw(surface, stage, (width // 2, 32), WHITE, align="center")
        self._draw_ladder(surface)
        self.player_look.draw(surface, (110, 200), self.tick, scale=2)
        self.opponent_looks[self.index].draw(surface, (370, 200), self.tick, scale=2, flip=True)
        font.draw(surface, text.VS, (width // 2, 136), GOLD, scale=4, align="center")
        for x, fdef, color in ((110, self.player, P1_COLOR), (370, self.opponent, P2_COLOR)):
            name_color = shade(fdef.color, 60)
            font.draw(surface, fdef.name, (x, 210), name_color, align="center")
            font.draw(surface, fdef.stand_name or fdef.role, (x, 221), color, align="center")
        arena = load_stage(stage_for_part(self.opponent.part)).name.upper()
        level = text.LEVEL_NAMES[self.level]
        font.draw(surface, f"{text.STAGE} : {arena}", (width // 2, 236), DIM, align="center")
        font.draw(surface, f"{text.DIFFICULTY} : {level}", (width // 2, 246), DIM, align="center")
        draw_hints(surface, self.hints, (width // 2, height - 12))

    def _draw_ladder(self, surface: pygame.Surface) -> None:
        """The rungs: beaten opponents dimmed, the next one framed, the boss last."""
        count = len(self.opponents)
        gap = 6
        x = surface.get_width() // 2 - (count * CELL + (count - 1) * gap) // 2
        for i, (fdef, look) in enumerate(zip(self.opponents, self.opponent_looks, strict=True)):
            rect = pygame.Rect(x, 48, CELL, CELL)
            surface.fill(shade(fdef.color, -90), rect)
            face = pygame.transform.scale_by(look.face(15), 2)
            surface.blit(face, face.get_rect(midbottom=(rect.centerx, rect.bottom)))
            part = self.parts.get(fdef.part)
            if part is not None:
                draw_icon(surface, part.emblem, (rect.right - 10, rect.y + 1))
            if i < self.index:
                veil = pygame.Surface(rect.size, pygame.SRCALPHA)
                veil.fill((10, 8, 20, 170))
                surface.blit(veil, rect)
                pygame.draw.line(surface, (230, 60, 60), rect.topleft, rect.bottomright, 2)
            border = GOLD if i == self.index else (FAINT if i > self.index else DIM)
            pygame.draw.rect(surface, border, rect.inflate(4, 4) if i == self.index else rect, 1)
            x += CELL + gap


class ArcadeFight(FightScene):
    """One fight of the ladder: two rounds to win, in the opponent's arena."""

    def __init__(self, ctx: GameContext, arcade: ArcadeScene) -> None:
        self.arcade = arcade
        opponent = arcade.opponent
        super().__init__(
            ctx,
            rounds_to_win=ROUNDS_TO_WIN,
            fighter_ids=(arcade.player_id, opponent.id),
            stage_id=stage_for_part(opponent.part),
            bots=(False, True),
            cpu_level=arcade.level,
        )
        self.mode = "arcade"

    def _result_items(self) -> list[MenuItem]:
        if self.rounds.winner == 0:
            label = text.ARCADE_CLEAR if self.arcade.final else text.NEXT_FIGHT
            return [MenuItem("next", label), MenuItem("menu", text.MAIN_MENU)]
        return [MenuItem("retry", text.CONTINUE), MenuItem("menu", text.GIVE_UP)]

    def _update_result(self) -> None:
        action = self.result_menu.handle(self.ctx.read_menu())
        if action == ("confirm", "next"):
            self.ctx.scenes.switch(self.arcade.advanced())
        elif action == ("confirm", "retry"):
            self._new_rounds()
        elif action == ("confirm", "menu"):
            self._go_to_menu()


class ArcadeClearScene(Scene):
    """The ladder is cleared: the champion strikes their pose."""

    def __init__(self, ctx: GameContext, player_id: str) -> None:
        super().__init__()
        self.ctx = ctx
        self.player = get_fighter(player_id)
        self.look = FighterLook(self.player)
        self.backdrop = MenuBackdrop(part=self.player.part or None)
        self.tick = 0
        self.hints = [(menu_key("confirm", ctx.inputs), text.MAIN_MENU)]

    def update(self) -> None:
        self.tick += 1
        frame = self.ctx.read_menu()
        if frame.was_pressed("confirm") or frame.was_pressed("back"):
            from jojo_arena.ui.main_menu import MainMenuScene

            self.ctx.scenes.switch(MainMenuScene(self.ctx, cursor="arcade"))

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        font.draw(surface, text.ARCADE_CLEAR, (width // 2, 24), GOLD, scale=4, align="center")
        subtitle = text.ARCADE_CLEAR_SUB.format(name=self.player.name)
        font.draw(surface, subtitle, (width // 2, 66), WHITE, align="center")
        self.look.draw(surface, (width // 2, 220), self.tick, scale=3, anim="pose")
        draw_hints(surface, self.hints, (width // 2, height - 12))
