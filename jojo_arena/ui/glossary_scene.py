"""Glossary: the lore of JoJo, part by part. Terms, characters and Stands, each with its
picture, a description, the family and where the name comes from.

Q/E (or LB/RB) change the part, left/right the section, up/down the entry; confirm
turns the page of a long text.
"""

from __future__ import annotations

import math

import pygame

from jojo_arena.characters import FighterDef, PartDef, load_parts, load_roster
from jojo_arena.characters.glossary import KINDS, Entry, load_glossary
from jojo_arena.context import GameContext
from jojo_arena.engine import font, music
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import SheetSprites, frame_index, shade
from jojo_arena.paths import SPRITES_DIR
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.fight_view import FighterView
from jojo_arena.ui.icons import draw_icon, draw_part_tabs
from jojo_arena.ui.labels import menu_key
from jojo_arena.ui.portraits import FighterLook
from jojo_arena.ui.widgets import DIM, FAINT, GOLD, WHITE, draw_box, draw_hints

TABS_Y = 26
RULES_COLORS = ((200, 160, 72), (106, 90, 160))  # the rules tab: gold on purple
LIST = pygame.Rect(8, 70, 140, 178)
DETAIL = pygame.Rect(154, 70, 318, 178)
VISUAL = pygame.Rect(DETAIL.x + 6, DETAIL.y + 6, 58, 56)
TEXT_TOP = VISUAL.bottom + 7
LINE_H = 10
BODY = (226, 220, 240)


