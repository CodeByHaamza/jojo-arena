"""Title screen: the logo, the nine parts' emblems, and the cast of one part at a time
over the colors of that part - the two camps facing each other across the middle, the
way that part's fight actually went."""

from __future__ import annotations

import pygame

from jojo_arena import __version__
from jojo_arena.characters import PartDef, load_parts, load_roster
from jojo_arena.context import GameContext
from jojo_arena.engine import font, music
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import shade
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.icons import draw_icon
from jojo_arena.ui.labels import menu_key
from jojo_arena.ui.portraits import FighterLook
from jojo_arena.ui.widgets import DIM, GOLD, WHITE

LINEUP_Y = 232
LINEUP_SPACING = 46
MIDDLE_GAP = 30  # px either side of the center: the ground between the two camps
GROUP_F = 300  # each part's cast stays on screen this long
SLIDE_F = 16
EMBLEMS_Y = 93
EMBLEM_STEP = 24


class TitleScene(Scene):
    def __init__(self, ctx: GameContext) -> None:
        super().__init__()
        music.request("menu")
        self.ctx = ctx
        self.parts: dict[int, PartDef] = {p.number: p for p in load_parts()}
        fighters = [f for f in load_roster() if f.selectable]
        # The cast of each part that has fighters, in part order.
        self.groups: list[tuple[int, list[FighterLook]]] = []
        for number in sorted({f.part for f in fighters}):
            self.groups.append((number, [FighterLook(f) for f in fighters if f.part == number]))
        self.backdrop = MenuBackdrop(part=self.groups[0][0] if self.groups else None)
        self.tick = 0

    @property
    def group(self) -> tuple[int, list[FighterLook]]:
        return self.groups[(self.tick // GROUP_F) % len(self.groups)] if self.groups else (0, [])

    def update(self) -> None:
        self.tick += 1
        self.backdrop.part = self.group[0] or None
        frame = self.ctx.read_menu()
        if frame.was_pressed("confirm"):
            from jojo_arena.ui.main_menu import MainMenuScene

            self.ctx.scenes.switch(MainMenuScene(self.ctx))
        elif frame.was_pressed("back"):
            self.ctx.scenes.quit()

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width = surface.get_width()
        number, looks = self.group
        self._draw_lineup(surface, looks)
        font.draw(surface, text.TITLE, (width // 2, 20), GOLD, scale=5, align="center")
        font.draw(surface, text.DISCLAIMER, (width // 2, 69), DIM, align="center")
        if (self.tick // 30) % 2 == 0:
            start = text.PRESS_START.format(key=menu_key("confirm", self.ctx.inputs))
            font.draw(surface, start, (width // 2, 110), WHITE, align="center")
        self._draw_emblems(surface, number)
        part = self.parts.get(number)
        if part is not None:
            label = f"{text.PART_N.format(n=number)} - {part.title}"
            font.draw(surface, label, (width // 2, 244), shade(part.colors[0], 60), align="center")
            font.draw(surface, part.setting, (width // 2, 255), DIM, align="center")
        font.draw(surface, f"V{__version__}", (width - 6, 258), DIM, align="right")

    def _draw_lineup(self, surface: pygame.Surface, looks: list[FighterLook]) -> None:
        """The two camps, facing each other: whoever stood against the Joestars on the
        right, everyone who stood with them on the left - Stroheim included, because in
        Part 2 that is where he stood."""
        if not looks:
            return
        width = surface.get_width()
        center = width // 2
        slide = max(0, SLIDE_F - self.tick % GROUP_F) * 12
        camps = (
            [look for look in looks if look.fdef.side != "villain"],
            [look for look in looks if look.fdef.side == "villain"],
        )
        for camp, (way, group) in enumerate(zip((-1, 1), camps, strict=True)):
            room = center - MIDDLE_GAP - 22
            spacing = min(LINEUP_SPACING, room // max(1, len(group) - 1 or 1))
            for i, look in enumerate(group):
                # The nearest to the middle is the one the part was about.
                x = center + way * (MIDDLE_GAP + i * spacing) + slide * (1 if camp else -1)
                look.draw(surface, (x, LINEUP_Y), self.tick + i * 7, flip=x > center)
        if all(camps):
            self._draw_versus(surface, center)

    def _draw_versus(self, surface: pygame.Surface, center: int) -> None:
        """What is between the two camps: a word, and the spark of the two meeting."""
        beat = (self.tick // 4) % 2
        font.draw(surface, text.VS, (center, LINEUP_Y - 28), GOLD, scale=2, align="center")
        for i in range(3):
            y = LINEUP_Y - 10 + i * 7
            length = 3 + (i + beat) % 3
            surface.fill(shade(GOLD, -20), (center - length, y, length * 2, 1))

    def _draw_emblems(self, surface: pygame.Surface, current: int) -> None:
        """The nine parts in a row: the one on screen lit, those still to come dim."""
        numbers = sorted(self.parts)
        if not numbers:
            return
        ready = {n for n, _ in self.groups}
        x = surface.get_width() // 2 - (len(numbers) - 1) * EMBLEM_STEP // 2
        for number in numbers:
            part = self.parts[number]
            lit = number == current
            if lit:
                pygame.draw.circle(surface, shade(part.colors[0], -30), (x, EMBLEMS_Y), 12)
                pygame.draw.circle(surface, shade(part.colors[0], 60), (x, EMBLEMS_Y), 12, 1)
            alpha = 255 if lit or number in ready else 110
            draw_icon(surface, part.emblem, (x, EMBLEMS_Y), scale=2, center=True, alpha=alpha)
            x += EMBLEM_STEP
