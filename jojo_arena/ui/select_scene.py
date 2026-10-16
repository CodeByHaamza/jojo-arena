"""Character select: one tab per JoJo part, each a grid of its fighters (and slots for
those still to come), a big preview for each side, and the move list one key away.

Player 1 picks first, then player 2 (or the training dummy). Back undoes the last pick.
"""

from __future__ import annotations

import pygame

from jojo_arena.characters import FighterDef, PartDef, load_parts, load_roster
from jojo_arena.combat.rules import load_rules
from jojo_arena.context import GameContext
from jojo_arena.engine import audio, font
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import shade
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.icons import draw_icon, draw_part_tabs
from jojo_arena.ui.labels import menu_key
from jojo_arena.ui.movelist import MoveListPanel
from jojo_arena.ui.portraits import FighterLook
from jojo_arena.ui.widgets import (
    DIM,
    FAINT,
    GOLD,
    P1_COLOR,
    P2_COLOR,
    WHITE,
    draw_box,
    draw_hints,
    draw_toast,
    draw_wrapped,
)

GRID_COLS, GRID_ROWS = 4, 3
CELL, GAP = 30, 2
GRID_X = 240 - (GRID_COLS * (CELL + GAP) - GAP) // 2
GRID_Y = 62
TABS_Y = 45
FACE = 15  # px of the head shown in a cell, before doubling
SIDE_W = 152
FEET_Y = 150
TOAST_F = 90
PICK_FLASH_F = 14

MODES = ("training", "versus", "vs_cpu", "arcade")


