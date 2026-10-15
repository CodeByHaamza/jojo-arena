"""Draws a Match: arena, fighters, projectiles and impact effects."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from jojo_arena.characters import FighterDef
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.combat.match import Match
from jojo_arena.engine.effects import blit_glow, blit_shadow, radial_glow
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.sprites import (
    AnimSpec,
    PlaceholderSprites,
    SheetSprites,
    frame_index,
    shade,
    sprite_direction,
)
from jojo_arena.paths import SPRITES_DIR
from jojo_arena.stages.base import StageDef

OUTLINE = (23, 18, 31)
CHEST = Vec2(0, -16)  # effects happen at chest height, not on the ground
SHADOW_SIZE = (22, 7)

# When a sheet lacks an animation, show the closest one that exists.
ANIM_FALLBACKS = {
    "special": "heavy",
    "heavy": "light",
    "light": "idle",
    "hha": "special",
    "pose": "idle",
    "guard": "idle",
    "hurt": "idle",
    "ko": "hurt",
    "dash": "walk",
    "walk": "idle",
}
STATE_ANIMS = {
    State.IDLE: "idle",
    State.WALK: "walk",
    State.GUARD: "guard",
    State.BLOCKSTUN: "guard",
    State.GUARD_BROKEN: "hurt",
    State.DASH: "dash",
    State.HITSTUN: "hurt",
    State.KO: "ko",
}


class FighterView:
    def __init__(self, fighter_def: FighterDef) -> None:
        self.fighter_def = fighter_def
        sheet = None
        if fighter_def.sprite:
            base = SPRITES_DIR / fighter_def.sprite
            sheet = SheetSprites.load(
                base.with_suffix(".png"), base.with_suffix(".toml"), fighter_def.palette or None
            )
        self.sprites = sheet or PlaceholderSprites(fighter_def.color)

    def resolve(self, anim: str) -> tuple[str, AnimSpec]:
        name = anim
        while self.sprites.spec(name) is None and name in ANIM_FALLBACKS:
            name = ANIM_FALLBACKS[name]
        return name, self.sprites.spec(name) or AnimSpec(name, 1)

    def current_frame(self, fighter: Fighter) -> pygame.Surface:
        phase = None
        if fighter.state == State.ATTACK and fighter.attack is not None:
            anim = fighter.attack.move.anim
            phase = fighter.attack.phase_info()
        else:
            anim = STATE_ANIMS.get(fighter.state, "idle")
        name, spec = self.resolve(anim)
        index = frame_index(spec, fighter.state_f, phase)
        direction, flip = sprite_direction(fighter.facing.x, fighter.facing.y)
        image = self.sprites.frame(name, direction, flip, index)
        if fighter.state in (State.HITSTUN, State.GUARD_BROKEN) and fighter.state_f < 3:
            image = image.copy()
            image.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_MAX)
        return image

    def draw(self, surface: pygame.Surface, fighter: Fighter, tick: int) -> None:
        image = self.current_frame(fighter)
        ax, ay = self.sprites.anchor
        _, flip = sprite_direction(fighter.facing.x, fighter.facing.y)
        if flip:
            ax = image.get_width() - 1 - ax
        if fighter.invincible:
            # Afterimages trailing behind an invincible dash.
            ghost = image.copy()
            ghost.fill((*self.fighter_def.aura, 0), special_flags=pygame.BLEND_RGB_MAX)
            ghost.set_alpha(70)
            step = fighter.dash_dir * fighter.rules.dash_speed
            for back in (6, 3):
                pos = fighter.pos - step * back
                surface.blit(ghost, (round(pos.x) - ax, round(pos.y) - ay))
        surface.blit(image, (round(fighter.pos.x) - ax, round(fighter.pos.y) - ay))
        if fighter.state == State.GUARD_BROKEN:
            # Dizzy stars circling over the head.
            for i in range(3):
                a = tick * 0.15 + i * 2 * math.pi / 3
                x = fighter.pos.x + math.cos(a) * 8
                y = fighter.pos.y - 44 + math.sin(a) * 3
                surface.fill((255, 230, 90), (round(x), round(y), 2, 2))


@dataclass
class Spark:
    pos: Vec2
    life: int
    max_life: int
    color: tuple[int, int, int]
    size: int
    rays: int = 0
    angle: float = 0.0


class FightView:
    def __init__(self, stage: StageDef, fighter_defs: list[FighterDef]) -> None:
        from jojo_arena.stages import stage_renderer

        self.renderer = stage_renderer(stage)
        self.fighter_views = [FighterView(d) for d in fighter_defs]
        self.fighter_defs = fighter_defs
        self.sparks: list[Spark] = []
        self.shake = 0
        self.tick = 0
        self._tint: pygame.Surface | None = None

    # Reacting to the simulation ------------------------------------------------------

    def on_events(self, events: list[Event]) -> None:
        for event in events:
            pos = event.pos + CHEST if event.pos is not None else None
            if event.kind == "hit":
                heavy = event.value >= 80
                self.sparks.append(Spark(pos, 14, 14, (255, 210, 140), 16 if heavy else 10, 6))
                self.shake = max(self.shake, 8 if heavy else 3)
            elif event.kind in ("wall_bounce", "prop_break"):
                self.sparks.append(Spark(pos, 12, 12, (150, 130, 110), 12, 8))
                self.shake = max(self.shake, 6)
            elif event.kind == "prop_hit":
                self.sparks.append(Spark(pos, 8, 8, (170, 140, 100), 6, 4))
            elif event.kind in ("projectile_wall", "projectile_clash", "projectile_fade"):
                self.sparks.append(Spark(pos, 10, 10, (200, 200, 255), 8, 5))
            elif event.kind == "block":
                self.sparks.append(Spark(pos, 10, 10, (110, 170, 255), 9, 4))
            elif event.kind == "guard_break":
                self.sparks.append(Spark(pos, 20, 20, (255, 255, 255), 20, 10))
                self.shake = max(self.shake, 10)
            elif event.kind == "stylish":
                self.sparks.append(Spark(pos, 24, 24, (255, 200, 60), 18, 8))
            elif event.kind == "ko":
                self.shake = max(self.shake, 14)

    def update(self) -> None:
        self.tick += 1
        for spark in self.sparks:
            spark.life -= 1
            spark.angle += 0.15
        self.sparks = [s for s in self.sparks if s.life > 0]
        if self.shake:
            self.shake -= 1

    # Drawing ---------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, match: Match) -> None:
        self.renderer.draw_background(surface)
        self.renderer.draw_floor_details(surface, match.arena)
        for fighter in match.fighters:
            blit_shadow(surface, (fighter.pos.x, fighter.pos.y), *SHADOW_SIZE)
        for projectile in match.projectiles:
            blit_shadow(surface, (projectile.pos.x, projectile.pos.y), 8, 3)
        drawables = [(o.rect.bottom, 0, o) for o in match.arena.obstacles if not o.broken]
        drawables += [(f.pos.y, 1, f) for f in match.fighters]
        for _, kind, item in sorted(drawables, key=lambda d: (d[0], d[1])):
            if kind == 0:
                self.renderer.draw_obstacle(surface, item)
            else:
                self.fighter_views[item.index].draw(surface, item, self.tick)
        for projectile in match.projectiles:
            self._draw_projectile(surface, projectile)
        self.renderer.draw_lights(surface, self.tick)
        for fighter in match.fighters:
            if fighter.state in (State.GUARD, State.BLOCKSTUN):
                shield = fighter.pos + fighter.facing * 10 + CHEST
                blit_glow(surface, radial_glow(10, (30, 50, 90)), shield)
        for spark in self.sparks:
            self._draw_spark(surface, spark)
        if match.slowmo:
            surface.blit(self._slowmo_tint(surface.get_size()), (0, 0))
        if self.shake:
            surface.scroll(1 if self.shake % 2 else -1, 1 if self.shake % 4 < 2 else 0)

    def _slowmo_tint(self, size: tuple[int, int]) -> pygame.Surface:
        if self._tint is None or self._tint.get_size() != size:
            self._tint = pygame.Surface(size, pygame.SRCALPHA)
            self._tint.fill((40, 30, 90, 50))
        return self._tint

    def _draw_projectile(self, surface: pygame.Surface, projectile) -> None:
        color = self.fighter_defs[projectile.owner].aura
        pos = projectile.pos + CHEST * 0.8
        r = round(projectile.radius)
        blit_glow(surface, radial_glow(r * 3, tuple(c // 2 for c in color)), (pos.x, pos.y))
        center = pos.as_ints()
        pygame.draw.circle(surface, OUTLINE, center, r + 1)
        pygame.draw.circle(surface, shade(color, 40), center, r)
        pygame.draw.circle(surface, (255, 255, 255), center, max(1, r - 2))

    def _draw_spark(self, surface: pygame.Surface, spark: Spark) -> None:
        k = spark.life / spark.max_life
        glow_color = tuple(round(c * k) for c in spark.color)
        blit_glow(
            surface, radial_glow(max(2, round(spark.size * (1.5 - k))), glow_color), spark.pos
        )
        length = spark.size * (1.2 - k * 0.6)
        for i in range(spark.rays):
            a = spark.angle + i * 2 * math.pi / spark.rays
            start = spark.pos + Vec2.from_angle(a, length * 0.4)
            end = spark.pos + Vec2.from_angle(a, length)
            pygame.draw.line(surface, (255, 255, 230), start.as_ints(), end.as_ints())
