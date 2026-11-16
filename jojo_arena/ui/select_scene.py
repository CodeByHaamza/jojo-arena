"""Character select: one tab per JoJo part, each a grid of its fighters (and slots for
those still to come), a big preview for each side, and the move list one key away.

Player 1 picks first, then player 2 (or the training dummy). Back undoes the last pick.
"""

from __future__ import annotations

import random
from dataclasses import replace

import pygame

from jojo_arena.characters import FighterDef, PartDef, load_parts, load_roster
from jojo_arena.combat.rules import load_rules
from jojo_arena.context import GameContext
from jojo_arena.engine import audio, font, i18n, music
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import shade
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.icons import draw_icon, draw_part_tabs
from jojo_arena.ui.labels import menu_key
from jojo_arena.ui.loadout import Loadout, distinct, random_outfit, resolve_loadout
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
# The lines of the outfit step, in the order they are shown.
OUTFIT_ROWS = ("costume", "color", "pose", "stand_pose")


class CharacterSelectScene(Scene):
    def __init__(
        self,
        ctx: GameContext,
        mode: str = "versus",
        picks: tuple[str, ...] = (),
        cursor: str | None = None,
    ) -> None:
        super().__init__()
        music.request("menu")
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
        # The outfit step: the side choosing the costume, the colour and the poses of the
        # fighter it just picked.
        self.choosing: int | None = None
        self.loadout = Loadout()
        self.row = 0  # index in self.outfit_rows()
        self.preview: FighterLook | None = None  # the fighter in the outfit being tried
        self.worn: dict[int, FighterLook] = {}  # each side that picked, dressed as it picked
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

    def rows(self) -> int:
        """Rows this tab needs. A part whose fighters fill two rows shows two, not
        three: an empty row at the bottom says nothing and eats the screen."""
        return max(1, min(GRID_ROWS, -(-len(self.grid()) // GRID_COLS)))

    def cells(self) -> int:
        """Cells the cursor may stand on. A finished part has no empty cell to land on:
        its last row stops at its last fighter."""
        part = self.parts.get(self.tab)
        if part is not None and part.complete:
            return max(1, len(self.grid()))
        return GRID_COLS * self.rows()

    def row_length(self, row: int) -> int:
        return max(1, min(GRID_COLS, self.cells() - row * GRID_COLS))

    def _move(self, dx: int, dy: int) -> None:
        """Move the cursor, wrapping around the grid, never onto a missing cell."""
        rows = self.rows()
        col, row = self.cell % GRID_COLS, min(self.cell // GRID_COLS, rows - 1)
        row = (row + dy) % rows
        col = min(col, self.row_length(row) - 1)
        col = (col + dx) % self.row_length(row)
        self.cell = row * GRID_COLS + col

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
        self.cell = min(self.cell, self.cells() - 1)

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
        if self.choosing is not None:
            self._update_outfit(frame)
            return
        step = frame.presses("next") - frame.presses("prev")
        if step:
            at = self.part_numbers.index(self.tab)
            self._open_tab(self.part_numbers[(at + step) % len(self.part_numbers)])
        before = self.cell
        self._move(
            frame.presses("right") - frame.presses("left"),
            frame.presses("down") - frame.presses("up"),
        )
        if self.cell != before or step:
            audio.play("menu_move")
        if frame.was_pressed("confirm"):
            self._pick()
        elif frame.was_pressed("back"):
            if self.picks:
                self.worn.pop(len(self.picks) - 1, None)
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

    # The outfit step --------------------------------------------------------------------

    def step_look(self) -> FighterLook | None:
        """The hovered fighter as the step shows it: in the outfit being tried."""
        if self.cursor is None:
            return None
        return self.preview or self.looks[self.cursor]

    def _poses(self, stand: bool) -> list[str]:
        look = self.step_look()
        if look is None:
            return []
        return [i for i, info in look.sprites.poses.items() if info.stand == stand]

    def _rival(self) -> Loadout | None:
        """What player 1 wears, when player 2 is picking the very same fighter."""
        if self.choosing != 1 or self.mode != "versus" or not self.picks:
            return None
        return self.ctx.loadouts[0] if self.picks[0] == self.cursor else None

    def choices(self, row: str) -> list[str]:
        """The ids one line of the step cycles through."""
        look = self.step_look()
        if look is None:
            return []
        if row == "costume":
            return ["", *self.roster[self.cursor].costumes]
        if row == "color":
            colors = list(look.sprites.colors)
            rival = self._rival()
            if rival is not None and rival.costume == self.loadout.costume and len(colors) > 1:
                taken = rival.color if rival.color in colors else colors[0]
                colors.remove(taken)  # player 1's: not player 2's to take
            return colors
        return self._poses(row == "stand_pose")

    def outfit_rows(self) -> list[str]:
        """The lines of the step: a costume or a colour only when there is a choice, a
        pose line whenever the sheet has poses of that kind."""
        rows = [row for row in ("costume", "color") if len(self.choices(row)) > 1]
        return rows + [row for row in ("pose", "stand_pose") if self.choices(row)]

    def _wants_outfit(self, side: int) -> bool:
        """A person picks for this side (not the computer, not the training dummy), and
        the hovered fighter has something to choose."""
        human = side == 0 or (side == 1 and self.mode == "versus")
        return human and bool(self.outfit_rows())

    def _wear(self, loadout: Loadout) -> None:
        """Try this outfit on: the preview is dressed, and what its sheet cannot play (a
        pose the costume lacks, a colour it does not have) falls back."""
        fdef = self.roster[self.cursor]
        if loadout.costume not in fdef.costumes:
            loadout = replace(loadout, costume="")
        plain = self.looks[self.cursor]
        first = next(iter(plain.sprites.colors), "")
        as_drawn = not loadout.costume and loadout.color in ("", first)
        self.preview = None if as_drawn else FighterLook(fdef, loadout)
        look = self.step_look()
        loadout = resolve_loadout(look.sprites, loadout)
        rival = self._rival()
        if rival is not None:
            moved = distinct(rival, loadout, list(look.sprites.colors))
            if moved != loadout:
                self._wear(moved)  # off player 1's colour: dressed again, once
                return
        self.loadout = loadout

    def _open_outfit(self, side: int) -> None:
        fighter_id = self.roster[self.cursor].id
        poses = self.ctx.settings.poses.get(fighter_id, ["", ""])
        outfit = self.ctx.settings.outfits.get(fighter_id, ["", ""])
        self.choosing = side
        self.row = 0
        self._wear(Loadout(poses[0], poses[1], outfit[0], outfit[1]))

    def _update_outfit(self, frame) -> None:
        rows = self.outfit_rows()
        down = frame.presses("down") - frame.presses("up")
        if down and len(rows) > 1:
            self.row = (self.row + down) % len(rows)
            audio.play("menu_move")
        turn = frame.presses("right") - frame.presses("left")
        if turn and rows:
            row = rows[self.row]
            ids = self.choices(row)
            current = getattr(self.loadout, row)
            at = ids.index(current) if current in ids else 0
            chosen = ids[(at + turn) % len(ids)]
            if row == "costume":
                # Another costume: in its first colour, the poses kept if it has them.
                self._wear(replace(self.loadout, costume=chosen, color=""))
                self.row = self.outfit_rows().index("costume")
            else:
                self._wear(replace(self.loadout, **{row: chosen}))
            audio.play("menu_move")
        if frame.was_pressed("confirm"):
            side, fighter_id = self.choosing, self.roster[self.cursor].id
            worn = self.loadout
            self.ctx.settings.poses[fighter_id] = [worn.pose, worn.stand_pose]
            self.ctx.settings.outfits[fighter_id] = [worn.costume, worn.color]
            self.ctx.save_settings()
            look = self.step_look()
            self.choosing, self.preview = None, None
            self._commit(side, worn, look)
        elif frame.was_pressed("back"):
            audio.play("menu_back")
            self.choosing, self.preview = None, None

    def _pick(self) -> None:
        if self._hovered() is None:
            self.toast_f = TOAST_F
            audio.play("menu_locked")
            return
        side = self.picking
        self.choosing = side  # for the time of the question: who is asking matters
        wanted = self._wants_outfit(side)
        self.choosing = None
        if wanted:
            audio.play("menu_ok")
            self._open_outfit(side)
            return
        if side == 1 and self.mode == "vs_cpu":
            # The computer dresses itself, here, so the VS screen already shows it.
            self._commit(side, random_outfit(self._hovered(), random.Random()))
            return
        self._commit(side, Loadout())

    def _commit(self, side: int, loadout: Loadout, look: FighterLook | None = None) -> None:
        """The fighter under the cursor is this side's, in this outfit and these poses."""
        audio.play("menu_ok")
        self.ctx.loadouts[side] = loadout
        if look is None and (loadout.costume or loadout.color):
            look = FighterLook(self.roster[self.cursor], loadout)
        if look is not None:
            self.worn[side] = look
        self.flash_f[side] = PICK_FLASH_F
        self.picks.append(self.cursor)  # not None: a fighter is hovered
        if len(self.picks) < self.picks_needed:
            return
        ids = self.fighter_ids
        if self.mode == "arcade":
            from jojo_arena.ui.arcade_scene import ArcadeScene

            self.ctx.scenes.switch(ArcadeScene(self.ctx, ids[0]))
            return
        # Fighters chosen: now the arena, then the VS screen (or straight to training).
        from jojo_arena.ui.stage_scene import StageSelectScene

        self.ctx.scenes.switch(StageSelectScene(self.ctx, self.mode, fighter_ids=(ids[0], ids[1])))

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
            # Right under the grid, so it follows a tab with fewer rows.
            y = GRID_Y + self.rows() * (CELL + GAP) + 5
            font.draw(surface, name, (width // 2, y), shade(part.colors[0], 50), align="center")
        font.draw(surface, text.VS, (width // 2, 172), GOLD, scale=3, align="center")
        for side in (0, 1):
            self._draw_side(surface, side)
        draw_hints(surface, self.hints, (width // 2, height - 14))
        draw_toast(surface, text.SOON_TOAST, self.toast_f, y=210)
        if self.move_list is not None:
            self.move_list.draw(surface)

    def _cell_rect(self, index: int) -> pygame.Rect:
        col, row = index % GRID_COLS, index // GRID_COLS
        # A short last row (complete part) sits in the middle, not against the left.
        shift = (GRID_COLS - self.row_length(row)) * (CELL + GAP) // 2
        x = GRID_X + shift + col * (CELL + GAP)
        return pygame.Rect(x, GRID_Y + row * (CELL + GAP), CELL, CELL)

    def _draw_tabs(self, surface: pygame.Surface) -> None:
        """One tab per part, its emblem inside; parts with nobody yet stay dim."""
        filled = {self.part_of(i) for i in range(len(self.roster))}
        draw_part_tabs(surface, self.parts, self.part_numbers, self.tab, filled, TABS_Y)

    def _draw_grid(self, surface: pygame.Surface) -> None:
        grid = self.grid()
        part = self.parts.get(self.tab)
        for cell in range(self.cells()):
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
            elif part is None or not part.complete:
                # An empty cell of a part still being filled: more are coming.
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
            anim, with_stand, offset = "idle", True, None
            look = self.worn.get(side, self.looks[index]) if side < self.picking else None
            look = look or self.looks[index]
            if side == self.choosing:
                # Dressed as picked; in the pose on a pose line, standing on the others.
                look = self.step_look()
                rows = self.outfit_rows()
                row = rows[min(self.row, len(rows) - 1)] if rows else ""
                if row in ("pose", "stand_pose"):
                    with_stand = row == "stand_pose"
                    pose_id = getattr(self.loadout, row)
                    anim = f"pose_{pose_id}"
                    info = look.sprites.poses.get(pose_id)
                    offset = info.stand_offset if info is not None and with_stand else None
            look.draw(
                surface,
                (feet_x, FEET_Y),
                self.tick,
                scale=2,
                flip=side == 1,
                stand=with_stand,
                anim=anim,
                stand_offset=offset,
            )
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
        if side == self.choosing:
            # The step needs the room: the name in small, then its lines.
            font.draw(surface, fdef.name, (box.x + 5, y), shade(fdef.color, 60))
            self._draw_outfit_lines(surface, box, y + 12)
            return
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

    def _named(self, row: str) -> tuple[str, str]:
        """(the name, the source) of what the step has picked on one of its lines."""
        sprites = self.step_look().sprites
        english = i18n.language() == "en"
        if row == "costume":
            label, label_en, source = sprites.costume
            return (label_en if english else label) or text.COSTUME_NORMAL, source
        if row == "color":
            color = sprites.colors.get(self.loadout.color) or next(
                iter(sprites.colors.values()), None
            )
            if color is None:
                return "", ""
            return color.label_en if english else color.label, color.source
        info = sprites.poses.get(getattr(self.loadout, row))
        if info is None:
            return "", ""
        return info.label_en if english else info.label, info.source

    def _draw_outfit_lines(self, surface: pygame.Surface, box: pygame.Rect, y: int) -> None:
        """One line per choice (COSTUME 2/3, COULEUR 1/4, POSE 1/3...), the active one lit;
        under them the full name of what the active line has picked, between its arrows,
        then where it comes from."""
        rows = self.outfit_rows()
        if not rows:
            return
        titles = {
            "costume": text.COSTUME_ROW,
            "color": text.COLOR_ROW,
            "pose": text.POSE_ROW,
            "stand_pose": text.POSE_STAND_ROW,
        }
        active = rows[min(self.row, len(rows) - 1)]
        for row in rows:
            ids = self.choices(row)
            current = getattr(self.loadout, row)
            at = ids.index(current) + 1 if current in ids else 1
            lit = WHITE if row == active else DIM
            font.draw(surface, titles[row], (box.x + 5, y), lit)
            font.draw(surface, f"{at}/{len(ids)}", (box.right - 5, y), lit, align="right")
            y += 10
        name, source = self._named(active)
        if not name:
            return
        y = draw_wrapped(surface, f"< {name} >", (box.x + 5, y + 1), SIDE_W - 10, GOLD)
        lines = font.wrap(source, SIDE_W - 10)[: max(0, (box.bottom - y) // 10)]
        draw_wrapped(surface, " ".join(lines), (box.x + 5, y), SIDE_W - 10, DIM)
