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
    sprite_direction,
)
from jojo_arena.paths import SPRITES_DIR
from jojo_arena.stages.base import StageDef
from jojo_arena.ui import sfx, vfx
from jojo_arena.ui.duel_view import DuelScreen

OUTLINE = (23, 18, 31)
STAND_ALPHA = 215  # Stands look a little spectral
STAND_FLOAT = 6  # Stands hover this many pixels above the ground

# When a sheet lacks an animation, show the closest one that exists.
ANIM_FALLBACKS = {
    "kick": "light",
    "kick_high": "kick",
    "uppercut": "heavy",
    "headbutt": "heavy",
    "sweep": "kick",
    "leap": "dash",
    "counter": "guard",
    "grab": "special",
    "tackle": "dash",
    "special_alt": "special",
    "gha": "hha",
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
        if sprites.spec(name) is None and sprites.spec("idle") is not None:
            name = "idle"  # an animation nobody planned for: never crash, stand still
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
        attack = fighter.attack
        rushing = attack is not None and attack.move.hits > 1 and attack.active
        if fighter.state == State.CLASH or rushing:
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
        attack = fighter.attack
        if fighter.state == State.ATTACK and attack is not None and attack.move.stand_flash:
            return 1.0  # it surges out for this one blow
        return 1.0 if fighter.aura_active else 0.0

    def draw_stand(self, surface: pygame.Surface, fighter: Fighter, tick: int) -> None:
        presence = self.stand_presence(fighter)
        if presence <= 0:
            return
        pos = fighter.stand_spot()  # same spot the simulation uses for hits on the Stand
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

    @staticmethod
    def lift(fighter: Fighter) -> float:
        """How high a leaping fighter is above the ground (its shadow stays down)."""
        attack = fighter.attack
        if fighter.state != State.ATTACK or attack is None or attack.dest is None:
            return 0.0
        if attack.phase != 0 or attack.move.leap_height <= 0:
            return 0.0
        t = (attack.frame + 1) / max(1, attack.move.startup_f)
        return math.sin(math.pi * min(1.0, t)) * attack.move.leap_height

    def draw(self, surface: pygame.Surface, fighter: Fighter, tick: int) -> None:
        self.draw_aura(surface, fighter, tick)
        image = self.current_frame(fighter)
        ax, ay = self.sprites.anchor
        ay += round(self.lift(fighter))
        _, flip = sprite_direction(fighter.facing.x, fighter.facing.y)
        if flip:
            ax = image.get_width() - 1 - ax
        trail = None
        if fighter.invincible and fighter.state == State.DASH:
            trail = fighter.dash_dir * fighter.rules.dash_speed
        elif fighter.buff is not None and fighter.buff.afterimages:
            if fighter.walk_dir.length_sq():
                trail = fighter.walk_dir * fighter.walk_speed()
            elif fighter.state == State.ATTACK:
                trail = fighter.facing * 1.5
        if trail is not None:
            # Afterimages trailing behind a dash, or behind a body moving too fast to see.
            ghost = image.copy()
            ghost.fill((*self.fighter_def.aura, 0), special_flags=pygame.BLEND_RGB_MAX)
            ghost.set_alpha(70)
            for back in (6, 3):
                pos = fighter.pos - trail * back
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
        self.waves: list[list] = []  # time stop shockwaves: [center, age]
        self.tick = 0
        self._overlays: dict[tuple, pygame.Surface] = {}
        self.words = sfx.SfxLayer()
        self.fx = vfx.EffectsLayer()
        self._seen: list[tuple] = [(None, -1), (None, -1)]  # (state, attack serial) per fighter
        self.duel: DuelScreen | None = None  # the rush duel close-up, while a clash lasts
        self.debug = False  # F3: draw the circles the simulation hits with
        self._block_word_f = [0, 0]

    # Reacting to the simulation ------------------------------------------------------

    def chest(self, index: int | None) -> Vec2:
        """Chest offset of one fighter, or the average of both when nobody in particular."""
        if index is not None:
            return self.fighter_views[index].chest
        a, b = (view.chest for view in self.fighter_views)
        return (a + b) * 0.5

    def on_events(self, events: list[Event], match: Match | None = None) -> None:
        if match is not None:
            self._comic(events, match)
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
            elif event.kind == "time_stop":
                self.waves.append([event.pos + self.chest(event.fighter), 0])
                self.shake = max(self.shake, 10)
            elif event.kind == "time_resume":
                self.flash = 8
            elif event.kind == "delayed_hits":
                self.sparks.append(Spark(pos, 26, 26, (255, 220, 160), 30, 12))
                self.shake = max(self.shake, 14)
            elif event.kind == "trap_triggered":
                aura = self.fighter_defs[event.fighter].aura
                self.sparks.append(Spark(event.pos + Vec2(0, -8), 12, 12, aura, 12, 6))
            elif event.kind == "drain":
                self.sparks.append(Spark(pos, 16, 16, (230, 40, 60), 12, 6))
            elif event.kind == "ko":
                self.shake = max(self.shake, 14)

    def _shout_style(self, index: int):
        return sfx.shout_style(self.fighter_defs[index].aura)

    def _head(self, fighter: Fighter) -> Vec2:
        return fighter.pos + Vec2(0, -self.fighter_views[fighter.index].height - 8)

    def _comic(self, events: list[Event], match: Match) -> None:
        """Sound effects written on screen and impact effects, comic-book style."""
        words, fx = self.words, self.fx
        for event in events:
            kind = event.kind
            pos = event.pos + self.chest(event.fighter) if event.pos is not None else None
            if kind == "hit" and event.fighter is not None:
                attacker = match.fighters[1 - event.fighter]
                attack = attacker.attack
                move = attack.move if attack is not None else None
                if move is not None and move.hits > 1:
                    word = move.shout or "!"
                    base = attacker.stand_pos() or attacker.pos
                    center = base + self.chest(attacker.index) + Vec2(0, -24)
                    style = self._shout_style(attacker.index)
                    if attack.hits_done >= move.hits:
                        words.add(word + " !", center + Vec2(0, -12), style, 3, 44, 0.3, 2)
                        words.add(sfx.DOGO, pos + Vec2(0, -16), "impact", 3, 36, 0.4, 1)
                        fx.add(vfx.Ring(pos, (255, 240, 200), 3.0, 12, 3))
                        fx.focus(pos, heavy=True)
                    else:
                        words.scatter(word, center, 24, style=style, scale=2, life=20, rise=0.9)
                    fx.add(vfx.Flash(pos, 12))
                    continue
                if event.value >= 70:
                    words.add(sfx.DON if self.tick % 2 else sfx.DOGO, pos + Vec2(0, -14))
                    fx.add(vfx.Flash(pos, 18))
                    fx.add(vfx.Ring(pos, (255, 236, 190), 2.5, 10))
                    fx.focus(pos, heavy=True)
                elif event.value >= 35:
                    fx.add(vfx.Flash(pos, 11))
                    fx.focus(pos, heavy=False)
                else:
                    fx.add(vfx.Flash(pos, 7))
            elif kind == "block" and event.fighter is not None:
                if self._block_word_f[event.fighter] <= 0:
                    words.add(sfx.GA, pos + Vec2(0, -10), "block", 2, 18, 0.5)
                    self._block_word_f[event.fighter] = 12
                fx.add(vfx.Flash(pos, 8, (120, 170, 255)))
            elif kind == "guard_break":
                words.add(sfx.BAKI, pos + Vec2(0, -16), "white", 3, 40, 0.3, 2)
                fx.add(vfx.Ring(pos, (200, 220, 255), 3.0, 14, 3))
                fx.focus(pos, heavy=True)
            elif kind == "wall_bounce":
                words.add(sfx.DON, pos + Vec2(0, -12), "impact", 2, 30)
                fx.dust(event.pos, 8, 1.6)
                fx.add(vfx.Ring(pos, (220, 200, 170), 2.0, 10))
            elif kind == "prop_break":
                words.add(sfx.BAKI, pos + Vec2(0, -8), "impact", 2, 30)
                fx.dust(event.pos, 10, 1.8, 4)
            elif kind == "ko" and event.fighter is not None:
                loser = match.fighters[event.fighter]
                words.add(sfx.BAAN, self._head(loser) + Vec2(0, -6), "ko", 4, 80, 0.15, 1)
                fx.add(vfx.Ring(pos, (255, 90, 90), 3.5, 18, 3))
                fx.dust(loser.pos, 12, 2.0, 4)
            elif kind == "clash_start":
                shouts = tuple(self._rush_word(f) for f in match.fighters)
                self.duel = DuelScreen(self.fighter_views, self.fighter_defs, shouts)
                self.flash = 6
            elif kind == "clash_tie":
                self.duel = None
                self.flash = 8
            elif kind == "clash_win" and event.fighter is not None:
                self.duel = None
                self.flash = 8
                champion = match.fighters[event.fighter]
                shout = self._rush_word(champion) + " !"
                words.add(shout, self._head(champion), self._shout_style(champion.index), 3, 50)
                words.add(sfx.DOGO, pos, "impact", 3, 40, 0.4, 2)
                fx.add(vfx.Ring(pos, (255, 240, 200), 4.0, 16, 3))
                fx.focus(pos, heavy=True)
            elif kind in ("hha", "gha") and event.fighter is not None:
                user = match.fighters[event.fighter]
                aura = self.fighter_defs[user.index].aura
                fx.add(vfx.Ring(pos, aura, 4.0, 18, 3))
                words.add(sfx.DODODO, self._head(user) + Vec2(0, -8), "menace", 2, 50, 0.25, 1)
            elif kind == "stance_switch" and event.fighter is not None:
                user = match.fighters[event.fighter]
                if user.switch_target != user.base_stance:
                    fx.add(vfx.Ring(pos, self.fighter_defs[user.index].aura, 2.5, 14, 2))
                    side = -1 if user.facing.x >= 0 else 1
                    words.menace(user.pos + self.chest(user.index), side)
            elif kind == "delayed_hits":
                words.add(sfx.DOGO, pos + Vec2(0, -10), "impact", 3, 44, 0.3, 2)
                fx.add(vfx.Ring(pos, (255, 230, 180), 3.5, 16, 3))
                fx.focus(pos, heavy=True)
            elif kind == "stylish":
                fx.add(vfx.Ring(pos, (255, 210, 90), 2.5, 14))
            elif kind == "counter" and event.fighter is not None:
                user = match.fighters[event.fighter]
                aura = self.fighter_defs[user.index].aura
                words.add(sfx.DON, self._head(user), "white", 3, 40, 0.3, 2)
                fx.add(vfx.Ring(pos, aura, 3.5, 16, 3))
                fx.focus(pos, heavy=True)
                self.flash = max(self.flash, 4)
            elif kind == "armor":
                fx.add(vfx.Flash(pos, 16, (255, 150, 60), 6))
                fx.add(vfx.Ring(pos, (255, 170, 80), 2.0, 10))

    def _rush_word(self, fighter: Fighter) -> str:
        """What a fighter shouts while mashing a rush: its rush move's shout."""
        for move in fighter.kit.all_moves():
            if move.hits > 1 and move.shout:
                return move.shout
        return "!"

    def _observe(self, match: Match) -> None:
        """Effects that follow what fighters are doing rather than one event."""
        for fighter in match.fighters:
            i = fighter.index
            last_state, last_serial = self._seen[i]
            attack = fighter.attack
            serial = attack.serial if attack is not None else last_serial
            if fighter.state == State.DASH and last_state != State.DASH:
                self.fx.dust(fighter.pos, 5, 1.0)
                self.fx.add(vfx.SpeedLines(fighter.pos + self.chest(i), fighter.dash_dir))
            if attack is not None and serial != last_serial and fighter.state == State.ATTACK:
                move = attack.move
                if move.shout and move.hits <= 1:
                    self.words.add(move.shout, self._head(fighter), self._shout_style(i), 2, 46)
                elif move.hits > 1:
                    self.words.add(sfx.DODODO, self._head(fighter), "menace", 2, 30, 0.4, 1)
            if fighter.state == State.POSE and fighter.state_f % 16 == 0:
                side = 1 if (fighter.state_f // 16) % 2 else -1
                self.words.menace(fighter.pos + self.chest(i), side)
            if match.clash is not None and i == 0:
                self.shake = max(self.shake, 3)
                if self.tick % 4 == 0:
                    self.fx.focus(match.clash.pos + self.chest(None), heavy=True)
            if match.clash is not None and self.tick % 6 == i * 3:
                away = (fighter.pos - match.clash.pos).normalized()
                center = fighter.pos + self.chest(i) + away * 30 + Vec2(0, -6)
                style = self._shout_style(i)
                self.words.scatter(self._rush_word(fighter), center, 16, style=style, life=18)
            self._seen[i] = (fighter.state, serial)
            self._block_word_f[i] = max(0, self._block_word_f[i] - 1)

    def update(self, match: Match | None = None) -> None:
        if match is not None:
            self._observe(match)
            if match.clash is None:
                self.duel = None
            elif self.duel is not None:
                self.duel.update(self.tick)
        self.words.update()
        self.fx.update()
        for wave in self.waves:
            wave[1] += 1
        self.waves = [w for w in self.waves if w[1] < 40]
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
        if match.clash is not None and self.duel is not None:
            # The rush duel leaves the arena for its own close-up screen.
            self.duel.draw(surface, match, self.tick)
            self._draw_duel_bar(surface, match)
            self._finish_frame(surface)
            return
        self.renderer.draw_background(surface)
        self.renderer.draw_floor_details(surface, match.arena)
        for fighter in match.fighters:
            shadow = self.fighter_views[fighter.index].shadow
            blit_shadow(surface, (fighter.pos.x, fighter.pos.y), *shadow)
        for projectile in match.projectiles:
            blit_shadow(surface, (projectile.pos.x, projectile.pos.y), 8, 3)
        for trap in match.traps:
            self._draw_trap(surface, trap)
        for fighter in match.fighters:
            self._draw_falling_strike(surface, fighter)
        drawables = [(o.rect.bottom, 0, o) for o in match.arena.obstacles if not o.broken]
        drawables += [(f.pos.y, 1, f) for f in match.fighters]
        for fighter in match.fighters:
            view = self.fighter_views[fighter.index]
            if view.stand_presence(fighter) > 0:
                drawables.append((fighter.stand_spot().y, 2, fighter))
        for _, kind, item in sorted(drawables, key=lambda d: (d[0], d[1])):
            if kind == 0:
                self.renderer.draw_obstacle(surface, item)
            elif kind == 1:
                self.fighter_views[item.index].draw(surface, item, self.tick)
            else:
                self.fighter_views[item.index].draw_stand(surface, item, self.tick)
        for fighter in match.fighters:
            self._draw_reach(surface, fighter)
            self._draw_rush(surface, fighter)
            self._draw_reticle(surface, fighter)
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
        for center, age in self.waves:
            # The time stop shockwave: a ring sweeping out over the arena.
            radius = 8 + age * 9
            ring = (255, 255, 255) if age % 4 < 2 else (180, 160, 255)
            pygame.draw.circle(surface, ring, center.as_ints(), radius, 2)
        self.fx.draw(surface)
        if self.debug:
            self._draw_debug(surface, match)
        if match.clash is not None:
            self._draw_clash(surface, match)
        if match.time_stop is not None and match.super_freeze == 0:
            # Stopped time: the whole picture turns to its negative.
            negative = surface.copy()
            surface.fill((255, 255, 255))
            surface.blit(negative, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
        if match.slowmo:
            surface.blit(self._overlay(surface.get_size(), (40, 30, 90, 50)), (0, 0))
        self.words.draw(surface)
        self._finish_frame(surface)

    def _finish_frame(self, surface: pygame.Surface) -> None:
        """Screen-wide touches applied last: white flash and shake."""
        if self.flash:
            surface.blit(
                self._overlay(surface.get_size(), (255, 255, 255, 20 * self.flash)), (0, 0)
            )
        if self.shake:
            # Big hits shake harder; the shake settles as it runs out.
            amplitude = 1 + min(2, self.shake // 5)
            dx = amplitude if self.shake % 2 else -amplitude
            dy = (amplitude - 1 or 1) * (1 if self.shake % 4 < 2 else -1)
            surface.scroll(dx, dy)

    def _overlay(self, size: tuple[int, int], rgba: tuple[int, int, int, int]) -> pygame.Surface:
        """Full-screen translucent color, cached per size and color."""
        key = (size, rgba)
        if key not in self._overlays:
            overlay = pygame.Surface(size, pygame.SRCALPHA)
            overlay.fill(rgba)
            self._overlays[key] = overlay
        return self._overlays[key]

    def _draw_trap(self, surface: pygame.Surface, trap) -> None:
        """Threads laid on the ground: faint lines in the owner's color, a slight shimmer."""
        aura = self.fighter_defs[trap.owner].aura
        dim = tuple(c // 3 for c in aura)
        r = trap.defn.radius
        center = trap.pos
        for i in range(3):
            a = i * math.pi / 3 + 0.3
            start = center + Vec2.from_angle(a, r)
            end = center - Vec2.from_angle(a, r)
            pygame.draw.line(surface, dim, start.as_ints(), end.as_ints())
        if (self.tick // 20) % 3 == 0:
            surface.set_at(center.as_ints(), aura)

    def _draw_falling_strike(self, surface: pygame.Surface, fighter: Fighter) -> None:
        """A heavy object dropping on a spot (moves that land on the target): its shadow
        grows on the floor while it falls."""
        attack = fighter.attack
        if attack is None or not attack.move.at_target or attack.phase != 0:
            return
        progress = attack.frame / max(1, attack.move.startup_f)
        target = attack.target
        size = round(attack.move.radius * 2 * (0.3 + 0.7 * progress))
        blit_shadow(surface, (target.x, target.y), size, max(3, size // 3))
        height = 120 * (1 - progress)
        block = pygame.Rect(0, 0, 30, 18)
        block.midbottom = (round(target.x), round(target.y - height))
        surface.fill(OUTLINE, block.inflate(2, 2))
        surface.fill((90, 96, 108), block)
        surface.fill((140, 146, 160), (block.x, block.y, block.w, 4))

    def _draw_clash(self, surface: pygame.Surface, match: Match) -> None:
        clash = match.clash
        center = clash.pos + self.chest(None)
        # Flickering impact light where the two barrages meet, sparks flying off.
        flicker = 0.6 + 0.4 * ((self.tick // 2) % 2)
        blit_glow(surface, radial_glow(18, tuple(round(220 * flicker) for _ in range(3))), center)
        for i in range(10):
            a = self.tick * 0.5 + i * math.pi / 5
            end = center + Vec2.from_angle(a, 8 + (i * 7 + self.tick) % 10)
            pygame.draw.line(surface, OUTLINE, center.as_ints(), end.as_ints(), 3)
            pygame.draw.line(surface, (255, 250, 220), center.as_ints(), end.as_ints())
        self._draw_duel_bar(surface, match)

    def _draw_duel_bar(self, surface: pygame.Surface, match: Match) -> None:
        """Each side pushes the split point toward the other; time left underneath."""
        clash = match.clash
        width, height = 200, 8
        bar = pygame.Rect(0, 0, width, height)
        bar.center = (surface.get_width() // 2, 72)
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
        aura = self.fighter_defs[projectile.owner].aura
        pos = projectile.pos + self.chest(projectile.owner) * 0.8
        look = projectile.defn.look
        vfx.draw_projectile(surface, look, pos, projectile.velocity, projectile.radius, aura)

    def _draw_debug(self, surface: pygame.Surface, match: Match) -> None:
        """Hurt circles in blue, hit circles in red, projectiles in yellow (on the ground)."""
        for fighter in match.fighters:
            for center, radius in fighter.hurtboxes():
                pygame.draw.circle(surface, (80, 160, 255), center.as_ints(), round(radius), 1)
            for center, radius in fighter.hitboxes():
                pygame.draw.circle(surface, (255, 60, 60), center.as_ints(), round(radius), 1)
        for projectile in match.projectiles:
            pos, radius = projectile.pos.as_ints(), round(projectile.radius)
            pygame.draw.circle(surface, (255, 220, 60), pos, radius, 1)

    def _draw_reticle(self, surface: pygame.Surface, fighter: Fighter) -> None:
        """Where an aimed move (a grapple) would go: the cursor, held within range."""
        if fighter.cursor is None:
            return
        reach = max((m.leap for m in fighter.kit.all_moves() if m.leap_to == "cursor"), default=0)
        if reach <= 0:
            return
        offset = fighter.cursor - fighter.pos
        if offset.length() > reach:
            offset = offset.normalized() * reach
        x, y = (fighter.pos + offset).as_ints()
        color = self.fighter_defs[fighter.index].aura
        pulse = 4 + (self.tick // 8) % 2
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a = (x + dx * 2, y + dy * 2)
            b = (x + dx * (2 + pulse), y + dy * (2 + pulse))
            pygame.draw.line(surface, OUTLINE, a, b, 3)
            pygame.draw.line(surface, color, a, b, 1)

    def _strike_origin(self, fighter: Fighter) -> Vec2:
        """Where blows come from on screen: the Stand's chest if it is out, else the body."""
        view = self.fighter_views[fighter.index]
        if view.stand_presence(fighter) > 0 and view.stand is not None:
            return fighter.stand_spot() + Vec2(0, -view.stand.chest - 6)
        return fighter.pos + view.chest

    def _draw_rush(self, surface: pygame.Surface, fighter: Fighter) -> None:
        """Rushes and clashes: a flurry of fists (or thrusts) a new spread every frame."""
        if fighter.frozen:
            return
        attack = fighter.attack
        if fighter.state == State.ATTACK and attack is not None and attack.move.hits > 1:
            if not attack.active:
                return
            aim, length = attack.aim, attack.move.reach + attack.move.radius
            kind = "blade" if attack.move.fx == "blade" else "fists"
        elif fighter.state == State.CLASH:
            aim, length = fighter.facing, 26.0
            kind = "fists"
        else:
            return
        color = self.fighter_defs[fighter.index].aura
        seed = self.tick * 13 + fighter.index * 7
        origin = self._strike_origin(fighter)
        vfx.draw_flurry(surface, origin, aim, color, seed, length, 12, kind)

    def _draw_reach(self, surface: pygame.Surface, fighter: Fighter) -> None:
        """A finger, tentacle or blade stretching out while the move is active."""
        attack = fighter.attack
        if fighter.state != State.ATTACK or attack is None or not attack.move.fx:
            return
        if attack.dest is not None and attack.phase == 0:
            # A grapple: the tentacle is anchored where the user is being pulled.
            view = self.fighter_views[fighter.index]
            color = self.fighter_defs[fighter.index].aura
            start, end = fighter.pos + view.chest, attack.dest + view.chest
            vfx.draw_reach(surface, start, end, color, attack.move.fx, 2)
            return
        if not attack.active:
            return
        move = attack.move
        view = self.fighter_views[fighter.index]
        if view.stand_presence(fighter) > 0 and view.stand is not None:
            start = fighter.stand_spot() + Vec2(0, -view.stand.chest - 6)
        else:
            start = fighter.pos + view.chest
        grow = min(1.0, (attack.active_offset + 1) / 3)
        tip = fighter.pos + attack.aim * (move.reach * grow) + view.chest
        width = 3 if move.reach > 40 else 2
        vfx.draw_reach(surface, start, tip, self.fighter_defs[fighter.index].aura, move.fx, width)

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
