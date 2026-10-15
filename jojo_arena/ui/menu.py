"""A vertical menu driven by InputFrames: up/down to move, left/right to change, confirm."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from jojo_arena.engine import font
from jojo_arena.engine.actions import InputFrame

WHITE = (255, 255, 255)
DIM = (150, 144, 170)
HIGHLIGHT = (255, 214, 90)


@dataclass
class MenuItem:
    key: str
    label: str
    values: list[str] = field(default_factory=list)  # empty = a plain button
    index: int = 0

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

    def handle(self, frame: InputFrame) -> tuple[str, str] | None:
        """Returns ("confirm", key), ("change", key), ("back", "") or None."""
        self.tick += 1
        if frame.was_pressed("up"):
            self.cursor = (self.cursor - 1) % len(self.items)
        if frame.was_pressed("down"):
            self.cursor = (self.cursor + 1) % len(self.items)
        item = self.selected
        if item.values:
            step = int(frame.was_pressed("right")) - int(frame.was_pressed("left"))
            if step:
                item.index = (item.index + step) % len(item.values)
                return "change", item.key
        if frame.was_pressed("confirm"):
            if item.values:
                item.index = (item.index + 1) % len(item.values)
                return "change", item.key
            return "confirm", item.key
        if frame.was_pressed("back"):
            return "back", ""
        return None

    def draw(self, surface: pygame.Surface, center_x: int, top: int, spacing: int = 14) -> None:
        for i, item in enumerate(self.items):
            selected = i == self.cursor
            color = HIGHLIGHT if selected else DIM
            text = item.label if not item.values else f"{item.label} : < {item.value} >"
            rect = font.draw(surface, text, (center_x, top + i * spacing), color, align="center")
            if selected and (self.tick // 15) % 2 == 0:
                font.draw(surface, ">", (rect.x - 8, rect.y), HIGHLIGHT)
