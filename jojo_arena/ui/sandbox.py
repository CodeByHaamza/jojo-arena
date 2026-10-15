"""Debug scene: walk two bodies around the arena to check walls, props and controls."""

from __future__ import annotations

import pygame

from jojo_arena.context import GameContext
from jojo_arena.engine.geometry import Vec2, circles_overlap
from jojo_arena.engine.scene import Scene
from jojo_arena.stages import load_stage, stage_renderer

BODY_RADIUS = 8
SPEED = 1.6
COLORS = [(220, 70, 70), (70, 130, 230)]


class SandboxScene(Scene):
    def __init__(self, ctx: GameContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.stage = load_stage("cairo_night")
        self.renderer = stage_renderer(self.stage)
        self.arena = self.stage.build_arena()
        self.bodies = [spawn.copy() for spawn in self.arena.spawns]
        self.sources = [p.build_source() for p in ctx.controls.active_preset.players]

    def update(self) -> None:
        for i, source in enumerate(self.sources):
            frame = source.read(self.ctx.inputs)
            pos = self.bodies[i] + Vec2(*frame.move) * SPEED
            pos, _, _ = self.arena.constrain(pos, BODY_RADIUS)
            self.bodies[i] = pos
            if frame.was_pressed("light"):
                for obstacle in self.arena.obstacles:
                    if obstacle.solid and obstacle.rect.inflate(14).contains(pos):
                        obstacle.damage(30)
        a, b = self.bodies
        if circles_overlap(a, BODY_RADIUS, b, BODY_RADIUS):
            push = (a - b).normalized() * ((2 * BODY_RADIUS - a.distance_to(b)) / 2)
            self.bodies = [a + push, b - push]
        for obstacle in self.arena.obstacles:
            obstacle.tick()

    def draw(self, surface: pygame.Surface) -> None:
        self.renderer.draw_background(surface)
        self.renderer.draw_floor_details(surface, self.arena)
        items = [(o.rect.bottom, "obstacle", o) for o in self.arena.obstacles]
        items += [(b.y, "body", i) for i, b in enumerate(self.bodies)]
        for _, kind, item in sorted(items, key=lambda entry: entry[0]):
            if kind == "obstacle":
                self.renderer.draw_obstacle(surface, item)
            else:
                pos = self.bodies[item]
                pygame.draw.ellipse(surface, (10, 8, 16), (pos.x - 9, pos.y - 3, 18, 6))
                pygame.draw.circle(surface, COLORS[item], (pos.x, pos.y - 12), BODY_RADIUS)
