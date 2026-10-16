"""The Joestar mansion in flames: parquet, carpet, burning walls, and dawn through the
windows, all generated in code (no image files needed)."""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.stages.base import StageDef
from jojo_arena.stages.cairo_night import HOLE, OUTLINE, _jitter, _to_pygame

STONE = (150, 140, 136)
STONE_LIGHT = (180, 170, 164)
STONE_DARK = (110, 102, 100)
PORCELAIN = (224, 228, 236)
PORCELAIN_BLUE = (70, 100, 170)
WOOD = (110, 66, 40)
WOOD_LIGHT = (140, 90, 56)
WOOD_DARK = (80, 46, 30)
VELVET = (120, 30, 46)
WINDOW_W, WINDOW_H = 22, 30


class JoestarMansionRenderer:
    def __init__(self, stage: StageDef, size: tuple[int, int] = (480, 270)) -> None:
        self.stage = stage
        self.palette = {key: tuple(value) for key, value in stage.palette.items()}
        self.size = size
        self.tick_hint = 0
        self.background = self._build_background()

    # Static layers --------------------------------------------------------------------

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface(self.size)
        self._draw_parquet(surface)
        self._draw_carpet(surface)
        surface.blit(self._build_frame(), (0, 0))
        self._draw_curb(surface)
        for lamp in self.stage.lanterns:
            self._draw_candelabra(surface, lamp.as_ints())
        return surface

    def _draw_parquet(self, surface: pygame.Surface) -> None:
        pal = self.palette
        rng = random.Random(1888)
        surface.fill(pal["seam"])
        bounds = self.stage.bounds.rect
        row_h = 6
        for y in range(int(bounds.top) - row_h, int(bounds.bottom) + row_h, row_h):
            x = int(bounds.left) - rng.randint(0, 30)
            while x < bounds.right + 4:
                length = rng.randint(22, 42)
                base = rng.choices([pal["plank"], pal["plank_light"], pal["plank_dark"]], [5, 2, 2])
                color = _jitter(base[0], rng, 2)
                board = pygame.Rect(x + 1, y + 1, length - 1, row_h - 1)
                surface.fill(color, board)
                surface.fill(tuple(min(255, c + 5) for c in color), (board.x, board.y, board.w, 1))
                if rng.random() < 0.3:  # a knot in the wood
                    surface.fill(
                        tuple(max(0, c - 10) for c in color), (board.x + 6, board.y + 2, 2, 1)
                    )
                x += length

    def _draw_carpet(self, surface: pygame.Surface) -> None:
        """A long, worn red carpet down the hall, with a dull gold border."""
        pal = self.palette
        rng = random.Random(4)
        bounds = self.stage.bounds.rect
        carpet = pygame.Rect(0, 0, 210, 120)
        carpet.center = (round(bounds.center.x), round(bounds.center.y) + 4)
        surface.fill(pal["carpet_border"], carpet)
        inner = carpet.inflate(-6, -6)
        surface.fill(pal["carpet"], inner)
        pattern = tuple(min(255, c + 12) for c in pal["carpet"])
        for x in range(inner.x + 8, inner.right - 4, 16):
            for y in range(inner.y + 8, inner.bottom - 4, 16):
                pygame.draw.polygon(
                    surface, pattern, [(x, y - 3), (x + 3, y), (x, y + 3), (x - 3, y)], 1
                )
        # Wear: knock out random pixels so it looks trodden.
        for _ in range(260):
            px, py = (
                rng.randint(carpet.x, carpet.right - 1),
                rng.randint(carpet.y, carpet.bottom - 1),
            )
            color = surface.get_at((px, py))
            surface.set_at((px, py), tuple(max(0, c - 14) for c in color[:3]))

    def window_rects(self) -> list[pygame.Rect]:
        """The tall windows of the north wall, one above each patch of sunlight."""
        rects = []
        for sun in self.stage.sun_windows:
            rect = pygame.Rect(0, 0, WINDOW_W, WINDOW_H)
            rect.midbottom = (round(sun.x + sun.w / 2), 37)
            rects.append(rect)
        return rects

    def _build_frame(self) -> pygame.Surface:
        pal = self.palette
        frame = pygame.Surface(self.size)
        frame.fill(pal["frame"])
        width, height = self.size
        # The north wall: panelled, with its tall windows.
        frame.fill(pal["wall"], (0, 0, width, 38))
        for x in range(0, width, 24):
            frame.fill(pal["wall_light"], (x + 2, 4, 20, 26))
            frame.fill(pal["wall"], (x + 4, 6, 16, 22))
        frame.fill(pal["trim"], (0, 34, width, 4))
        for rect in self.window_rects():
            self._draw_window(frame, rect, pal["glass_night"])
        # Side walls and the south wall, darker, the fire's work.
        frame.fill(pal["frame_dark"], (0, 252, width, 18))
        frame.set_colorkey(HOLE)
        bounds = self.stage.bounds
        pygame.draw.rect(frame, HOLE, _to_pygame(bounds.rect), border_radius=int(bounds.radius))
        return frame

    def _draw_window(self, surface: pygame.Surface, rect: pygame.Rect, glass) -> None:
        surface.fill(OUTLINE, rect.inflate(4, 2))
        surface.fill(self.palette["trim"], rect.inflate(2, 0))
        pane = rect.inflate(-2, -2)
        surface.fill(glass, pane)
        pygame.draw.ellipse(surface, glass, (pane.x, pane.y - 6, pane.w, 12))
        pygame.draw.line(
            surface,
            self.palette["trim"],
            (pane.centerx, pane.y - 4),
            (pane.centerx, pane.bottom),
            1,
        )
        pygame.draw.line(
            surface, self.palette["trim"], (pane.x, pane.centery), (pane.right, pane.centery), 1
        )

    def _draw_curb(self, surface: pygame.Surface) -> None:
        bounds = self.stage.bounds
        radius = int(bounds.radius)
        rect = _to_pygame(bounds.rect)
        pygame.draw.rect(surface, OUTLINE, rect.inflate(10, 10), 1, border_radius=radius + 5)
        pygame.draw.rect(
            surface, self.palette["curb"], rect.inflate(8, 8), 4, border_radius=radius + 4
        )
        pygame.draw.rect(surface, OUTLINE, rect.inflate(2, 2), 1, border_radius=radius + 1)

    def _draw_candelabra(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        x, y = pos
        surface.fill(OUTLINE, (x - 4, y - 2, 9, 5))
        surface.fill((190, 150, 70), (x - 3, y - 1, 7, 3))
        for dx in (-3, 0, 3):
            surface.fill((240, 232, 210), (x + dx, y - 4, 1, 3))
            surface.set_at((x + dx, y - 5), self.palette["lantern"])

    # Per-frame drawing ----------------------------------------------------------------

    def draw_background(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (0, 0))

    def draw_sun(self, surface: pygame.Surface, arena: Arena, amount: float) -> None:
        """Dawn: the windows glow, then sunlight lies on the floor below them."""
        if amount <= 0:
            return
        pal = self.palette
        glass = tuple(
            round(n + (d - n) * min(1.0, amount))
            for n, d in zip(pal["glass_night"], pal["glass_dawn"], strict=True)
        )
        for rect in self.window_rects():
            self._draw_window(surface, rect, glass)
        light = pygame.Surface(self.size)  # added on top: black adds nothing
        sun = pal["sun"]

        def glow(strength: float):
            return tuple(round(c * strength) for c in sun)

        for window in arena.sun_windows:
            rect = _to_pygame(window)
            for i in range(rect.h):
                # Brighter near the window, fading down the floor, soft at the edges.
                strength = 0.32 * amount * (1 - 0.5 * i / rect.h)
                light.fill(glow(strength * 0.5), (rect.x, rect.y + i, rect.w, 1))
                light.fill(glow(strength), (rect.x + 3, rect.y + i, rect.w - 6, 1))
            # Dust motes drifting in the light.
            rng = random.Random(rect.x)
            for k in range(6):
                drift = (self.tick_hint * 0.3 + k * 17) % rect.h
                x = rect.x + 4 + rng.randrange(rect.w - 8)
                light.fill(glow(0.45 * amount), (x, rect.y + round(drift), 1, 1))
        surface.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def draw_lights(self, surface: pygame.Surface, tick: int) -> None:
        """Candlelight on the walls, and the fire licking along the south wall."""
        self.tick_hint = tick  # the dust in the sunlight drifts with time
        lantern = self.palette["lantern"]
        for i, lamp in enumerate(self.stage.lanterns):
            flicker = 0.28 + 0.05 * math.sin(tick * 0.17 + i * 2.1)
            blit_glow(
                surface, radial_glow(36, tuple(round(c * flicker) for c in lantern)), lamp.as_ints()
            )
        fire = self.palette["fire"]
        width = self.size[0]
        for i, x in enumerate(range(10, width, 34)):
            flicker = (
                0.35 + 0.15 * math.sin(tick * 0.23 + i * 1.3) + 0.08 * math.sin(tick * 0.61 + i)
            )
            blit_glow(surface, radial_glow(26, tuple(round(c * flicker) for c in fire)), (x, 262))
            height = 6 + round(4 * (0.5 + 0.5 * math.sin(tick * 0.3 + i * 2.0)))
            pygame.draw.polygon(
                surface, (255, 170, 60), [(x - 4, 270), (x, 270 - height), (x + 4, 270)]
            )
            pygame.draw.polygon(
                surface, (255, 236, 150), [(x - 2, 270), (x, 270 - height // 2), (x + 2, 270)]
            )

    def draw_floor_details(self, surface: pygame.Surface, arena: Arena) -> None:
        for obstacle in arena.obstacles:
            if obstacle.broken:
                self._draw_debris(surface, obstacle)

    def stage_index(self, obstacle: Obstacle) -> int:
        return int(obstacle.rect.x * 7 + obstacle.rect.y * 13)

    def draw_obstacle(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        if obstacle.broken:
            return
        shake = (1 if obstacle.flash % 2 else -1) if obstacle.flash else 0
        rect = _to_pygame(obstacle.rect).move(shake, 0)
        damaged = obstacle.hp < obstacle.max_hp / 2
        if obstacle.kind == "pillar":
            self._draw_pillar(surface, rect, damaged)
        elif obstacle.kind == "vase":
            self._draw_vase(surface, rect, damaged)
        else:
            self._draw_chair(surface, rect, damaged)

    def _shadow(self, surface, rect: pygame.Rect, grow: int = 4) -> None:
        shadow = pygame.Surface((rect.w + grow, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surface.blit(shadow, (rect.x - grow // 2, rect.bottom - 3))

    def _draw_pillar(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        """A marble column seen from above and a little in front: shaft, capital."""
        self._shadow(surface, rect, 6)
        shaft = pygame.Rect(rect.x + 2, rect.y - 14, rect.w - 4, rect.h + 12)
        surface.fill(OUTLINE, shaft.inflate(2, 2))
        surface.fill(STONE, shaft)
        for x in range(shaft.x + 2, shaft.right - 1, 3):
            surface.fill(STONE_DARK, (x, shaft.y + 3, 1, shaft.h - 4))
        capital = pygame.Rect(rect.x, rect.y - 18, rect.w, 5)
        surface.fill(OUTLINE, capital.inflate(2, 2))
        surface.fill(STONE_LIGHT, capital)
        base = pygame.Rect(rect.x, rect.bottom - 3, rect.w, 4)
        surface.fill(OUTLINE, base.inflate(2, 2))
        surface.fill(STONE_LIGHT, base)
        if damaged:
            surface.fill(OUTLINE, (shaft.x + 3, shaft.y + 6, 1, 5))
            surface.fill(OUTLINE, (shaft.x + 4, shaft.y + 10, 2, 1))

    def _draw_vase(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        """A blue and white porcelain vase."""
        self._shadow(surface, rect)
        belly = pygame.Rect(rect.x - 1, rect.y - 3, rect.w + 2, rect.h + 3)
        neck = pygame.Rect(0, 0, 4, 4)
        neck.midbottom = (belly.centerx, belly.y + 1)
        pygame.draw.ellipse(surface, OUTLINE, belly.inflate(2, 2))
        pygame.draw.rect(surface, OUTLINE, neck.inflate(2, 2))
        pygame.draw.ellipse(surface, PORCELAIN, belly)
        surface.fill(PORCELAIN, neck)
        surface.fill(PORCELAIN_BLUE, (belly.x + 2, belly.centery, belly.w - 4, 1))
        surface.fill(PORCELAIN_BLUE, (belly.centerx - 1, belly.y + 2, 2, 2))
        if damaged:
            surface.fill(OUTLINE, (belly.centerx + 1, belly.y + 3, 1, 3))

    def _draw_chair(self, surface, rect: pygame.Rect, damaged: bool) -> None:
        """A carved wooden chair with a velvet seat."""
        self._shadow(surface, rect)
        back = pygame.Rect(rect.x, rect.y - 8, rect.w, 5)
        seat = pygame.Rect(rect.x, rect.y - 3, rect.w, 6)
        legs = pygame.Rect(rect.x + 1, rect.y + 3, rect.w - 2, rect.h - 4)
        pygame.draw.rect(surface, OUTLINE, back.union(legs).inflate(2, 2))
        surface.fill(WOOD_DARK, legs)
        surface.fill(WOOD, (legs.x + 2, legs.y, legs.w - 4, legs.h))
        surface.fill(WOOD_LIGHT, back)
        surface.fill(VELVET, seat)
        surface.fill(tuple(c + 20 for c in VELVET), (seat.x + 1, seat.y + 1, seat.w - 2, 1))
        if damaged:
            surface.fill(OUTLINE, (back.x + 4, back.y + 1, 1, 3))

    def _draw_debris(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        rng = random.Random(self.stage_index(obstacle))
        rect = _to_pygame(obstacle.rect)
        colors = {
            "pillar": [STONE, STONE_LIGHT, STONE_DARK],
            "vase": [PORCELAIN, PORCELAIN_BLUE],
        }.get(obstacle.kind, [WOOD, WOOD_LIGHT, WOOD_DARK])
        for _ in range(10 if obstacle.kind == "pillar" else 5):
            x = rng.randint(rect.x - 6, rect.right + 4)
            y = rng.randint(rect.y - 2, rect.bottom + 3)
            w, h = (rng.randint(3, 6), 2) if rng.random() < 0.5 else (2, rng.randint(2, 4))
            surface.fill(OUTLINE, (x - 1, y - 1, w + 2, h + 2))
            surface.fill(rng.choice(colors), (x, y, w, h))