class GlossaryScene(Scene):
    def __init__(self, ctx: GameContext, part: int | None = None) -> None:
        super().__init__()
        music.request("menu")
        self.ctx = ctx
        self.parts: dict[int, PartDef] = {p.number: p for p in load_parts()}
        self.glossary = load_glossary()
        if self.glossary.get(0):
            # Part 0 is not a part: it is how the fight works. Its own tab, up front.
            self.parts[0] = PartDef(
                number=0,
                title=text.GLOSSARY_RULES,
                setting="",
                colors=(RULES_COLORS[0], RULES_COLORS[1]),
                emblem="emblem_rules",
                complete=True,
            )
        self.numbers = sorted(self.parts) or [0]
        self.fighters: dict[str, FighterDef] = {f.id: f for f in load_roster()}
        self._looks: dict[str, FighterLook] = {}
        self._sheets: dict[str, SheetSprites | None] = {}
        if part not in self.numbers:
            # The saga first: the rules tab is there when it is asked for.
            part = next((n for n in self.numbers if n and self.count(n)), self.numbers[0])
        self.part = part
        self.backdrop = MenuBackdrop(part=part)
        self.kind = self._first_kind()
        self.index = 0
        self.page = 0
        self.tick = 0
        self.hints = [
            (f"{menu_key('prev', ctx.inputs)} {menu_key('next', ctx.inputs)}", text.HINT_PART),
            ("←→", text.HINT_CATEGORY),
            (menu_key("confirm", ctx.inputs), text.HINT_SCROLL),
            (menu_key("back", ctx.inputs), text.HINT_BACK),
        ]

    # Queries ----------------------------------------------------------------------------

    def count(self, part: int) -> int:
        return sum(len(entries) for entries in self.glossary.get(part, {}).values())

    def entries(self) -> list[Entry]:
        return self.glossary.get(self.part, {}).get(self.kind, [])

    @property
    def entry(self) -> Entry | None:
        entries = self.entries()
        return entries[self.index] if self.index < len(entries) else None

    def _first_kind(self) -> str:
        sections = self.glossary.get(self.part, {})
        return next((kind for kind in KINDS if sections.get(kind)), KINDS[0])

    # Update -----------------------------------------------------------------------------

    def update(self) -> None:
        self.tick += 1
        frame = self.ctx.read_menu()
        step = frame.presses("next") - frame.presses("prev")
        if step:
            at = self.numbers.index(self.part)
            self.part = self.numbers[(at + step) % len(self.numbers)]
            self.backdrop.part = self.part
            self.kind = self._first_kind()
            self.index = self.page = 0
        side = frame.presses("right") - frame.presses("left")
        if side:
            self.kind = KINDS[(KINDS.index(self.kind) + side) % len(KINDS)]
            self.index = self.page = 0
        down = frame.presses("down") - frame.presses("up")
        if down and self.entries():
            self.index = (self.index + down) % len(self.entries())
            self.page = 0
        if frame.was_pressed("confirm"):
            self.page = (self.page + 1) % max(1, len(self._pages()))
        elif frame.was_pressed("back"):
            from jojo_arena.ui.main_menu import MainMenuScene

            self.ctx.scenes.switch(MainMenuScene(self.ctx, cursor="glossary"))

    # Draw -------------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        font.draw(surface, text.GLOSSARY, (width // 2, 6), GOLD, scale=2, align="center")
        filled = {n for n in self.numbers if self.count(n)}
        draw_part_tabs(surface, self.parts, self.numbers, self.part, filled, TABS_Y)
        part = self.parts.get(self.part)
        if part is not None:
            label = part.title
            if part.number:
                label = f"{text.PART_N.format(n=part.number)} - {label}"
            font.draw(surface, label, (width // 2, 43), shade(part.colors[0], 60), align="center")
        self._draw_sections(surface)
        draw_box(surface, LIST)
        draw_box(surface, DETAIL)
        if not self.entries():
            lines = font.wrap(text.EMPTY_PART, DETAIL.width - 20)
            y = DETAIL.centery - len(lines) * LINE_H // 2
            for line in lines:
                font.draw(surface, line, (DETAIL.centerx, y), FAINT, align="center")
                y += LINE_H
        else:
            self._draw_list(surface)
            self._draw_entry(surface, self.entry)
        draw_hints(surface, self.hints, (width // 2, height - 14))

    def _draw_sections(self, surface: pygame.Surface) -> None:
        labels = {
            "terms": text.TAB_TERMS,
            "characters": text.TAB_CHARACTERS,
            "stands": text.TAB_STANDS,
        }
        sections = self.glossary.get(self.part, {})
        items = [(kind, f"{labels[kind]} ({len(sections.get(kind, []))})") for kind in KINDS]
        gap = 18
        total = sum(font.text_width(label) for _, label in items) + gap * (len(items) - 1)
        x = surface.get_width() // 2 - total // 2
        for kind, label in items:
            current = kind == self.kind
            color = GOLD if current else (DIM if sections.get(kind) else FAINT)
            rect = font.draw(surface, label, (x, 56), color)
            if current:
                surface.fill(GOLD, (rect.x, rect.bottom, rect.width, 1))
            x = rect.right + gap

    def _draw_list(self, surface: pygame.Surface) -> None:
        entries = self.entries()
        rows = (LIST.height - 8) // 12
        first = max(0, min(self.index - rows // 2, len(entries) - rows))
        for row, entry in enumerate(entries[first : first + rows]):
            index = first + row
            y = LIST.y + 5 + row * 12
            if index == self.index:
                bar = pygame.Surface((LIST.width - 6, 11), pygame.SRCALPHA)
                bar.fill((255, 214, 90, 40))
                surface.blit(bar, (LIST.x + 3, y - 2))
                surface.fill(GOLD, (LIST.x + 3, y - 2, 2, 11))
            color = GOLD if index == self.index else WHITE
            font.draw(surface, entry.name, (LIST.x + 8, y), color)

    def _pages(self) -> list[list[tuple[str, tuple[int, int, int]]]]:
        """The entry's text cut in lines, then in pages that fit under the picture. A
        section (family, name) starts on the next page when less than its heading and
        three lines would fit; cut in two, it shows its heading again."""
        entry = self.entry
        if entry is None:
            return [[]]
        width = DETAIL.width - 12
        per_page = (DETAIL.bottom - 4 - TEXT_TOP) // LINE_H
        sections = [(None, entry.text, BODY)]
        sections += [(text.GLOSSARY_FAMILY, entry.family, DIM)]
        sections += [(text.GLOSSARY_NAME, entry.name_origin, DIM)]
        pages: list[list[tuple[str, tuple[int, int, int]]]] = []
        page: list[tuple[str, tuple[int, int, int]]] = []
        for heading, body, color in sections:
            if not body:
                continue
            title = [(heading, GOLD)] if heading else []
            block = title + [(line, color) for line in font.wrap(body, width)]
            room = per_page - len(page) - 1
            if page and len(block) > room and room < min(len(block), 4):
                pages.append(page)  # not even the heading and three lines fit here
                page = []
            if page:
                page.append(("", BODY))
            while len(page) + len(block) > per_page:
                cut = per_page - len(page)
                pages.append(page + block[:cut])
                page, block = [], title + block[cut:]
            page += block
        pages.append(page)
        return pages

    def _draw_entry(self, surface: pygame.Surface, entry: Entry | None) -> None:
        if entry is None:
            return
        surface.fill((10, 8, 22), VISUAL)
        pygame.draw.rect(surface, (60, 52, 84), VISUAL, 1)
        self._draw_visual(surface, entry)
        x = VISUAL.right + 7
        room = DETAIL.right - 6 - x
        scale = 2 if font.text_width(entry.name, 2) <= room else 1
        font.draw(surface, entry.name, (x, VISUAL.y + 2), GOLD, scale=scale)
        y = VISUAL.y + 4 + 10 * scale
        if entry.subtitle:
            template = {
                "stand": text.GLOSSARY_STAND,
                "power": text.GLOSSARY_POWER,
            }.get(entry.subtitle_kind, text.GLOSSARY_USER)
            font.draw(surface, template.format(name=entry.subtitle), (x, y), WHITE)
            y += 12
        grades = entry.stat_grades()
        if len(grades) == 6:
            font.draw(surface, text.GLOSSARY_STATS.format(**grades), (x, y), DIM)
            font.draw(surface, text.GLOSSARY_STATS2.format(**grades), (x, y + 10), DIM)
        pages = self._pages()
        page = min(self.page, len(pages) - 1)
        y = TEXT_TOP
        for line, color in pages[page]:
            font.draw(surface, line, (DETAIL.x + 6, y), color)
            y += LINE_H
        if len(pages) > 1:
            marker = f"{page + 1}/{len(pages)}"
            font.draw(surface, marker, (DETAIL.right - 6, DETAIL.bottom - 11), FAINT, align="right")

    def _draw_visual(self, surface: pygame.Surface, entry: Entry) -> None:
        feet = (VISUAL.centerx, VISUAL.bottom - 5)
        surface.set_clip(VISUAL.inflate(-2, -2))
        try:
            if entry.kind == "terms":
                bob = round(math.sin(self.tick * 0.06) * 1.5)
                center = (VISUAL.centerx, VISUAL.centery + bob)
                draw_icon(surface, entry.icon, center, scale=3, size=16, center=True)
            elif entry.kind == "characters" and entry.fighter in self.fighters:
                look = self._look(entry.fighter)
                look.draw(surface, feet, self.tick, scale=1, stand=False, direction="down")
            elif entry.kind == "stands":
                sheet = self._sheet(entry.sprite)
                if sheet is not None:
                    name, spec = FighterView.resolve(sheet, "idle")
                    image = sheet.frame(name, "down", False, frame_index(spec, self.tick))
                    ax, ay = sheet.anchor
                    surface.blit(image, (feet[0] - ax, feet[1] - ay))
                else:
                    draw_icon(surface, "", VISUAL.center, scale=3, size=16, center=True)
        finally:
            surface.set_clip(None)

    def _look(self, fighter_id: str) -> FighterLook:
        if fighter_id not in self._looks:
            self._looks[fighter_id] = FighterLook(self.fighters[fighter_id])
        return self._looks[fighter_id]

    def _sheet(self, sprite: str) -> SheetSprites | None:
        if sprite not in self._sheets:
            base = SPRITES_DIR / sprite
            self._sheets[sprite] = (
                SheetSprites.load(base.with_suffix(".png"), base.with_suffix(".toml"))
                if sprite
                else None
            )
        return self._sheets[sprite]