class CharacterSelectScene(Scene):
    def __init__(
        self,
        ctx: GameContext,
        mode: str = "versus",
        picks: tuple[str, ...] = (),
        cursor: str | None = None,
    ) -> None:
        super().__init__()
        if mode not in MODES:
            raise ValueError(f"unknown mode '{mode}'")
        self.ctx = ctx
        self.mode = mode
        self.rules = load_rules()
        self.parts: dict[int, PartDef] = {p.number: p for p in load_parts()}
        self.part_numbers = sorted(self.parts) or [0]
        self.roster: list[FighterDef] = [f for f in load_roster() if f.selectable]
        self.looks = [FighterLook(f) for f in self.roster]
        ids = [f.id for f in self.roster]
        self.picks: list[int] = [ids.index(i) for i in picks if i in ids][:2]
        first = ids.index(cursor) if cursor in ids else (self.picks[-1] if self.picks else 0)
        self.tab = self.part_numbers[0]
        self.cell = 0
        self.backdrop = MenuBackdrop(part=self.tab)
        if self.roster:
            self._show(first)
        self.move_list: MoveListPanel | None = None
        self.toast_f = 0
        self.flash_f = [0, 0]
        self.tick = 0
        self.hints = [
            (menu_key("confirm", ctx.inputs), text.HINT_CONFIRM),
            (menu_key("info", ctx.inputs), text.HINT_INFO),
            (f"{menu_key('prev', ctx.inputs)} {menu_key('next', ctx.inputs)}", text.HINT_PART),
            (menu_key("back", ctx.inputs), text.HINT_BACK),
        ]

    # Queries ----------------------------------------------------------------------------

    @property
    def picking(self) -> int:
        """Which side is choosing: 0 = player 1, 1 = player 2 or the dummy."""
        return len(self.picks)

    @property
    def fighter_ids(self) -> tuple[str, ...]:
        return tuple(self.roster[i].id for i in self.picks)

    @property
    def picks_needed(self) -> int:
        """Arcade: the player alone picks; the opponents come from the ladder."""
        return 1 if self.mode == "arcade" else 2

    def side_label(self, side: int) -> str:
        if side == 0:
            return text.P1
        if self.mode == "training":
            return text.DUMMY
        return text.CPU if self.mode in ("vs_cpu", "arcade") else text.P2

    def part_of(self, index: int) -> int:
        """The tab of a fighter: its part (the first tab if it has none)."""
        part = self.roster[index].part
        return part if part in self.part_numbers else self.part_numbers[0]

    def grid(self) -> list[int]:
        """Roster indexes of the fighters in the current tab, in order."""
        return [i for i in range(len(self.roster)) if self.part_of(i) == self.tab]

    @property
    def cursor(self) -> int | None:
        """Roster index under the cursor, or None on an empty cell."""
        grid = self.grid()
        return grid[self.cell] if self.cell < len(grid) else None

    def _hovered(self) -> FighterDef | None:
        index = self.cursor
        return self.roster[index] if index is not None else None

    def _show(self, index: int) -> None:
        """Open the tab of that fighter and put the cursor on it."""
        self._open_tab(self.part_of(index))
        self.cell = self.grid().index(index)

    def _open_tab(self, part: int) -> None:
        self.tab = part
        self.backdrop.part = part

    # Update -----------------------------------------------------------------------------

    def update(self) -> None:
        self.tick += 1
        self.toast_f = max(0, self.toast_f - 1)
        self.flash_f = [max(0, f - 1) for f in self.flash_f]
        frame = self.ctx.read_menu()
        if self.move_list is not None:
            if not self.move_list.handle(frame):
                self.move_list = None
            return
        step = frame.presses("next") - frame.presses("prev")
        if step:
            at = self.part_numbers.index(self.tab)
            self._open_tab(self.part_numbers[(at + step) % len(self.part_numbers)])
        col, row = self.cell % GRID_COLS, self.cell // GRID_COLS
        col = (col + frame.presses("right") - frame.presses("left")) % GRID_COLS
        row = (row + frame.presses("down") - frame.presses("up")) % GRID_ROWS
        if row * GRID_COLS + col != self.cell or step:
            audio.play("menu_move")
        self.cell = row * GRID_COLS + col
        if frame.was_pressed("confirm"):
            self._pick()
        elif frame.was_pressed("back"):
            if self.picks:
                self._show(self.picks.pop())
            else:
                from jojo_arena.ui.main_menu import MainMenuScene

                self.ctx.scenes.switch(MainMenuScene(self.ctx, cursor=self.mode))
        elif frame.was_pressed("info") and self._hovered() is not None:
            # Training: the move list is for player 1, who practises with it.
            side = 0 if self.mode == "training" else min(self.picking, 1)
            player = self.ctx.controls.active_preset.players[side]
            self.move_list = MoveListPanel(
                self._hovered(),
                player,
                self.rules,
                text.PLAYER_N.format(n=side + 1),
                self.ctx.inputs,
            )

    def _pick(self) -> None:
        if self._hovered() is None:
            self.toast_f = TOAST_F
            audio.play("menu_locked")
            return
        audio.play("menu_ok")
        self.flash_f[self.picking] = PICK_FLASH_F
        self.picks.append(self.cursor)  # not None: a fighter is hovered
        if len(self.picks) < self.picks_needed:
            return
        ids = self.fighter_ids
        if self.mode == "arcade":
            from jojo_arena.ui.arcade_scene import ArcadeScene

            self.ctx.scenes.switch(ArcadeScene(self.ctx, ids[0]))
            return
        if self.mode == "training":
            from jojo_arena.stages import stage_for_part
            from jojo_arena.ui.training_scene import TrainingScene

            stage = stage_for_part(self.roster[self.picks[0]].part)
            scene = TrainingScene(self.ctx, fighter_ids=(ids[0], ids[1]), stage_id=stage)
            self.ctx.scenes.switch(scene)
        else:
            from jojo_arena.ui.setup_scene import SetupScene

            cpu = self.mode == "vs_cpu"
            self.ctx.scenes.switch(SetupScene(self.ctx, fighter_ids=(ids[0], ids[1]), cpu=cpu))

    # Draw -------------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        title = {
            "training": text.MENU_TRAINING,
            "vs_cpu": text.MENU_VS_CPU,
            "arcade": text.MENU_ARCADE,
        }.get(self.mode, text.MENU_VERSUS)
        font.draw(surface, title, (width // 2, 8), GOLD, scale=2, align="center")
        if self.picking < 2:
            if self.picking == 0:
                step, color = text.PICK_P1, P1_COLOR
            elif self.mode == "training":
                step, color = text.PICK_DUMMY, P2_COLOR
            elif self.mode == "vs_cpu":
                step, color = text.PICK_CPU, P2_COLOR
            else:
                step, color = text.PICK_P2, P2_COLOR
            font.draw(surface, step, (width // 2, 32), color, align="center")
        self._draw_tabs(surface)
        self._draw_grid(surface)
        part = self.parts.get(self.tab)
        if part is not None:
            name = f"{text.PART_SHORT.format(n=part.number)} - {part.title}"
            font.draw(surface, name, (width // 2, 159), shade(part.colors[0], 50), align="center")
        font.draw(surface, text.VS, (width // 2, 172), GOLD, scale=3, align="center")
        for side in (0, 1):
            self._draw_side(surface, side)
        draw_hints(surface, self.hints, (width // 2, height - 14))
        draw_toast(surface, text.SOON_TOAST, self.toast_f, y=210)
        if self.move_list is not None:
            self.move_list.draw(surface)

    def _cell_rect(self, index: int) -> pygame.Rect:
        col, row = index % GRID_COLS, index // GRID_COLS
        return pygame.Rect(GRID_X + col * (CELL + GAP), GRID_Y + row * (CELL + GAP), CELL, CELL)

    def _draw_tabs(self, surface: pygame.Surface) -> None:
        """One tab per part, its emblem inside; parts with nobody yet stay dim."""
        filled = {self.part_of(i) for i in range(len(self.roster))}
        draw_part_tabs(surface, self.parts, self.part_numbers, self.tab, filled, TABS_Y)

    def _draw_grid(self, surface: pygame.Surface) -> None:
        grid = self.grid()
        part = self.parts.get(self.tab)
        for cell in range(GRID_COLS * GRID_ROWS):
            rect = self._cell_rect(cell)
            if cell < len(grid):
                index = grid[cell]
                fdef = self.roster[index]
                surface.fill(shade(fdef.color, -90), rect)
                face = pygame.transform.scale_by(self.looks[index].face(FACE), 2)
                surface.blit(face, face.get_rect(midbottom=(rect.centerx, rect.bottom)))
                surface.fill(fdef.color, (rect.x, rect.bottom - 2, rect.width, 2))
                pygame.draw.rect(surface, (96, 84, 132), rect, 1)
                if part is not None:
                    draw_icon(surface, part.emblem, (rect.right - 10, rect.y + 1))
            else:
                surface.fill((20, 16, 34), rect)
                pygame.draw.rect(surface, (52, 46, 72), rect, 1)
                font.draw(surface, "?", (rect.centerx, rect.y + 11), FAINT, align="center")
        # Picked cells keep a tag; the cursor of the side choosing blinks over its cell.
        for side, index in enumerate(self.picks):
            if index not in grid:
                continue  # picked in another tab
            rect = self._cell_rect(grid.index(index))
            color = P1_COLOR if side == 0 else P2_COLOR
            pygame.draw.rect(surface, color, rect, 1)
            tag = "1" if side == 0 else "2"
            surface.fill(color, (rect.x, rect.y, 7, 9))
            font.draw(surface, tag, (rect.x + 1, rect.y), (20, 16, 34), outline=None)
        if self.picking < 2:
            color = P1_COLOR if self.picking == 0 else P2_COLOR
            rect = self._cell_rect(self.cell).inflate(4, 4)
            thickness = 2 if (self.tick // 12) % 2 == 0 else 1
            pygame.draw.rect(surface, color, rect, thickness)

    def _draw_side(self, surface: pygame.Surface, side: int) -> None:
        width = surface.get_width()
        x0 = 8 if side == 0 else width - 8 - SIDE_W
        center = x0 + SIDE_W // 2
        color = P1_COLOR if side == 0 else P2_COLOR
        locked = side == self.picking and self.cursor is None
        if side < self.picking:
            index: int | None = self.picks[side]
        elif side == self.picking:
            index = self.cursor
        else:
            index = None  # waiting for player 1
        box = pygame.Rect(x0, FEET_Y + 6, SIDE_W, 96)

        if index is not None:
            # The fighter faces the middle; its Stand looms behind, towards the edge.
            feet_x = center + 12 if side == 0 else center - 12
            self.looks[index].draw(surface, (feet_x, FEET_Y), self.tick, scale=2, flip=side == 1)
            if self.flash_f[side]:
                strength = self.flash_f[side] / PICK_FLASH_F
                flash = pygame.Surface((SIDE_W, 110), pygame.SRCALPHA)
                flash.fill((255, 255, 255, round(150 * strength)))
                surface.blit(flash, (x0, FEET_Y - 100), special_flags=pygame.BLEND_RGBA_ADD)
        draw_box(surface, box, border=color if side < self.picking else None)

        # Side tag on the box: "J1", "J2" or "MANNEQUIN", then "READY!" once picked.
        label = self.side_label(side)
        tag = pygame.Rect(box.x, box.y - 11, font.text_width(label) + 8, 11)
        surface.fill(color, tag)
        font.draw(surface, label, (tag.x + 4, tag.y + 1), (20, 16, 34), outline=None)
        if side < self.picking:
            font.draw(surface, text.READY, (tag.right + 5, tag.y + 1), WHITE)

        if locked:
            font.draw(surface, text.LOCKED_NAME, (center, 96), FAINT, scale=3, align="center")
            font.draw(surface, text.SOON, (box.x + 5, box.y + 5), DIM, scale=2)
            return
        if index is None:
            font.draw(surface, text.WAITING, (box.centerx, box.y + 42), FAINT, align="center")
            return

        fdef = self.roster[index]
        y = box.y + 5
        name_scale = 2 if font.text_width(fdef.name, 2) <= SIDE_W - 8 else 1
        font.draw(surface, fdef.name, (box.x + 5, y), shade(fdef.color, 60), scale=name_scale)
        y += 10 * name_scale + 2
        if fdef.stand_name:
            font.draw(surface, fdef.stand_name, (box.x + 5, y), fdef.aura)
            y += 11
        if fdef.role:
            font.draw(surface, fdef.role, (box.x + 5, y), WHITE)
            y += 11
        hp = text.HP.format(hp=fdef.kit.max_hp)
        font.draw(surface, hp, (box.x + 5, y), DIM)
        bar_x = box.x + 10 + font.text_width(hp)
        bar_w = round(60 * min(1.0, fdef.kit.max_hp / 1100))
        surface.fill((40, 34, 56), (bar_x, y + 2, 60, 5))
        surface.fill((240, 200, 70), (bar_x, y + 2, bar_w, 5))
        y += 12
        lines = font.wrap(fdef.blurb, SIDE_W - 10)[: max(0, (box.bottom - y) // 10)]
        draw_wrapped(surface, " ".join(lines), (box.x + 5, y), SIDE_W - 10)
