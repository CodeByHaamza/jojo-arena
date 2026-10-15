"""A vertical menu driven by InputFrames: up/down to move, left/right to change, confirm."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from jojo_arena.engine import font
from jojo_arena.engine.actions import InputFrame

WHITE = (255, 255, 255)
DIM = (150, 144, 170)
ENABLED = (204, 198, 222)
HIGHLIGHT = (255, 214, 90)
DISABLED = (92, 86, 112)
TAG_FILL = (58, 44, 92)
TAG_TEXT = (196, 176, 255)


@dataclass
class MenuItem:
    key: str
    label: str
    values: list[str] = field(default_factory=list)  # empty = a plain button
    index: int = 0
    enabled: bool = True  # a disabled item can be highlighted but not used
    tag: str = ""  # small label beside the item, e.g. "SOON"

    @property
    def value(self) -> str | None:
        return self.values[self.index] if self.values else None


class Menu:
    def __init__(self, items: list[MenuItem]) -> None:
        self.items = items
        self.cursor = 0
        self.tick = 0

    @property
    def selected(self) -> MenuItem:
        return self.items[self.cursor]

    def item(self, key: str) -> MenuItem:
        return next(i for i in self.items if i.key == key)

    def select(self, key: str) -> None:
        self.cursor = next(n for n, i in enumerate(self.items) if i.key == key)

    def handle(self, frame: InputFrame) -> tuple[str, str] | None:
        """Returns ("confirm", key), ("change", key), ("locked", key), ("back", "") or None."""
        self.tick += 1
        if frame.was_pressed("up"):
            self.cursor = (self.cursor - 1) % len(self.items)
        if frame.was_pressed("down"):
            self.cursor = (self.cursor + 1) % len(self.items)
        item = self.selected
        if item.values and item.enabled:
            step = int(frame.was_pressed("right")) - int(frame.was_pressed("left"))
            if step:
                item.index = (item.index + step) % len(item.values)
                return "change", item.key
        if frame.was_pressed("confirm"):
            if not item.enabled:
                return "locked", item.key
            if item.values:
                item.index = (item.index + 1) % len(item.values)
                return "change", item.key
            return "confirm", item.key
        if frame.was_pressed("back"):
            return "back", ""
        return None

    def draw(
        self,
        surface: pygame.Surface,
        x: int,
        top: int,
        spacing: int = 14,
        align: str = "center",
    ) -> None:
        """Draw the items; `x` is their center, or their left edge with align="left"."""
        for i, item in enumerate(self.items):
            selected = i == self.cursor
            if not item.enabled:
                color = DIM if selected else DISABLED
            else:
                color = HIGHLIGHT if selected else ENABLED
            text = item.label if not item.values else f"{item.label} : < {item.value} >"
            y = top + i * spacing
            if selected and align == "left":
                # A soft bar behind the highlighted line.
                bar = pygame.Surface((180, spacing - 2), pygame.SRCALPHA)
                bar.fill((255, 214, 90, 34))
                surface.blit(bar, (x - 6, y - 3))
                surface.fill(HIGHLIGHT, (x - 6, y - 3, 2, spacing - 2))
            rect = font.draw(surface, text, (x, y), color, align=align)
            if item.tag:
                tag_x = rect.right + 6
                width = font.text_width(item.tag) + 6
                pygame.draw.rect(surface, TAG_FILL, (tag_x, y - 1, width, 11))
                font.draw(surface, item.tag, (tag_x + 3, y), TAG_TEXT, outline=None)
            if selected and align == "center" and (self.tick // 15) % 2 == 0:
                font.draw(surface, ">", (rect.x - 8, rect.y), HIGHLIGHT)
