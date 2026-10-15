"""Debug scene: walk two bodies around the arena to check walls, props, sprites and controls."""

from __future__ import annotations

import pygame

from jojo_arena.context import GameContext
from jojo_arena.engine.effects import blit_glow, blit_shadow, radial_glow
from jojo_arena.engine.geometry import Vec2, circles_overlap
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import (
    PlaceholderSprites,
    SheetSprites,
    frame_index,
    parse_color,
    sprite_direction,
)
from jojo_arena.paths import SPRITES_DIR
from jojo_arena.stages import load_stage, stage_renderer

BODY_RADIUS = 8
SPEED = 1.6
PALETTES = [
    {
        "body": ["#6b1f2a", "#a8303c", "#d8545a", "#f3a19c"],
        "trim": ["#3b2f3f", "#5d4b5f", "#86708a"],
    },
    {
        "body": ["#1f3b6b", "#2f5fa8", "#5288d8", "#a6c8f3"],
        "trim": ["#3b2f3f", "#5d4b5f", "#86708a"],
    },
]


class SandboxScene(Scene):
    def __init__(self, ctx: GameContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.stage = load_stage("cairo_night")
        self.renderer = stage_renderer(self.stage)
        self.arena = self.stage.build_arena()
        self.bodies = [spawn.copy() for spawn in self.arena.spawns]
        self.facing = [Vec2(1, 0), Vec2(-1, 0)]
        self.moving = [False, False]
        self.sources = [p.build_source() for p in ctx.controls.active_preset.players]
        self.sprites = []
        for palette in PALETTES:
            tones = {slot: [parse_color(c) for c in colors] for slot, colors in palette.items()}
            sheet = SheetSprites.load(
                SPRITES_DIR / "mannequin" / "mannequin.png",
                SPRITES_DIR / "mannequin" / "mannequin.toml",
                tones,
            )
            self.sprites.append(sheet or PlaceholderSprites(tones["body"][1]))
        self.tick = 0
        self.sparks: list[tuple[Vec2, int]] = []

    def update(self) -> None:
        self.tick += 1
        for i, source in enumerate(self.sources):
            frame = source.read(self.ctx.inputs)
            move = Vec2(*frame.move)
            self.moving[i] = move.length_sq() > 0
            if self.moving[i]:
                self.facing[i] = move
            pos, _, _ = self.arena.constrain(self.bodies[i] + move * SPEED, BODY_RADIUS)
            self.bodies[i] = pos
            if frame.was_pressed("light"):
                self.sparks.append((pos + self.facing[i] * 16 + Vec2(0, -16), 14))
                for obstacle in self.arena.obstacles:
                    if obstacle.solid and obstacle.rect.inflate(14).contains(pos):
                        obstacle.damage(30)
        a, b = self.bodies
        if circles_overlap(a, BODY_RADIUS, b, BODY_RADIUS):
            push = (a - b).normalized() * ((2 * BODY_RADIUS - a.distance_to(b)) / 2)
            self.bodies = [a + push, b - push]
        for obstacle in self.arena.obstacles:
            obstacle.tick()
        self.sparks = [(pos, life - 1) for pos, life in self.sparks if life > 1]

    def draw(self, surface: pygame.Surface) -> None:
        self.renderer.draw_background(surface)
        self.renderer.draw_floor_details(surface, self.arena)
        for pos in self.bodies:
            blit_shadow(surface, (pos.x, pos.y), 20, 7)
        items = [(o.rect.bottom, "obstacle", o) for o in self.arena.obstacles]
        items += [(b.y, "body", i) for i, b in enumerate(self.bodies)]
        for _, kind, item in sorted(items, key=lambda entry: entry[0]):
            if kind == "obstacle":
                self.renderer.draw_obstacle(surface, item)
            else:
                self._draw_body(surface, item)
        self.renderer.draw_lights(surface, self.tick)
        for pos, life in self.sparks:
            blit_glow(surface, radial_glow(4 + life, (255, 200, 120)), (pos.x, pos.y))

    def _draw_body(self, surface: pygame.Surface, i: int) -> None:
        sprites = self.sprites[i]
        anim = "walk" if self.moving[i] else "idle"
        direction, flip = sprite_direction(self.facing[i].x, self.facing[i].y)
        index = frame_index(sprites.spec(anim), self.tick)
        image = sprites.frame(anim, direction, flip, index)
        ax, ay = sprites.anchor
        if flip:
            ax = image.get_width() - 1 - ax
        pos = self.bodies[i]
        surface.blit(image, (round(pos.x) - ax, round(pos.y) - ay))
