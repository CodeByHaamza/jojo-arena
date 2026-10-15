"""Cairo night street: floor, frame and props generated in code (no image files needed)."""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.stages.base import StageDef

OUTLINE = (23, 18, 31)
WOOD_LIGHT = (128, 94, 66)
WOOD = (104, 74, 52)
WOOD_DARK = (78, 54, 40)
AWNING_COLORS = [
    ((138, 62, 60), (186, 166, 136)),
    ((60, 92, 128), (186, 166, 136)),
    ((70, 112, 76), (186, 166, 136)),
    ((150, 110, 50), (90, 52, 70)),
]
GOODS = [(196, 120, 52), (150, 168, 64), (204, 176, 72), (170, 70, 64)]
HOLE = (255, 0, 255)


def _jitter(color: tuple[int, int, int], rng: random.Random, amount: int):
    return tuple(max(0, min(255, c + rng.randint(-amount, amount))) for c in color)


class CairoNightRenderer:
    def __init__(self, stage: StageDef, size: tuple[int, int] = (480, 270)) -> None:
        self.stage = stage
        self.palette = {key: tuple(value) for key, value in stage.palette.items()}
        self.size = size
        self.background = self._build_background()

    # Static layers --------------------------------------------------------------------

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface(self.size)
        self._draw_cobbles(surface)
        self._draw_markings(surface)
        surface.blit(self._build_frame(), (0, 0))
        self._draw_curb(surface)
        for lamp in self.stage.lanterns:
            self._draw_lantern(surface, lamp.as_ints())
        return surface

    def _draw_lantern(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        x, y = pos
        surface.fill(OUTLINE, (x - 3, y - 4, 7, 8))
        surface.fill(self.palette["lantern"], (x - 2, y - 3, 5, 6))
        surface.fill((255, 236, 190), (x - 1, y - 2, 2, 2))

    def _draw_cobbles(self, surface: pygame.Surface) -> None:
        pal = self.palette
        rng = random.Random(1987)
        surface.fill(pal["mortar"])
        bounds = self.stage.bounds.rect
        row_h = 7
        top, bottom = int(bounds.top) - row_h, int(bounds.bottom) + row_h
        for row, y in enumerate(range(top, bottom, row_h)):
            x = int(bounds.left) - (row % 2) * 6 - 4
            while x < bounds.right + 4:
                width = rng.randint(8, 12)
                base = rng.choices(
                    [pal["stone"], pal["stone_light"], pal["stone_dark"]], [5, 2, 2]
                )[0]
                color = _jitter(base, rng, 2)
                stone = pygame.Rect(x + 1, y + 1, width - 1, row_h - 1)
                surface.fill(color, stone)
                light = tuple(min(255, c + 6) for c in color)
                dark = tuple(max(0, c - 7) for c in color)
                surface.fill(light, (stone.x, stone.y, stone.w - 1, 1))
                surface.fill(dark, (stone.x + 1, stone.bottom - 1, stone.w - 1, 1))
                x += width

    def _draw_markings(self, surface: pygame.Surface) -> None:
        """Faint, worn court lines: center line and circle."""
        color = self.palette["marking"]
        rng = random.Random(7)
        bounds = self.stage.bounds.rect
        center = bounds.center
        marks = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.circle(marks, (*color, 255), center.as_ints(), 30, 1)
        pygame.draw.line(
            marks, (*color, 255), (center.x, bounds.top + 6), (center.x, bounds.bottom - 6)
        )
        # Wear: knock out random pixels so the paint looks old.
        for y in range(int(bounds.top), int(bounds.bottom)):
            for x in range(int(center.x) - 31, int(center.x) + 32):
                if marks.get_at((x, y)).a and rng.random() < 0.3:
                    marks.set_at((x, y), (0, 0, 0, 0))
        surface.blit(marks, (0, 0))

    def _build_frame(self) -> pygame.Surface:
        pal = self.palette
        rng = random.Random(42)
        frame = pygame.Surface(self.size)
        frame.fill(pal["frame"])
        # Rooftop silhouettes along the top and bottom edges.
        for band_top, band_bottom in ((0, 40), (252, 270)):
            x = 0
            while x < self.size[0]:
                width = rng.randint(24, 56)
                height = rng.randint(10, band_bottom - band_top)
                y = band_top + (band_bottom - band_top - height)
                frame.fill(pal["frame_dark"], (x, y, width - 2, height))
                for wx in range(x + 4, x + width - 6, 7):
                    for wy in range(y + 3, band_bottom - 3, 6):
                        if rng.random() < 0.18:
                            frame.fill(pal["window"], (wx, wy, 2, 3))
                x += width
        frame.set_colorkey(HOLE)
        bounds = self.stage.bounds
        pygame.draw.rect(frame, HOLE, _to_pygame(bounds.rect), border_radius=int(bounds.radius))
        return frame

    def _draw_curb(self, surface: pygame.Surface) -> None:
        bounds = self.stage.bounds
        radius = int(bounds.radius)
        rect = _to_pygame(bounds.rect)
        pygame.draw.rect(surface, OUTLINE, rect.inflate(10, 10), 1, border_radius=radius + 5)
        pygame.draw.rect(
            surface, self.palette["curb"], rect.inflate(8, 8), 4, border_radius=radius + 4
        )
        pygame.draw.rect(surface, OUTLINE, rect.inflate(2, 2), 1, border_radius=radius + 1)

    # Per-frame drawing ----------------------------------------------------------------

    def draw_background(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (0, 0))

    def draw_lights(self, surface: pygame.Surface, tick: int) -> None:
        """Warm lantern light, added on top of the whole scene."""
        lantern = self.palette["lantern"]
        for i, lamp in enumerate(self.stage.lanterns):
            # Slow, deterministic flicker, out of phase between lanterns.
            flicker = 0.30 + 0.04 * math.sin(tick * 0.11 + i * 1.7)
            color = tuple(round(c * flicker) for c in lantern)
            blit_glow(surface, radial_glow(40, color), lamp.as_ints())

    def draw_floor_details(self, surface: pygame.Surface, arena: Arena) -> None:
        """Debris of broken props, drawn flat on the floor under everything else."""
        for obstacle in arena.obstacles:
            if obstacle.broken:
                self._draw_debris(surface, obstacle)

    def draw_obstacle(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        if obstacle.broken:
            return
        shake = (1 if obstacle.flash % 2 else -1) if obstacle.flash else 0
        rect = _to_pygame(obstacle.rect).move(shake, 0)
        index = self.stage_index(obstacle)
        if obstacle.kind == "stall":
            self._draw_stall(surface, rect, index, obstacle.hp < obstacle.max_hp / 2)
        else:
            self._draw_crate(surface, rect, obstacle.hp < obstacle.max_hp / 2)

    def stage_index(self, obstacle: Obstacle) -> int:
        return int(obstacle.rect.x * 7 + obstacle.rect.y * 13)

    def _draw_stall(self, surface, rect: pygame.Rect, index: int, damaged: bool) -> None:
        rng = random.Random(index)
        stripe_a, stripe_b = AWNING_COLORS[index % len(AWNING_COLORS)]
        # Shadow on the floor, then the counter (front face + top), then the awning.
        shadow = pygame.Surface((rect.w + 6, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surface.blit(shadow, (rect.x - 3, rect.bottom - 4))
        front = pygame.Rect(rect.x, rect.bottom - 8, rect.w, 8)
        top = pygame.Rect(rect.x, rect.y - 4, rect.w, rect.h - 4)
        surface.fill(WOOD_DARK, front)
        for x in range(front.x + 5, front.right - 2, 6):
            surface.fill(WOOD, (x, front.y + 1, 1, front.h - 2))
        surface.fill(WOOD_LIGHT, top)
        surface.fill(tuple(c + 14 for c in WOOD_LIGHT), (top.x + 1, top.y + 1, top.w - 2, 1))
        for _ in range(9):  # goods on the counter
            gx = rng.randint(top.x + 3, top.right - 5)
            gy = rng.randint(top.y + 4, top.bottom - 3)
            surface.fill(rng.choice(GOODS), (gx, gy, 3, 2))
        pygame.draw.rect(surface, OUTLINE, top.union(front), 1)
        # Poles and awning.
        awning = pygame.Rect(rect.x - 3, rect.y - 16, rect.w + 6, 11)
        for px in (awning.x + 2, awning.right - 4):
            surface.fill(OUTLINE, (px, awning.bottom, 2, top.y - awning.bottom + 3))
        for i, x in enumerate(range(awning.x, awning.right, 5)):
            color = stripe_a if i % 2 == 0 else stripe_b
            width = min(5, awning.right - x)
            surface.fill(color, (x, awning.y, width, awning.h))
            surface.fill(color, (x + 1, awning.bottom, max(0, width - 2), 2))  # scallops
        surface.fill(
            tuple(min(255, c + 24) for c in stripe_b), (awning.x + 1, awning.y + 1, awning.w - 2, 1)
        )
        pygame.draw.rect(surface, OUTLINE, awning, 1)
        if damaged:
            tear = pygame.Rect(awning.x + awning.w // 3, awning.y + 3, 6, 4)
            surface.fill(OUTLINE, tear)
            surface.fill(OUTLINE, (top.x + top.w // 2, top.y + 2, 1, top.h - 2))

    def _draw_crate(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        shadow = pygame.Surface((rect.w + 4, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surface.blit(shadow, (rect.x - 2, rect.bottom - 3))
        top = pygame.Rect(rect.x, rect.y - 5, rect.w, 6)
        front = pygame.Rect(rect.x, rect.y + 1, rect.w, rect.h - 1)
        surface.fill(WOOD_LIGHT, top)
        surface.fill(WOOD, front)
        pygame.draw.line(surface, WOOD_DARK, front.topleft, (front.right - 1, front.bottom - 1))
        pygame.draw.line(
            surface, WOOD_DARK, (front.x, front.bottom - 1), (front.right - 1, front.y)
        )
        pygame.draw.rect(surface, OUTLINE, top.union(front), 1)
        if damaged:
            surface.fill(OUTLINE, (front.x + 3, front.y + 2, 1, 4))

    def _draw_debris(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        rng = random.Random(self.stage_index(obstacle))
        rect = _to_pygame(obstacle.rect)
        count = 12 if obstacle.kind == "stall" else 5
        for _ in range(count):
            x = rng.randint(rect.x - 6, rect.right + 4)
            y = rng.randint(rect.y - 2, rect.bottom + 3)
            if rng.random() < 0.5:
                w, h = rng.randint(4, 8), 2
            else:
                w, h = 2, rng.randint(3, 6)
            surface.fill(OUTLINE, (x - 1, y - 1, w + 2, h + 2))
            surface.fill(rng.choice([WOOD, WOOD_LIGHT, WOOD_DARK]), (x, y, w, h))
        if obstacle.kind == "stall":
            stripe_a, _ = AWNING_COLORS[self.stage_index(obstacle) % len(AWNING_COLORS)]
            cloth = pygame.Rect(rect.x + rect.w // 4, rect.y + 2, rect.w // 2, 6)
            surface.fill(OUTLINE, cloth.inflate(2, 2))
            surface.fill(stripe_a, cloth)


def _to_pygame(rect) -> pygame.Rect:
    return pygame.Rect(round(rect.x), round(rect.y), round(rect.w), round(rect.h))
