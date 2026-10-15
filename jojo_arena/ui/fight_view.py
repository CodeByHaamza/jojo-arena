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
STAND_ALPHA = 215  # Stands look a little spectral
STAND_FLOAT = 6  # Stands hover this many pixels above the ground

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
    "switch": "pose",
}
STATE_ANIMS = {
    State.IDLE: "idle",
    State.WALK: "walk",
    State.GUARD: "guard",
    State.BLOCKSTUN: "guard",
    State.GUARD_BROKEN: "hurt",
    State.DASH: "dash",
    State.POSE: "pose",
    State.SWITCH: "switch",
    State.CLASH: "light",
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
        # Effects happen at chest height, not on the ground; labels go over the head.
        self.chest = Vec2(0, -self.sprites.chest)
        self.height = self.sprites.height
        self.shadow = (round(14 + self.height * 0.25), 7)
        self.stand: SheetSprites | None = None
        if fighter_def.stand_sprite:
            base = SPRITES_DIR / fighter_def.stand_sprite
            self.stand = SheetSprites.load(base.with_suffix(".png"), base.with_suffix(".toml"))

    @staticmethod
    def resolve(sprites, anim: str) -> tuple[str, AnimSpec]:
        name = anim
        while sprites.spec(name) is None and name in ANIM_FALLBACKS:
            name = ANIM_FALLBACKS[name]
        return name, sprites.spec(name) or AnimSpec(name, 1)

    def current_frame(self, fighter: Fighter, sprites=None) -> pygame.Surface:
        """The fighter's frame; with `sprites`, the same animation from another sheet."""
        sprites = sprites or self.sprites
        phase = None
        if fighter.state == State.ATTACK and fighter.attack is not None:
            anim = fighter.attack.move.anim
            phase = fighter.attack.phase_info()
        else:
            anim = STATE_ANIMS.get(fighter.state, "idle")
        name, spec = self.resolve(sprites, anim)
        if fighter.state == State.CLASH:
            # Rapid-fire punches, alternating between the two "extended" frames.
            index = min(spec.frames - 1, 1 + (fighter.state_f // 3) % 2)
        else:
            index = frame_index(spec, fighter.state_f, phase)
        direction, flip = sprite_direction(fighter.facing.x, fighter.facing.y)
        image = sprites.frame(name, direction, flip, index)
        if fighter.state in (State.HITSTUN, State.GUARD_BROKEN) and fighter.state_f < 3:
            image = image.copy()
            image.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_MAX)
        return image

    # The Stand ---------------------------------------------------------------------------

    def stand_presence(self, fighter: Fighter) -> float:
        """0 = no Stand on screen, 1 = fully out (it fades in and out while switching)."""
        if self.stand is None:
            return 0.0
        if fighter.state == State.SWITCH:
            t = fighter.state_f / max(1, fighter.rules.stance_switch_f)
            coming_out = fighter.switch_target != next(iter(fighter.kit.stances))
            return t if coming_out else 1 - t
        return 1.0 if fighter.aura_active else 0.0

    def stand_ground(self, fighter: Fighter) -> Vec2:
        """Where the Stand floats: just behind its user, or in front of them to strike."""
        if fighter.state in (State.ATTACK, State.CLASH):
            return fighter.pos + fighter.facing * 13
        beside = Vec2(-fighter.facing.y, fighter.facing.x)
        return fighter.pos - fighter.facing * 8 + beside * 6

    def draw_stand(self, surface: pygame.Surface, fighter: Fighter, tick: int) -> None:
        presence = self.stand_presence(fighter)
        if presence <= 0:
            return
        pos = self.stand_ground(fighter)
        lift = STAND_FLOAT + round(math.sin(tick * 0.08) * 1.5)
        chest = pos + Vec2(0, -self.stand.chest - lift)
        aura = tuple(round(c * 0.45 * presence) for c in self.fighter_def.aura)
        blit_glow(surface, radial_glow(26, aura), chest)
        image = self.current_frame(fighter, self.stand).copy()
        image.set_alpha(round(STAND_ALPHA * presence))
        ax, ay = self.stand.anchor
        _, flip = sprite_direction(fighter.facing.x, fighter.facing.y)
        if flip:
            ax = image.get_width() - 1 - ax
        surface.blit(image, (round(pos.x) - ax, round(pos.y) - ay - lift))

    def draw_aura(self, surface: pygame.Surface, fighter: Fighter, tick: int) -> None:
        """Additive light behind the body: Stand aura, stance switch, Résolution."""
        body = fighter.pos + self.chest
        aura = self.fighter_def.aura
        if fighter.aura_active or fighter.state == State.SWITCH:
            pulse = 0.75 + 0.15 * math.sin(tick * 0.2)
            if fighter.state == State.SWITCH:
                pulse = 0.4 + 0.6 * fighter.state_f / max(1, fighter.rules.stance_switch_f)
            # With a visible Stand the user's own aura stays discreet.
            radius = 18 if self.stand is not None else 30
            if self.stand is not None:
                pulse *= 0.5
            blit_glow(surface, radial_glow(radius, tuple(round(c * pulse) for c in aura)), body)
        if fighter.state == State.POSE:
            for i in range(4):
                rise = (tick * 0.6 + i * 9) % 36
                x = fighter.pos.x + math.sin(i * 2.1 + tick * 0.05) * 10
                glow = radial_glow(3, tuple(round(c * (1 - rise / 36)) for c in aura))
                blit_glow(surface, glow, (x, fighter.pos.y - 6 - rise))
        if fighter.in_resolve:
            pulse = 0.25 + 0.15 * math.sin(tick * 0.25)
            blit_glow(surface, radial_glow(14, (round(255 * pulse), 20, 20)), fighter.pos)

    def draw(self, surface: pygame.Surface, fighter: Fighter, tick: int) -> None:
        self.draw_aura(surface, fighter, tick)
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
        if fighter.aura_active:
            # A faint second pass over the body so the aura also tints the sprite.
            tint = tuple(round(c * 0.18) for c in self.fighter_def.aura)
            blit_glow(surface, radial_glow(18, tint), fighter.pos + self.chest)
        if fighter.state == State.GUARD_BROKEN:
            # Dizzy stars circling over the head.
            for i in range(3):
                a = tick * 0.15 + i * 2 * math.pi / 3
                x = fighter.pos.x + math.cos(a) * 8
                y = fighter.pos.y - self.height - 4 + math.sin(a) * 3
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
        self.flash = 0  # white screen flash frames left
        self.tick = 0
        self._overlays: dict[tuple, pygame.Surface] = {}

    # Reacting to the simulation ------------------------------------------------------

    def chest(self, index: int | None) -> Vec2:
        """Chest offset of one fighter, or the average of both when nobody in particular."""
        if index is not None:
            return self.fighter_views[index].chest
        a, b = (view.chest for view in self.fighter_views)
        return (a + b) * 0.5

    def on_events(self, events: list[Event]) -> None:
        for event in events:
            pos = event.pos + self.chest(event.fighter) if event.pos is not None else None
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
            elif event.kind == "flash_cancel":
                self.sparks.append(Spark(pos, 12, 12, (255, 255, 255), 20, 12))
                self.flash = 6
            elif event.kind == "hha":
                aura = self.fighter_defs[event.fighter].aura
                self.sparks.append(Spark(pos, 30, 30, aura, 30, 12))
            elif event.kind == "clash_start":
                self.sparks.append(Spark(pos, 20, 20, (255, 255, 255), 24, 10))
                self.shake = max(self.shake, 8)
            elif event.kind in ("clash_win", "clash_tie"):
                self.sparks.append(Spark(pos, 24, 24, (255, 230, 150), 28, 12))
                self.shake = max(self.shake, 12)
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
        if self.flash:
            self.flash -= 1

    # Drawing ---------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, match: Match) -> None:
        self.renderer.draw_background(surface)
        self.renderer.draw_floor_details(surface, match.arena)
        for fighter in match.fighters:
            shadow = self.fighter_views[fighter.index].shadow
            blit_shadow(surface, (fighter.pos.x, fighter.pos.y), *shadow)
        for projectile in match.projectiles:
            blit_shadow(surface, (projectile.pos.x, projectile.pos.y), 8, 3)
        drawables = [(o.rect.bottom, 0, o) for o in match.arena.obstacles if not o.broken]
        drawables += [(f.pos.y, 1, f) for f in match.fighters]
        for fighter in match.fighters:
            view = self.fighter_views[fighter.index]
            if view.stand_presence(fighter) > 0:
                drawables.append((view.stand_ground(fighter).y, 2, fighter))
        for _, kind, item in sorted(drawables, key=lambda d: (d[0], d[1])):
            if kind == 0:
                self.renderer.draw_obstacle(surface, item)
            elif kind == 1:
                self.fighter_views[item.index].draw(surface, item, self.tick)
            else:
                self.fighter_views[item.index].draw_stand(surface, item, self.tick)
        for projectile in match.projectiles:
            self._draw_projectile(surface, projectile)
        self.renderer.draw_lights(surface, self.tick)
        for fighter in match.fighters:
            if fighter.state in (State.GUARD, State.BLOCKSTUN):
                shield = fighter.pos + fighter.facing * 10 + self.chest(fighter.index)
                blit_glow(surface, radial_glow(10, (30, 50, 90)), shield)
        if match.super_user is not None:
            # Heart Heat flash: the world goes dark, only the user stays lit.
            surface.blit(self._overlay(surface.get_size(), (8, 4, 20, 150)), (0, 0))
            user = match.fighters[match.super_user]
            aura = self.fighter_defs[user.index].aura
            glow = radial_glow(40, tuple(c // 2 for c in aura))
            blit_glow(surface, glow, user.pos + self.chest(user.index))
            self.fighter_views[user.index].draw(surface, user, self.tick)
        for spark in self.sparks:
            self._draw_spark(surface, spark)
        if match.clash is not None:
            self._draw_clash(surface, match)
        if match.slowmo:
            surface.blit(self._overlay(surface.get_size(), (40, 30, 90, 50)), (0, 0))
        if self.flash:
            surface.blit(
                self._overlay(surface.get_size(), (255, 255, 255, 20 * self.flash)), (0, 0)
            )
        if self.shake:
            surface.scroll(1 if self.shake % 2 else -1, 1 if self.shake % 4 < 2 else 0)

    def _overlay(self, size: tuple[int, int], rgba: tuple[int, int, int, int]) -> pygame.Surface:
        """Full-screen translucent color, cached per size and color."""
        key = (size, rgba)
        if key not in self._overlays:
            overlay = pygame.Surface(size, pygame.SRCALPHA)
            overlay.fill(rgba)
            self._overlays[key] = overlay
        return self._overlays[key]

    def _draw_clash(self, surface: pygame.Surface, match: Match) -> None:
        clash = match.clash
        center = clash.pos + self.chest(None)
        head_room = max(view.height for view in self.fighter_views) + self.chest(None).y
        # Flickering impact light where the two attacks meet.
        flicker = 0.6 + 0.4 * ((self.tick // 2) % 2)
        blit_glow(surface, radial_glow(22, tuple(round(255 * flicker) for _ in range(3))), center)
        for i in range(8):
            a = self.tick * 0.5 + i * math.pi / 4
            end = center + Vec2.from_angle(a, 10 + (i * 7 + self.tick) % 9)
            pygame.draw.line(surface, (255, 250, 220), center.as_ints(), end.as_ints())
        # Duel bar: each side pushes the split point toward the other.
        width, height = 120, 6
        bar = pygame.Rect(0, 0, width, height)
        bar.center = (round(center.x), round(center.y - head_room) - 12)
        bar.clamp_ip(surface.get_rect().inflate(-8, -8))
        # balance -1 = player 1 winning: their color fills toward the right.
        split = bar.x + round(width / 2 * (1 - clash.balance))
        colors = [self.fighter_defs[i].color for i in range(2)]
        surface.fill(OUTLINE, bar.inflate(4, 4))
        surface.fill(colors[0], (bar.x, bar.y, split - bar.x, height))
        surface.fill(colors[1], (split, bar.y, bar.right - split, height))
        surface.fill((255, 255, 255), (split - 1, bar.y - 2, 2, height + 4))
        # Time left, as a thin line under the bar.
        left = round(width * clash.frames_left / clash.duration_f)
        surface.fill((255, 255, 255), (bar.x, bar.bottom + 3, left, 1))

    def _draw_projectile(self, surface: pygame.Surface, projectile) -> None:
        color = self.fighter_defs[projectile.owner].aura
        pos = projectile.pos + self.chest(projectile.owner) * 0.8
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
