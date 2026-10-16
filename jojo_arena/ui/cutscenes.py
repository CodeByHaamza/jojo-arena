"""Cutscenes of the Great Heat Attacks: the fight holds while one of these plays.

Each cutscene is a short script over its frame counter: where the camera looks (centre
and an integer zoom, so pixels stay square), who stands where in which pose, which words
pop and which effects burst. The world is drawn on its own surface, then the camera
crops and enlarges it without smoothing; shouts are written over it, in screen space.
The simulation only knows how long a cutscene lasts and what lands at its end.
"""

from __future__ import annotations

import math
import random

import pygame

from jojo_arena.combat.cutscene import Cutscene
from jojo_arena.combat.match import Match
from jojo_arena.combat.traps import web_layout
from jojo_arena.engine.effects import blit_glow, blit_shadow, radial_glow
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.sprites import frame_index
from jojo_arena.ui import sfx, text, vfx

SCREEN = (480, 270)
OUTLINE = (23, 18, 31)
BARS = 22  # letterbox height
LIGHT = (255, 255, 255)


class CutscenePlayer:
    """What all cutscenes share: the camera, the words, the effects, the letterbox."""

    length = 1

    def __init__(self, view, match: Match, scene: Cutscene) -> None:
        self.view = view  # the FightView: stage renderer, fighter views and defs
        self.match = match
        self.scene = scene
        self.user = match.fighters[scene.user]
        self.target = match.fighters[scene.target]
        self.u = self.user.pos.copy()
        self.v = self.target.pos.copy()
        self.side = 1 if self.v.x >= self.u.x else -1  # +1: the user faces right
        self.world = pygame.Surface(SCREEN)
        self.world_words = sfx.SfxLayer(seed=scene.serial)
        self.words = sfx.SfxLayer(seed=scene.serial + 1)
        self.fx = vfx.EffectsLayer()
        self.rng = random.Random(scene.serial)
        self.center = (self.u + self.v) * 0.5
        self.zoom = 2
        self.flash = 0
        self.shake = 0
        self.frame = 0

    # Script hooks -----------------------------------------------------------------------

    def cue(self, f: int) -> None:
        """Called once per frame: start words and effects."""

    def camera(self, f: int) -> tuple[Vec2, int]:
        return (self.u + self.v) * 0.5, 2

    def negative(self, f: int) -> bool:
        return False

    def scene_draw(self, world: pygame.Surface, f: int) -> None:
        """Draw the characters and props of this frame on the world surface."""

    # Running ----------------------------------------------------------------------------

    def update(self, frame: int) -> None:
        while self.frame < frame:
            self.frame += 1
            self.cue(self.frame)
            self.world_words.update()
            self.words.update()
            self.fx.update()
            self.flash = max(0, self.flash - 1)
            self.shake = max(0, self.shake - 1)
            target, zoom = self.camera(self.frame)
            if zoom != self.zoom:
                self.center, self.zoom = target, zoom  # a cut
            else:
                self.center = self.center + (target - self.center) * 0.25

    def draw(self, surface: pygame.Surface) -> None:
        f = self.frame
        world = self.world
        renderer = self.view.renderer
        renderer.draw_background(world)
        renderer.draw_floor_details(world, self.match.arena)
        for obstacle in self.match.arena.obstacles:
            if not obstacle.broken:
                renderer.draw_obstacle(world, obstacle)
        self.scene_draw(world, f)
        self.fx.draw(world)
        self.world_words.draw(world)
        self._apply_camera(world, surface)
        if self.negative(f):
            negative = surface.copy()
            surface.fill(LIGHT)
            surface.blit(negative, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
        self.words.draw(surface)
        self._letterbox(surface, f)
        if self.flash:
            layer = pygame.Surface(SCREEN, pygame.SRCALPHA)
            layer.fill((255, 255, 255, min(255, 40 * self.flash)))
            surface.blit(layer, (0, 0))
        if self.shake:
            amplitude = 1 + min(3, self.shake // 4)
            surface.scroll(self.rng.randint(-amplitude, amplitude), self.rng.randint(-1, 1))

    def _apply_camera(self, world: pygame.Surface, surface: pygame.Surface) -> None:
        zoom = self.zoom
        width, height = SCREEN[0] // zoom, SCREEN[1] // zoom
        x = round(min(max(self.center.x - width / 2, 0), SCREEN[0] - width))
        y = round(min(max(self.center.y - height / 2, 0), SCREEN[1] - height))
        view = world.subsurface((x, y, width, height))
        if zoom == 1:
            surface.blit(view, (0, 0))
        else:
            surface.blit(pygame.transform.scale(view, SCREEN), (0, 0))

    def _letterbox(self, surface: pygame.Surface, f: int) -> None:
        grow = min(1.0, f / 8, (self.length - f) / 8)
        bar = round(BARS * max(0.0, grow))
        if bar:
            surface.fill((0, 0, 0), (0, 0, SCREEN[0], bar))
            surface.fill((0, 0, 0), (0, SCREEN[1] - bar, SCREEN[0], bar))

    # Drawing helpers ------------------------------------------------------------------

    def fighter_view(self, index: int):
        return self.view.fighter_views[index]

    def aura(self, index: int):
        return self.view.fighter_defs[index].aura

    def body(
        self,
        world: pygame.Surface,
        index: int,
        pos: Vec2,
        anim: str,
        frame: int,
        face_right: bool,
        lift: float = 0.0,
        stand: bool = False,
        alpha: int = 255,
        shadow: bool = True,
    ) -> None:
        """A fighter (or its Stand) at `pos` on the ground, `lift` px above it."""
        from jojo_arena.ui.fight_view import FighterView

        view = self.fighter_view(index)
        sprites = view.stand if stand and view.stand is not None else view.sprites
        if shadow and not stand:
            blit_shadow(world, (pos.x, pos.y), *view.shadow)
        name, spec = FighterView.resolve(sprites, anim)
        image = sprites.frame(name, "right", not face_right, min(frame, spec.frames - 1))
        if alpha != 255:
            image = image.copy()
            image.set_alpha(alpha)
        ax, ay = sprites.anchor
        if not face_right:
            ax = image.get_width() - 1 - ax
        world.blit(image, (round(pos.x) - ax, round(pos.y - lift) - ay))

    def idle_frame(self, index: int, f: int) -> int:
        spec = self.fighter_view(index).sprites.spec("idle")
        return frame_index(spec, f) if spec else 0

    def chest(self, index: int, pos: Vec2, stand: bool = False, lift: float = 0.0) -> Vec2:
        view = self.fighter_view(index)
        sprites = view.stand if stand and view.stand is not None else view.sprites
        return pos + Vec2(0, -sprites.chest - lift)

    def head(self, index: int, pos: Vec2, lift: float = 0.0) -> Vec2:
        return pos + Vec2(0, -self.fighter_view(index).height - lift - 6)

    def shout(self, text: str, f_pos: tuple[int, int] = (240, 52), scale: int = 3, life=50):
        style = sfx.shout_style(self.aura(self.scene.user))
        self.words.add(text, Vec2(*f_pos), style, scale, life, 0.1, 2)

    def caption(self, text: str, life: int = 40) -> None:
        self.words.add(text, Vec2(240, 135), "white", 2, life, 0.0, 0)

    def victim(self, world: pygame.Surface, f: int, pos: Vec2 | None = None) -> None:
        """The target, frozen in a hurt pose, trembling."""
        pos = pos or self.v
        jitter = Vec2(self.rng.choice((-1, 0, 1)), 0) if f % 4 < 2 else Vec2()
        self.body(world, self.scene.target, pos + jitter, "hurt", 0, self.side < 0)


# DIO: Road Roller ------------------------------------------------------------------------


def draw_road_roller(surface: pygame.Surface, foot: Vec2, face_right: bool, crack: float):
    """A road roller seen from the side, bottom centre at `foot`. Generic heavy machinery,
    drawn in the game's style: dark outline, three tones, a highlight."""
    x, y = round(foot.x), round(foot.y)
    d = 1 if face_right else -1
    yellow, yellow_dark, yellow_light = (232, 184, 58), (172, 122, 30), (255, 226, 120)
    steel, steel_dark, steel_light = (138, 140, 152), (84, 86, 100), (196, 198, 210)
    body = pygame.Rect(0, 0, 46, 20)
    body.midbottom = (x - d * 4, y - 8)
    cab = pygame.Rect(0, 0, 18, 15)
    cab.bottomleft = (body.left + 3, body.top) if d > 0 else (body.right - 21, body.top)
    drum = pygame.Rect(0, 0, 22, 20)
    drum.midbottom = (x + d * 18, y)
    wheel = (x - d * 16, y - 8)
    for rect in (body, cab, drum):
        pygame.draw.rect(surface, OUTLINE, rect.inflate(2, 2), border_radius=3)
    pygame.draw.circle(surface, OUTLINE, wheel, 10)
    pygame.draw.rect(surface, yellow, body, border_radius=2)
    surface.fill(yellow_dark, (body.x, body.bottom - 6, body.w, 6))
    surface.fill(yellow_light, (body.x + 2, body.y + 1, body.w - 4, 2))
    pygame.draw.rect(surface, yellow, cab, border_radius=2)
    surface.fill((40, 40, 60), cab.inflate(-6, -6))
    surface.fill(yellow_light, (cab.x + 1, cab.y + 1, cab.w - 2, 1))
    pygame.draw.rect(surface, steel, drum, border_radius=5)
    for band in range(drum.x + 3, drum.right - 2, 5):
        surface.fill(steel_dark, (band, drum.y + 2, 1, drum.h - 4))
    surface.fill(steel_light, (drum.x + 2, drum.y + 2, drum.w - 4, 2))
    pygame.draw.circle(surface, (40, 38, 46), wheel, 9)
    pygame.draw.circle(surface, steel_dark, wheel, 4)
    surface.fill(OUTLINE, (body.centerx - d * 10 - 1, body.top - 9, 4, 9))
    if crack > 0:
        rng = random.Random(7)
        for _ in range(round(crack * 9)):
            sx = rng.randint(body.left + 3, body.right - 3)
            sy = rng.randint(body.top + 2, body.bottom - 3)
            ex, ey = sx + rng.randint(-7, 7), sy + rng.randint(-5, 5)
            pygame.draw.line(surface, OUTLINE, (sx, sy), (ex, ey), 1)


class RoadRoller(CutscenePlayer):
    length = 330

    def camera(self, f):
        v = self.v
        if f < 22:
            return (self.u + v) * 0.5, 2
        if f < 70:
            return Vec2(240, 140), 1
        if f < 108:
            return v + Vec2(0, -20), 2
        if f < 160:
            return Vec2(v.x, v.y - 50), 1
        if f < 262:
            return v + Vec2(0, -24), 2
        if f < 292:
            return Vec2(240, 140), 1
        return v + Vec2(0, -20), 2

    def negative(self, f):
        return 34 <= f < 262

    def cue(self, f):
        v, u, words, fx = self.v, self.u, self.world_words, self.fx
        hit = self.chest(self.scene.target, v)
        if f == 1:
            words.add(sfx.DON, self.head(self.scene.target, v), "impact", 2, 30, 0.3, 1)
            fx.add(vfx.Flash(hit, 18))
            fx.focus(hit, heavy=True)
            self.shake = 10
        if f == 24:
            self.shout("ZA WARUDO !")
        if 30 <= f <= 56 and f % 6 == 0:
            fx.add(vfx.Ring(self.chest(self.scene.user, u), (255, 236, 160), 7.0, 40, 2))
        if f == 40:
            self.words.add(sfx.DODODO, Vec2(120, 220), "menace", 2, 40, 0.3, 1)
        if f == 72:
            self.shout("WRYYYYY !", (240, 60))
        if 72 <= f < 100 and f % 3 == 0:
            fx.add(vfx.SpeedLines(self.chest(self.scene.user, u, lift=(f - 70) * 7), Vec2(0, -1)))
        if f == 110:
            self.shout("ROAD ROLLER DA !", (240, 60), 3, 60)
        if f == 160:
            words.add(sfx.DOGO, v + Vec2(0, -40), "impact", 3, 40, 0.3, 2)
            fx.dust(v, 16, 2.4, 5)
            fx.add(vfx.Ring(v + Vec2(0, -10), (255, 230, 170), 4.0, 18, 3))
            self.flash, self.shake = 6, 16
        if f == 180:
            self.words.add(sfx.DODODO, Vec2(360, 220), "menace", 2, 60, 0.2, 1)
        if 178 <= f < 262 and f % 4 == 0:
            style = sfx.shout_style(self.aura(self.scene.user))
            spot = Vec2(240 + self.rng.uniform(-150, 150), self.rng.uniform(60, 210))
            self.words.add("MUDA", spot, style, self.rng.choice((2, 2, 3)), 22, 0.6, 1)
            self.shake = max(self.shake, 3)
        if f == 262:
            self.flash = 8
        if f == 266:
            self.caption("... ET LE TEMPS REPREND SON COURS")
        if f == 292:
            center = v + Vec2(0, -14)
            for speed, life in ((3.0, 24), (5.0, 30), (7.5, 36)):
                fx.add(vfx.Ring(center, (255, 200, 120), speed, life, 3))
            fx.add(vfx.Flash(center, 60, (255, 210, 140), 16))
            fx.dust(v, 24, 3.2, 6, (120, 100, 90), 30)
            words.add(sfx.BAAN, center + Vec2(0, -20), "ko", 4, 40, 0.2, 2)
            self.flash, self.shake = 10, 24

    def roller_height(self, f: int) -> float:
        t = min(1.0, max(0.0, (f - 108) / 52))
        return 320 * (1 - t) ** 2

    def scene_draw(self, world, f):
        u, v = self.u, self.v
        dio = self.scene.user
        right = self.side > 0
        if f < 70:
            # The opening blow, then the time stop pose.
            anim, frame = ("light", 2) if f < 22 else ("pose", f // 20)
            self.victim(world, f)
            self.body(world, dio, u, anim, frame, right)
            stand_at = u + Vec2(self.side * 13, -6) if f < 22 else u + Vec2(-self.side * 10, -8)
            self.body(world, dio, stand_at, anim, frame, right, stand=True, alpha=220)
            return
        if f < 108:
            self.victim(world, f)
            lift = (f - 70) * 7
            self.body(world, dio, u, "leap", 1, right, lift=lift, shadow=lift < 40)
            return
        if f < 292:
            height = self.roller_height(f)
            self.victim(world, f)
            if f < 160:
                # Its shadow grows on the frozen victim as the road roller falls.
                size = round(14 + 30 * (1 - height / 320))
                blit_shadow(world, (v.x, v.y), size * 2, max(4, size // 2))
            jitter = Vec2(self.rng.randint(-1, 1), 0) if f >= 178 else Vec2()
            foot = v + jitter + Vec2(0, -height)
            crack = max(0.0, (f - 178) / 84) if f >= 178 else 0.0
            draw_road_roller(world, foot, right, crack)
            top = foot + Vec2(-self.side * 4, -26)
            if f < 262:
                punch = 1 + (f // 3) % 2 if f >= 178 else 0
                anim = "light" if f >= 178 else "idle"
                self.body(world, dio, top, anim, punch, right, shadow=False)
                if f >= 178:
                    stand_at = top + Vec2(-self.side * 8, -10)
                    self.body(world, dio, stand_at, "light", punch, right, stand=True, alpha=220)
                    chest = self.chest(dio, stand_at, stand=True)
                    aura = self.aura(dio)
                    vfx.draw_flurry(world, chest, Vec2(self.side * 0.3, 1), aura, f * 13, 30, 14)
            else:
                # Time moves again: DIO springs off the road roller.
                t = (f - 262) / 30
                spot = top + (u - top) * t
                lift = math.sin(math.pi * t) * 30
                self.body(world, dio, spot, "leap", 2, right, lift=lift, shadow=False)
            return
        self.victim(world, f)
        self.body(world, dio, u, "pose", 0, right)


# Jotaro: Ora Ora final --------------------------------------------------------------------


class StarFinish(CutscenePlayer):
    length = 276

    def camera(self, f):
        v, side = self.v, self.side
        if f < 20:
            return (self.u + v) * 0.5, 2
        if f < 60:
            return Vec2(240, 140), 1
        if 200 <= f < 214:
            return v + Vec2(0, -16), 3
        if f < 224:
            return v - Vec2(side * 18, 20), 2
        if f < 250:
            return Vec2(240, 140), 1
        return v + Vec2(0, -16), 2

    def negative(self, f):
        return 30 <= f < 224

    def cue(self, f):
        v, fx = self.v, self.fx
        hit = self.chest(self.scene.target, v)
        user = self.scene.user
        if f == 1:
            self.world_words.add(sfx.DON, self.head(self.scene.target, v), "impact", 2, 30)
            fx.add(vfx.Flash(hit, 18))
            fx.focus(hit, heavy=True)
            self.shake = 10
        if f == 22:
            self.shout("STAR PLATINUM : THE WORLD !", (240, 52), 2, 60)
        if 30 <= f <= 50 and f % 6 == 0:
            fx.add(vfx.Ring(self.chest(user, self.u), (200, 180, 255), 7.0, 40, 2))
        if 60 <= f < 196:
            if f % 4 == 0:
                style = sfx.shout_style(self.aura(user))
                spot = Vec2(240 + self.rng.uniform(-170, 170), self.rng.uniform(50, 220))
                self.words.add("ORA", spot, style, self.rng.choice((2, 2, 3)), 22, 0.6, 1)
            if f % 8 == 0:
                fx.focus(hit, heavy=True)
                fx.add(vfx.Flash(hit, 10))
            self.shake = max(self.shake, 2)
        if f == 196:
            self.shout("ORAAAAA !", (240, 60), 4, 50)
        if f == 200:
            fx.add(vfx.Flash(hit, 30))
            fx.add(vfx.Ring(hit, (255, 255, 255), 4.0, 20, 3))
            self.world_words.add(sfx.DOGO, hit + Vec2(0, -14), "impact", 3, 50, 0.2, 2)
            self.flash, self.shake = 8, 16
        if f == 224:
            self.flash = 8
        if f == 228:
            self.caption("... ET LE TEMPS REPREND SON COURS")
        if f == 252:
            fx.add(vfx.Ring(hit, (255, 230, 170), 5.0, 22, 3))
            fx.dust(v, 14, 2.4, 5)
            self.shake = 14

    def scene_draw(self, world, f):
        u, v, side = self.u, self.v, self.side
        jotaro = self.scene.user
        right = side > 0
        self.victim(world, f)
        if f < 20:
            self.body(world, jotaro, u, "light", 2, right)
            self.body(world, jotaro, u + Vec2(side * 13, -6), "light", 2, right, stand=True)
            return
        if f < 60:
            self.body(world, jotaro, u, "pose", f // 20, right)
            stand_at = u + Vec2(-side * 10, -8)
            self.body(world, jotaro, stand_at, "pose", f // 20, right, stand=True, alpha=220)
            return
        self.body(world, jotaro, v - Vec2(side * 44, 0), "pose", 0, right)
        stand_at = v - Vec2(side * 20, 0) + Vec2(0, -6)
        if f < 196:
            punch = 1 + (f // 2) % 2
            self.body(world, jotaro, stand_at, "light", punch, right, stand=True)
            chest = self.chest(jotaro, stand_at, stand=True)
            aura = self.aura(jotaro)
            vfx.draw_flurry(world, chest, Vec2(side, 0), aura, f * 17, 30, 18, size=1)
            vfx.draw_flurry(world, chest + Vec2(0, 6), Vec2(side, 0), aura, f * 19, 26, 10)
        else:
            self.body(world, jotaro, stand_at, "uppercut", 2, right, stand=True)


# Polnareff: the clones of Armor Off ---------------------------------------------------------


class ChariotClones(CutscenePlayer):
    length = 240
    CLONES = 6

    def camera(self, f):
        if f < 20:
            return (self.u + self.v) * 0.5, 2
        if f < 56:
            return self.u + Vec2(0, -16), 2
        return self.v + Vec2(0, -16), 2

    def cue(self, f):
        v, fx, user = self.v, self.fx, self.scene.user
        hit = self.chest(self.scene.target, v)
        if f == 1:
            self.world_words.add(sfx.DON, self.head(self.scene.target, v), "impact", 2, 30)
            fx.add(vfx.Flash(hit, 16))
            fx.focus(hit, heavy=True)
            self.shake = 8
        if f == 22:
            self.shout("ARMOR OFF !", (240, 56), 3, 50)
            chest = self.chest(user, self.u + Vec2(-self.side * 10, -8), stand=True)
            fx.dust(chest, 14, 2.6, 2, (196, 200, 214), 26)  # shards of armor
            fx.add(vfx.Flash(chest, 24))
        if 56 <= f < 190 and f % 3 == 0:
            fx.add(vfx.Flash(hit, 9))
            if f % 6 == 0:
                style = sfx.shout_style(self.aura(user))
                spot = Vec2(240 + self.rng.uniform(-160, 160), self.rng.uniform(50, 220))
                self.words.add("ORA", spot, style, self.rng.choice((2, 2, 3)), 22, 0.6, 1)
            self.shake = max(self.shake, 2)
        if f == 190:
            self.shout("ORA ORA ORA !", (240, 60), 4, 40)
        if f == 196:
            fx.add(vfx.Flash(hit, 34))
            fx.add(vfx.Ring(hit, (230, 236, 255), 4.0, 22, 3))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.DOGO, hit + Vec2(0, -14), "impact", 3, 44, 0.2, 2)
            self.flash, self.shake = 8, 16

    def clone_spots(self, f: int) -> list[Vec2]:
        """The afterimages stand in a ring around the victim, turning slowly."""
        spin = f * 0.02
        spots = []
        for i in range(self.CLONES):
            angle = spin + i * math.tau / self.CLONES
            spots.append(self.v + Vec2(math.cos(angle) * 34, math.sin(angle) * 18))
        return spots

    def scene_draw(self, world, f):
        u, v, side = self.u, self.v, self.side
        pol = self.scene.user
        right = side > 0
        hit = self.chest(self.scene.target, v)
        if f < 56:
            self.victim(world, f)
            self.body(world, pol, u, "light" if f < 20 else "pose", 1, right)
            stand_at = u + Vec2(side * 13, -6) if f < 20 else u + Vec2(-side * 10, -8)
            self.body(world, pol, stand_at, "light", 2 if f < 20 else 0, right, stand=True)
            if f < 20:
                tip = hit
                start = self.chest(pol, stand_at, stand=True)
                vfx.draw_reach(world, start, tip, self.aura(pol), "blade", 2)
            return
        spots = self.clone_spots(f)
        behind = [s for s in spots if s.y < v.y]
        front = [s for s in spots if s.y >= v.y]
        fading = f >= 215
        alpha = 150 if not fading else max(0, round(150 * (240 - f) / 25))
        all_strike = 190 <= f < 215
        for group, victim_next in ((behind, True), (front, False)):
            for spot in group:
                facing = v.x >= spot.x
                striking = all_strike or (f // 3) % self.CLONES == spots.index(spot)
                anim, frame = ("light", 2) if striking else ("idle", 0)
                self.body(world, pol, spot, anim, frame, facing, stand=True, alpha=alpha)
                if striking and not fading:
                    start = self.chest(pol, spot, stand=True)
                    vfx.draw_reach(world, start, hit, self.aura(pol), "blade", 2)
            if victim_next:
                self.victim(world, f)


# Kakyoin: Emerald Splash, 20 metres ------------------------------------------------------


class HierophantWeb(CutscenePlayer):
    length = 156

    def __init__(self, view, match, scene):
        super().__init__(view, match, scene)
        self.nodes, self.edges = web_layout(match.arena.bounds.rect, scene.move.web)
        columns = scene.move.web.columns
        # Hierophant runs the rows in a snake, anchoring a thread at every point.
        order = []
        for row in range(scene.move.web.rows):
            cols = range(columns) if row % 2 == 0 else range(columns - 1, -1, -1)
            order += [row * columns + c for c in cols]
        self.path = order

    def camera(self, f):
        if f < 24:
            return self.u + Vec2(0, -16), 2
        return Vec2(240, 140), 1

    def progress(self, f: int) -> float:
        """How far along its path Hierophant is: 0 at the first anchor, 1 at the last."""
        return min(1.0, max(0.0, (f - 24) / 96))

    def visited(self, f: int) -> int:
        return 1 + int(self.progress(f) * (len(self.path) - 1))

    def cue(self, f):
        user, fx = self.scene.user, self.fx
        if f == 2:
            aura = self.aura(user)
            fx.add(vfx.Ring(self.chest(user, self.u), aura, 3.0, 20, 2))
            self.words.add("HIEROPHANT GREEN !", Vec2(240, 56), sfx.shout_style(aura), 2, 40)
        if f in (6, 14):
            self.world_words.menace(self.chest(user, self.u), 1 if f == 6 else -1)
        if 24 <= f < 120 and f % 5 == 0:
            spot = self.hierophant_spot(f)
            fx.add(vfx.Flash(spot + Vec2(0, -10), 8, self.aura(user), 8))
        if f == 122:
            self.shout("EMERALD SPLASH : 20 METRES !", (240, 56), 2, 40)
            self.flash = 4

    def hierophant_spot(self, f: int) -> Vec2:
        path = [self.nodes[i] for i in self.path]
        t = self.progress(f) * (len(path) - 1)
        i = min(len(path) - 2, int(t))
        return path[i] + (path[i + 1] - path[i]) * (t - i)

    def scene_draw(self, world, f):
        user = self.scene.user
        aura = self.aura(user)
        right = self.side > 0
        visited = set(self.path[: self.visited(f)]) if f >= 24 else set()
        for a, b in self.edges:
            if a in visited and b in visited:
                vfx.draw_thread(world, self.nodes[a], self.nodes[b], aura, f)
        for i in visited:
            vfx.draw_projectile(world, "gem", self.nodes[i] + Vec2(0, -2), Vec2(0, -1), 3, aura)
        self.victim(world, f)
        self.body(world, user, self.u, "pose", f // 20, right)
        if f < 24:
            stand_at = self.u + Vec2(-self.side * 10, -8)
            self.body(world, user, stand_at, "pose", 0, right, stand=True, alpha=220)
        elif f < 120:
            spot = self.hierophant_spot(f)
            last = self.nodes[self.path[self.visited(f) - 1]]
            vfx.draw_thread(world, last, spot, aura, f)
            self.body(world, user, spot, "dash", 0, spot.x >= last.x, stand=True, alpha=220)


# Kakyoin: Hierophant inside -------------------------------------------------------------


class HierophantInside(CutscenePlayer):
    """Hierophant unravels into a ribbon, slips into the victim's mouth, and the victim
    convulses until the emeralds burst out of them."""

    length = 144

    def camera(self, f):
        if f < 18:
            return (self.u + self.v) * 0.5, 2
        if f < 110:
            return self.v + Vec2(0, -18), 3 if 60 <= f < 70 else 2
        return self.v + Vec2(0, -24), 2

    def cue(self, f):
        v, fx, user = self.v, self.fx, self.scene.user
        aura = self.aura(user)
        hit = self.chest(self.scene.target, v)
        mouth = self.head(self.scene.target, v) + Vec2(0, 8)
        if f == 1:
            fx.add(vfx.Flash(hit, 14, aura))
            fx.focus(hit, heavy=False)
            self.shake = 6
        if f == 22:
            self.world_words.menace(hit, 1)
        if f == 50:
            self.shout(text.PUNISHMENT_TIME, (240, 56), 2, 50)
        if 56 <= f < 110 and f % 18 == 0:
            spot = mouth + Vec2(self.rng.uniform(-8, 8), -10)
            style = sfx.shout_style(aura)
            self.world_words.add(sfx.HEARTBEAT, spot, style, 2, 20, 0.3, 2)
            fx.add(vfx.Flash(hit, 16, aura, 8))
            self.shake = 5
        if f == 110:
            fx.add(vfx.Flash(hit, 40, (180, 255, 200), 14))
            for speed, life in ((2.5, 18), (4.0, 24)):
                fx.add(vfx.Ring(hit, aura, speed, life, 3))
            self.world_words.add(sfx.BAAN, mouth + Vec2(0, -14), "impact", 3, 40, 0.3, 2)
            self.flash, self.shake = 8, 16

    def scene_draw(self, world, f):
        u, v, side = self.u, self.v, self.side
        user, target = self.scene.user, self.scene.target
        right = side > 0
        aura = self.aura(user)
        mouth = self.head(target, v) + Vec2(0, 8)
        self.body(world, user, u, "special" if f < 50 else "pose", 1, right)
        hg_spot = u + Vec2(side * 18, -8)
        lift = 0.0
        if f < 110:
            jolt = Vec2(self.rng.randint(-2, 2), self.rng.randint(-1, 1)) if f >= 56 else Vec2()
            self.body(world, target, v + jolt, "hurt", (f // 5) % 2, not right)
        else:
            lift = min(30.0, (f - 110) * 2.5)
            self.body(world, target, v, "hurt", 1, not right, lift=lift)
        if f < 18:
            # The tentacles have caught the victim from above.
            self.body(world, user, hg_spot, "special", 2, right, stand=True, alpha=220)
            start = self.chest(user, hg_spot, stand=True)
            for bend in (-10, 0, 10):
                high = (start + mouth) * 0.5 + Vec2(bend, -24)
                vfx.draw_reach(world, start, high, aura, "tentacle", 1)
                vfx.draw_reach(world, high, self.chest(target, v), aura, "tentacle", 1)
        elif f < 56:
            # Hierophant unravels into a ribbon that slips into the victim's mouth.
            t = (f - 18) / 38
            alpha = max(0, round(220 * (1 - t)))
            self.body(world, user, hg_spot, "dash", 0, right, stand=True, alpha=alpha)
            start = self.chest(user, hg_spot, stand=True)
            tip = start + (mouth - start) * min(1.0, t * 1.3)
            vfx.draw_reach(world, start, tip, aura, "tentacle", 2)
        elif f < 110:
            # Inside: a green light throbs in the victim's chest.
            pulse = 0.5 + 0.5 * math.sin(f * 0.35)
            glow = tuple(round(c * (0.3 + 0.5 * pulse)) for c in aura)
            blit_glow(world, radial_glow(12, glow), self.chest(target, v))
        else:
            # The emeralds burst out of the victim.
            t = f - 110
            center = self.chest(target, v, lift=lift)
            for i in range(12):
                direction = Vec2.from_angle(i * math.tau / 12 + 0.3)
                gem = center + direction * (6 + t * 3.2)
                vfx.draw_projectile(world, "gem", gem, direction, 3, aura)


# Jonathan: Sunlight Yellow Overdrive -----------------------------------------------------

HAMON_GOLD = (255, 214, 80)


class SunlightYellowOverdrive(CutscenePlayer):
    """The Hamon fist landed: Jonathan breathes in, the Hamon blazes in his fists like the
    sun, then the barrage, and the last blow sends the sunlight through the opponent."""

    length = 216
    BREATH_END = 66
    FINAL = 168

    def camera(self, f):
        if f < 16:
            return (self.u + self.v) * 0.5, 2
        if f < self.BREATH_END:
            return self.u + Vec2(0, -24), 2
        return (self.u + self.v) * 0.5 + Vec2(0, -12), 2

    def puncher(self) -> Vec2:
        """Where Jonathan stands to punch: right up against the opponent."""
        return self.v - Vec2(self.side * 20, 0)

    def cue(self, f):
        fx, user = self.fx, self.scene.user
        hit = self.chest(self.scene.target, self.v)
        if f == 1:
            self.world_words.add(sfx.DON, self.head(self.scene.target, self.v), "impact", 2, 30)
            fx.add(vfx.Flash(hit, 16, HAMON_GOLD))
            fx.focus(hit, heavy=True)
            self.shake = 8
        if 16 <= f < self.BREATH_END and f % 8 == 0:
            chest = self.chest(user, self.u)
            fx.add(vfx.Ring(chest, HAMON_GOLD, 1.8, 20, 1))
            fx.add(vfx.Flash(chest + Vec2(self.side * 8, 2), 10, HAMON_GOLD, 6))
        if f == 20:
            self.world_words.add(sfx.BREATH, self.head(user, self.u), sfx.HAMON, 2, 46, 0.3)
        if f == 30:
            self.shout("SUNLIGHT YELLOW", (240, 50), 3, 60)
        if f == 50:
            self.shout("OVERDRIVE !!", (240, 78), 4, 60)
        if self.BREATH_END <= f < self.FINAL and f % 3 == 0:
            spot = hit + Vec2(self.rng.uniform(-8, 8), self.rng.uniform(-10, 8))
            fx.add(vfx.Flash(spot, 10, HAMON_GOLD, 5))
            if f % 9 == 0:
                style = sfx.HAMON
                where = Vec2(240 + self.rng.uniform(-170, 170), self.rng.uniform(46, 224))
                self.words.add("OVERDRIVE", where, style, self.rng.choice((2, 2, 3)), 22, 0.6, 1)
            if f % 12 == 0:
                fx.add(vfx.Ring(hit, HAMON_GOLD, 2.8, 14, 2))
            self.shake = max(self.shake, 2)
        if f == self.FINAL:
            fx.add(vfx.Flash(hit, 44, HAMON_GOLD, 14))
            fx.add(vfx.Ring(hit, HAMON_GOLD, 4.5, 24, 3))
            fx.add(vfx.Ring(hit, (255, 250, 220), 3.0, 20, 2))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.DOGO, hit + Vec2(0, -14), "impact", 3, 46, 0.2, 2)
            self.flash, self.shake = 9, 18
        if f > self.FINAL and f % 7 == 0:
            spot = hit + Vec2(self.rng.uniform(-10, 10), self.rng.uniform(-12, 8))
            self.world_words.add(sfx.CRACKLE, spot, sfx.HAMON, 2, 20, 0.5, 1)
            fx.add(vfx.Flash(spot, 12, HAMON_GOLD, 6))

    def negative(self, f):
        return self.FINAL <= f < self.FINAL + 3  # the impact frames

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        hit = self.chest(self.scene.target, self.v)
        if f < self.BREATH_END:
            self.victim(world, f)
            anim, frame = ("heavy_overdrive", 2) if f < 16 else ("breathe", (f // 10) % 2)
            self.body(world, user, self.u, anim, frame, right)
            if f >= 16:
                # Hamon gathering in his fists: a glow that grows like a small sun.
                chest = self.chest(user, self.u) + Vec2(self.side * 7, 4)
                glow = 10 + min(14, (f - 16) // 3)
                blit_glow(world, radial_glow(glow, (150, 110, 20)), (chest.x, chest.y))
            return
        spot = self.puncher()
        if f < self.FINAL:
            frame = 1 + (f // 3) % 2
            self.victim(world, f)
            self.body(world, user, spot, "light", frame, right)
            vfx.draw_flurry(
                world,
                self.chest(user, spot),
                Vec2(self.side, 0),
                HAMON_GOLD,
                f * 13,
                30,
                8,
                "fists",
            )
        else:
            knocked = self.v + Vec2(self.side * min(30, (f - self.FINAL) * 3), 0)
            self.body(world, self.scene.target, knocked, "hurt", 1, self.side < 0)
            self.body(world, user, spot, "heavy_overdrive", 3, right)
            blit_glow(world, radial_glow(20, (140, 100, 20)), (hit.x, hit.y))


# Zeppeli: Tornado Overdrive ---------------------------------------------------------------


class TornadoOverdrive(CutscenePlayer):
    """The kick landed: Zeppeli spins up into the air in a whirl of Hamon, then dives
    heel first onto the opponent, and the ripples go through them."""

    length = 180
    RISE_END = 70
    DIVE_END = 94

    def camera(self, f):
        if f < 16:
            return (self.u + self.v) * 0.5, 2
        if f < self.RISE_END:
            return self.u + Vec2(0, -40), 2
        return self.v + Vec2(0, -22), 2

    def lift(self, f) -> float:
        if f < 16:
            return 0.0
        if f < self.RISE_END:
            return min(44.0, (f - 16) * 1.3)
        if f < self.DIVE_END:
            return 44.0 * (1 - (f - self.RISE_END) / (self.DIVE_END - self.RISE_END))
        return 0.0

    def spot(self, f) -> Vec2:
        if f < self.RISE_END:
            return self.u
        if f < self.DIVE_END:
            t = (f - self.RISE_END) / (self.DIVE_END - self.RISE_END)
            return self.u + (self.v - Vec2(self.side * 12, 0) - self.u) * t
        return self.v - Vec2(self.side * 22, 0)

    def cue(self, f):
        fx, user = self.fx, self.scene.user
        hit = self.chest(self.scene.target, self.v)
        if f == 1:
            self.world_words.add(sfx.DON, self.head(self.scene.target, self.v), "impact", 2, 30)
            fx.add(vfx.Flash(hit, 16, HAMON_GOLD))
            fx.focus(hit, heavy=True)
            self.shake = 8
        if 16 <= f < self.RISE_END and f % 6 == 0:
            chest = self.chest(user, self.u, lift=self.lift(f))
            fx.add(vfx.Ring(chest, HAMON_GOLD, 2.0, 16, 1))
        if f == 24:
            self.shout("TORNADO", (240, 52), 4, 56)
        if f == 46:
            self.shout("OVERDRIVE !", (240, 84), 4, 56)
        if f == self.RISE_END:
            direction = (self.v - self.u).normalized()
            fx.add(vfx.SpeedLines(self.chest(user, self.u, lift=40), direction, HAMON_GOLD, 14))
        if f == self.DIVE_END:
            fx.add(vfx.Flash(hit, 42, HAMON_GOLD, 14))
            fx.add(vfx.Ring(hit, HAMON_GOLD, 4.5, 24, 3))
            fx.focus(hit, heavy=True)
            fx.dust(self.v, 12, 2.0, 2)
            self.world_words.add(sfx.DOGO, hit + Vec2(0, -14), "impact", 3, 46, 0.2, 2)
            self.flash, self.shake = 9, 18
        if f > self.DIVE_END and f % 8 == 0:
            fx.add(vfx.Ring(hit, HAMON_GOLD, 2.4, 16, 2))
            spot = hit + Vec2(self.rng.uniform(-10, 10), self.rng.uniform(-12, 8))
            self.world_words.add(sfx.CRACKLE, spot, sfx.HAMON, 2, 20, 0.5, 1)

    def negative(self, f):
        return self.DIVE_END <= f < self.DIVE_END + 3

    def scene_draw(self, world, f):
        user = self.scene.user
        lift, spot = self.lift(f), self.spot(f)
        if f < self.DIVE_END:
            self.victim(world, f)
            # Spinning: he turns around every few frames as he rises.
            facing = self.side > 0 if f < 16 or f >= self.RISE_END else (f // 4) % 2 == 0
            frame = 2 if f >= self.RISE_END else 1
            self.body(world, user, spot, "kick_high", frame, facing, lift=lift)
            if 16 <= f < self.DIVE_END:
                center = self.chest(user, spot, lift=lift)
                for i in range(3):
                    angle = f * 0.5 + i * math.tau / 3
                    a = center + Vec2(math.cos(angle) * 14, math.sin(angle) * 6)
                    b = center + Vec2(math.cos(angle + 0.9) * 14, math.sin(angle + 0.9) * 6)
                    pygame.draw.line(world, HAMON_GOLD, a.as_ints(), b.as_ints(), 2)
            return
        knocked = self.v + Vec2(self.side * min(26, (f - self.DIVE_END) * 2), 0)
        self.body(world, self.scene.target, knocked, "hurt", 1, self.side < 0)
        self.body(world, user, spot, "pose", 0, self.side > 0)


# Dio Brando: Absorption ------------------------------------------------------------------

BLOOD_RED = (210, 24, 48)


class Absorption(CutscenePlayer):
    """The grab took hold: Dio's fingers sink into the opponent's neck and he drinks, the
    heart pounding, the blood streaming up his arm, until he lets the body drop."""

    length = 192
    RELEASE = 172

    def camera(self, f):
        if f < 14:
            return (self.u + self.v) * 0.5, 2
        return (self.u + self.v) * 0.5 + Vec2(0, -18), 2

    def grip(self) -> Vec2:
        """Where Dio stands: right against his prey."""
        return self.v - Vec2(self.side * 14, 0)

    def cue(self, f):
        fx, user = self.fx, self.scene.user
        hit = self.chest(self.scene.target, self.v) + Vec2(0, -8)
        if f == 1:
            self.world_words.add(sfx.DON, self.head(self.scene.target, self.v), "impact", 2, 30)
            fx.add(vfx.Flash(hit, 16, BLOOD_RED))
            fx.focus(hit, heavy=True)
            self.shake = 8
        if f == 18:
            self.shout("WRYYYYY !", (240, 54), 4, 70)
        if 20 <= f < self.RELEASE and f % 16 == 4:
            self.world_words.add(sfx.HEARTBEAT, hit + Vec2(-self.side * 10, -6), sfx.BLOOD, 2, 22)
            fx.add(vfx.Ring(hit, BLOOD_RED, 2.2, 14, 2))
            self.shake = max(self.shake, 3)
        if f == 110:
            self.world_words.menace(self.chest(user, self.grip()), -self.side)
        if f == self.RELEASE:
            fx.add(vfx.Flash(hit, 34, BLOOD_RED, 12))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.DON, hit + Vec2(0, -12), "impact", 3, 40, 0.2, 2)
            self.flash, self.shake = 6, 14

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        target = self.scene.target
        if f >= self.RELEASE:
            fallen = self.v + Vec2(self.side * min(20, (f - self.RELEASE) * 2), 0)
            self.body(world, target, fallen, "ko", 1, self.side < 0)
            self.body(world, user, self.grip(), "pose", 0, right)
            return
        self.victim(world, f)
        spot = self.grip() if f >= 10 else self.u + (self.grip() - self.u) * (f / 10)
        self.body(world, user, spot, "grab", 1 if f >= 10 else 0, right)
        if f < 14:
            return
        neck = self.chest(target, self.v) + Vec2(-self.side * 2, -9)
        hand = self.chest(user, spot) + Vec2(self.side * 8, -4)
        # The blood, in drops climbing from the neck up the fingers.
        for k in range(7):
            t = ((f * 2 + k * 11) % 44) / 44
            point = neck + (hand - neck) * t + Vec2(0, math.sin(t * 6.3 + k) * 2)
            pygame.draw.circle(world, OUTLINE, point.as_ints(), 3)
            pygame.draw.circle(world, BLOOD_RED, point.as_ints(), 2)
            world.set_at((point + Vec2(-1, -1)).as_ints(), (255, 120, 130))
        pulse = 0.5 + 0.5 * math.sin(f * 0.4)
        glow = tuple(round(c * (0.25 + 0.25 * pulse)) for c in BLOOD_RED)
        blit_glow(world, radial_glow(18, glow), self.chest(user, spot).as_ints())


# Bruford: the Hair Dance ----------------------------------------------------------------

HAIR_DARK = (40, 30, 52)


class HairDance(CutscenePlayer):
    """The hair caught: it spreads all around the opponent, then pierces from every side
    at once and drinks."""

    length = 180
    PIERCE = 96

    def camera(self, f):
        if f < 14:
            return (self.u + self.v) * 0.5, 2
        return self.v + Vec2(0, -20), 2

    def roots(self, f: int) -> list[Vec2]:
        """Where the locks come from: a ring around the victim, closing in."""
        spread = 54 - min(20, f * 0.25)
        return [
            self.v
            + Vec2(math.cos(i * math.tau / 9 + 0.3) * spread, math.sin(i * math.tau / 9) * 22)
            for i in range(9)
        ]

    def cue(self, f):
        fx = self.fx
        hit = self.chest(self.scene.target, self.v)
        if f == 1:
            self.world_words.add(sfx.DON, self.head(self.scene.target, self.v), "impact", 2, 30)
            fx.add(vfx.Flash(hit, 14))
            self.shake = 6
        if f == 20:
            self.world_words.menace(hit, 1)
            self.world_words.menace(hit, -1)
        if f == self.PIERCE:
            fx.add(vfx.Flash(hit, 30, (230, 40, 60), 10))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.DOGO, hit + Vec2(0, -14), "impact", 3, 44, 0.2, 2)
            self.flash, self.shake = 6, 14
        if f > self.PIERCE and f % 14 == 0:
            self.world_words.add(sfx.HEARTBEAT, hit + Vec2(0, -18), sfx.BLOOD, 2, 22)
            fx.add(vfx.Ring(hit, (210, 24, 48), 2.0, 12, 2))

    def negative(self, f):
        return self.PIERCE <= f < self.PIERCE + 3

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        self.body(world, user, self.u, "special", 2, right)
        self.victim(world, f)
        hit = self.chest(self.scene.target, self.v)
        head = self.chest(user, self.u) + Vec2(0, -14)
        for i, root in enumerate(self.roots(f)):
            # Each lock runs from Bruford's head round to its spot, then stabs in.
            lift = root + Vec2(0, -18 - (i % 3) * 6)
            vfx.draw_reach(world, head, lift, HAIR_DARK, "hair", 1)
            if f >= self.PIERCE:
                vfx.draw_reach(
                    world, lift, hit + Vec2((i - 4) * 1.5, (i % 3) - 1), HAIR_DARK, "hair", 1
                )


# Tarkus: the Neck Breaker -----------------------------------------------------------------


class NeckBreaker(CutscenePlayer):
    """The grip took hold: the chain goes round the opponent's neck, Tarkus throws all his
    weight back on it, and pulls."""

    length = 180
    SNAP = 140

    def camera(self, f):
        if f < 14:
            return (self.u + self.v) * 0.5, 2
        return (self.u + self.v) * 0.5 + Vec2(0, -16), 2

    def puller(self, f: int) -> Vec2:
        """Tarkus steps back, pulling."""
        back = min(26.0, max(0, f - 40) * 0.4)
        return self.u - Vec2(self.side * back, 0)

    def cue(self, f):
        fx = self.fx
        hit = self.chest(self.scene.target, self.v) + Vec2(0, -8)
        if f == 1:
            self.world_words.add(sfx.DON, self.head(self.scene.target, self.v), "impact", 2, 30)
            fx.add(vfx.Flash(hit, 14))
            self.shake = 6
        if f == 24:
            self.world_words.add(sfx.RATTLE, hit + Vec2(0, -14), "impact", 3, 40, 0.2, 2)
        if 44 <= f < self.SNAP and f % 12 == 0:
            self.world_words.menace(self.chest(self.scene.user, self.puller(f)), -self.side)
            self.shake = max(self.shake, 3)
        if f == self.SNAP:
            fx.add(vfx.Flash(hit, 34, (255, 255, 255), 10))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.BAKI, hit + Vec2(0, -12), "impact", 3, 46, 0.2, 2)
            self.flash, self.shake = 8, 18

    def negative(self, f):
        return self.SNAP <= f < self.SNAP + 3

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        spot = self.puller(f)
        anim = "grab" if f < 40 else "guard"
        self.body(world, user, spot, anim, 1 if f < 40 else 0, right)
        self.victim(world, f)
        neck = self.chest(self.scene.target, self.v) + Vec2(0, -10)
        hands = self.chest(user, spot) + Vec2(self.side * 6, -4)
        if f >= 18:
            vfx.draw_chain(world, hands, neck, sag=0 if f >= 44 else 4)
            # The chain round the neck.
            for i in range(6):
                angle = i * math.tau / 6
                link = neck + Vec2(math.cos(angle) * 5, math.sin(angle) * 2)
                vfx.draw_chain(world, link, link + Vec2(1, 0))


# Lisa Lisa: the scarf trap ----------------------------------------------------------------


class ScarfTrap(CutscenePlayer):
    """The scarf caught: it wraps round and round the opponent, then Lisa Lisa runs her
    Hamon through it, and the whole bundle blazes."""

    length = 180
    BLAZE = 120

    def camera(self, f):
        if f < 14:
            return (self.u + self.v) * 0.5, 2
        return self.v + Vec2(0, -18), 2

    def cue(self, f):
        fx = self.fx
        hit = self.chest(self.scene.target, self.v)
        if f == 1:
            self.world_words.add(sfx.DON, self.head(self.scene.target, self.v), "impact", 2, 30)
            fx.add(vfx.Flash(hit, 14))
            self.shake = 6
        if 30 <= f < self.BLAZE and f % 18 == 0:
            self.world_words.menace(hit, 1 if f % 36 else -1)
        if f == self.BLAZE - 20:
            self.shout(text.SCARF_TRAP_LINE, scale=2, life=40)
        if f == self.BLAZE:
            fx.add(vfx.Flash(hit, 34, (255, 220, 80), 12))
            fx.add(vfx.Ring(hit, (255, 220, 80), 4.0, 18, 3))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.CRACKLE, hit + Vec2(0, -16), sfx.HAMON, 3, 46, 0.2, 2)
            self.flash, self.shake = 8, 16
        if f > self.BLAZE and f % 10 == 0:
            fx.add(vfx.Ring(hit, (255, 214, 80), 2.0, 12, 1))

    def negative(self, f):
        return self.BLAZE <= f < self.BLAZE + 3

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        self.body(world, user, self.u, "special", 2, right)
        self.victim(world, f)
        hit = self.chest(self.scene.target, self.v)
        hands = self.chest(user, self.u) + Vec2(self.side * 6, 0)
        kind = "scarf_spear" if f >= self.BLAZE else "scarf"
        vfx.draw_reach(world, hands, hit, (168, 40, 58), kind, 2)
        # The scarf wound round the victim, more turns as it goes.
        turns = min(5, f // 16)
        for i in range(turns):
            y = hit.y - 12 + i * 5
            band = pygame.Rect(round(hit.x) - 8, round(y), 16, 3)
            pygame.draw.rect(world, (23, 18, 31), band.inflate(2, 2))
            color = (255, 220, 110) if f >= self.BLAZE and (f // 3 + i) % 2 else (168, 40, 58)
            pygame.draw.rect(world, color, band)


# Straizo: the eye barrage -----------------------------------------------------------------


class EyeBarrage(CutscenePlayer):
    """The first jet struck: Straizo opens his eyes wide and fires jet after jet,
    sweeping the whole screen, until the last one pierces through."""

    length = 170
    LAST = 132

    def camera(self, f):
        if f < 30:
            return self.u + Vec2(0, -24), 3  # close on the eyes
        return (self.u + self.v) * 0.5, 2

    def cue(self, f):
        fx = self.fx
        hit = self.chest(self.scene.target, self.v)
        if f == 1:
            self.shake = 4
            self.world_words.add(
                sfx.MENACE * 2, self.head(self.scene.user, self.u), "menace", 2, 30
            )
        if f == 18:
            self.shout(text.EYE_BARRAGE_LINE, scale=2, life=40)
        if 30 <= f < self.LAST and f % 6 == 0:
            fx.add(vfx.Flash(hit + Vec2(self.rng.randint(-8, 8), self.rng.randint(-10, 6)), 10))
            self.shake = max(self.shake, 3)
        if f == self.LAST:
            fx.add(vfx.Flash(hit, 34, (255, 255, 255), 10))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.DOGO, hit + Vec2(0, -14), "impact", 3, 46, 0.2, 2)
            self.flash, self.shake = 8, 16

    def negative(self, f):
        return self.LAST <= f < self.LAST + 3

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        self.body(world, user, self.u, "special", 1, right)
        self.victim(world, f)
        if f < 30:
            return
        eyes = self.head(user, self.u) + Vec2(self.side * 3, 9)
        hit = self.chest(self.scene.target, self.v)
        color = self.aura(user)
        if f < self.LAST and f % 3 != 2:
            # Jets sweeping across, most of them on target.
            sweep = math.sin(f * 0.7) * 40
            tip = hit + Vec2(self.side * 30, sweep)
            vfx.draw_reach(world, eyes, tip, color, "beam", 1)
        if f >= self.LAST and f < self.LAST + 10:
            far = hit + (hit - eyes).normalized() * 120
            vfx.draw_reach(world, eyes, far, color, "beam", 2)


# Wamuu: Final Mode, Atmospheric Rift ------------------------------------------------------


class AtmosphericRift(CutscenePlayer):
    """Final Mode. The growths on his wind armour drag the air of the whole room into
    him; it is compressed inside his body, which is what tears him up, and it comes back
    out through the horn on his brow as a vortex that cuts stone."""

    length = 240
    WIND_UP = 70  # the air starts turning
    RIFT = 150  # the blade leaves him
    WIND = (196, 226, 236)
    BLOOD = (168, 36, 48)

    def camera(self, f):
        if f < self.WIND_UP:
            return self.u + Vec2(0, -20), 3  # close on him opening himself up
        if f < self.RIFT:
            return (self.u + self.v) * 0.5, 2
        return self.v + Vec2(0, -14), 2

    def horn(self) -> Vec2:
        """The tip of the horn on his brow, where it all comes back out."""
        return self.head(self.scene.user, self.u, 4)

    def cue(self, f):
        fx, chest = self.fx, self.chest(self.scene.user, self.u)
        if f == 1:
            self.shout(text.FINAL_MODE_LINE, scale=2, life=46)
        if 12 <= f < self.WIND_UP and f % 5 == 0:
            # The room's air pulled into him, and his own blood going the other way.
            drift = Vec2(self.rng.uniform(-0.7, 0.7), self.rng.uniform(-1.1, -0.3))
            fx.add(vfx.Dust(chest + Vec2(self.rng.randint(-8, 8), 0), drift, 2, 16, self.BLOOD))
        if f == self.WIND_UP:
            fx.add(vfx.Ring(self.horn(), self.WIND, 3.0, 20, 2))
            self.world_words.menace(self.head(self.scene.user, self.u), 1)
            self.shake = 4
        if self.WIND_UP < f < self.RIFT and f % 9 == 0:
            fx.add(vfx.Ring(self.horn(), self.WIND, 2.2, 16, 1))
        if f == self.RIFT:
            hit = self.chest(self.scene.target, self.v)
            fx.add(vfx.Ring(self.horn(), self.WIND, 4.0, 22, 2))
            fx.add(vfx.Flash(hit, 40, self.WIND, 12))
            fx.add(vfx.Ring(hit, self.WIND, 5.0, 26, 3))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.DON, hit + Vec2(0, -16), "impact", 3, 46, 0.2, 2)
            self.flash, self.shake = 10, 18
        if f > self.RIFT and f % 8 == 0:
            drift = Vec2(self.rng.uniform(-1.4, 1.4), self.rng.uniform(-1.0, 0.2))
            fx.add(vfx.Dust(self.chest(self.scene.target, self.v), drift, 2, 18, self.WIND))

    def negative(self, f):
        return self.RIFT <= f < self.RIFT + 3

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        anim = "pose" if f < self.WIND_UP else "heavy"
        self.body(world, user, self.u, anim, 2, right)
        if f >= self.RIFT:
            self.victim(world, f)
        horn = self.horn()
        if 12 <= f < self.RIFT:
            # The air of the room dragged in: rings closing on the horn, tighter and
            # tighter, while his own body gives way under the pressure.
            turn = min(1.0, (f - 12) / (self.RIFT - 12))
            for i in range(5):
                radius = round(30 - 24 * turn + i * 4)
                offset = Vec2(math.sin(f * 0.3 + i) * 2, math.cos(f * 0.3 + i) * 2)
                pygame.draw.circle(world, self.WIND, (horn + offset).as_ints(), max(2, radius), 1)
            if f % 9 < 4:  # the body tearing under what it is holding
                for i in range(3):
                    cut = self.chest(user, self.u) + Vec2(self.rng.randint(-7, 7), i * 4 - 4)
                    world.fill(self.BLOOD, (round(cut.x), round(cut.y), 2, 1))
        if f >= self.RIFT:
            # And out of the horn: a blade of vacuum laid across the whole arena.
            reach = min(1.0, (f - self.RIFT) / 10)
            tip = horn + Vec2(self.side * 240 * reach, 0)
            pygame.draw.line(world, OUTLINE, horn.as_ints(), tip.as_ints(), 7)
            pygame.draw.line(world, self.WIND, horn.as_ints(), tip.as_ints(), 3)
            pygame.draw.line(world, (255, 255, 255), horn.as_ints(), tip.as_ints(), 1)


# Esidisi: the tears ------------------------------------------------------------------------


class EsidisiTears(CutscenePlayer):
    """He holds them, and then he starts to cry - and what comes out of his eyes is the
    same blood that runs in his arms, at five hundred degrees. It falls on them."""

    length = 228
    WEEP = 60
    RAIN = 130
    BLOOD = (224, 74, 44)
    STEAM = (255, 196, 120)

    def camera(self, f):
        if f < self.WEEP:
            return self.u + Vec2(0, -26), 3  # close on his face
        return (self.u + self.v) * 0.5, 2

    def cue(self, f):
        fx = self.fx
        eyes = self.head(self.scene.user, self.u, 4)
        hit = self.chest(self.scene.target, self.v)
        if f == 1:
            self.shout(text.ESIDISI_LINE, scale=2, life=50)
        if self.WEEP <= f < self.RAIN and f % 6 == 0:
            fall = Vec2(self.rng.uniform(-0.3, 0.3), self.rng.uniform(0.6, 1.2))
            fx.add(vfx.Dust(eyes + Vec2(self.rng.randint(-4, 4), 0), fall, 2, 20, self.BLOOD))
        if f == self.RAIN:
            self.world_words.add(sfx.CRACKLE, hit + Vec2(0, -18), "impact", 2, 44, 0.2, 2)
            self.flash, self.shake = 7, 12
        if f >= self.RAIN and f % 5 == 0:
            drop = hit + Vec2(self.rng.randint(-26, 26), -40)
            fx.add(vfx.Dust(drop, Vec2(0, self.rng.uniform(1.0, 1.8)), 2, 22, self.BLOOD))
            fx.add(vfx.Ring(hit, self.STEAM, 2.4, 14, 1))

    def negative(self, f):
        return self.RAIN <= f < self.RAIN + 3

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        self.body(world, user, self.u, "special" if f < self.RAIN else "heavy", 2, right)
        self.victim(world, f)
        if f < self.WEEP:
            return
        # The tears, falling from his eyes onto the ground between them.
        eyes = self.head(user, self.u, 4)
        for i in range(4):
            drop_y = eyes.y + ((f * 3 + i * 17) % 70)
            x = round(eyes.x + (-3 if i % 2 else 3))
            pygame.draw.line(world, self.BLOOD, (x, round(drop_y)), (x, round(drop_y) + 3), 1)
        if f >= self.RAIN:
            hit = self.chest(self.scene.target, self.v)
            for i in range(7):
                x = round(hit.x - 24 + i * 8 + (f % 3))
                top = round(hit.y - 44 + ((f * 5 + i * 13) % 44))
                pygame.draw.line(world, self.BLOOD, (x, top), (x, top + 5), 1)


# Kars: the Ultimate Thing -------------------------------------------------------------------


class UltimateThing(CutscenePlayer):
    """The Red Stone goes into the mask, the mask goes on, and what stands up afterwards
    is not a Pillar Man any more. The light comes out of him, not onto him."""

    length = 252
    MASK = 60
    BURST = 140
    LIGHT = (255, 244, 200)
    HALO = (236, 160, 248)

    def camera(self, f):
        if f < self.BURST:
            return self.u + Vec2(0, -22), 3
        return (self.u + self.v) * 0.5, 2

    def cue(self, f):
        fx, chest = self.fx, self.chest(self.scene.user, self.u)
        if f == 1:
            self.shout(text.KARS_LINE, scale=2, life=50)
        if f == self.MASK:
            self.world_words.menace(self.head(self.scene.user, self.u), 1)
            fx.add(vfx.Ring(chest, self.HALO, 2.0, 16, 2))
            self.shake = 3
        if self.MASK < f < self.BURST and f % 10 == 0:
            fx.add(vfx.Ring(chest, self.HALO, 2.6, 20, 1))
        if f == self.BURST:
            fx.add(vfx.Flash(chest, 70, self.LIGHT, 16))
            fx.focus(chest, heavy=True)
            self.flash, self.shake = 14, 16
        if f > self.BURST and f % 12 == 0:
            fx.add(vfx.Ring(chest, self.LIGHT, 4.0, 26, 2))

    def negative(self, f):
        return self.BURST <= f < self.BURST + 4

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        self.body(world, user, self.u, "pose", 2, right)
        if f >= self.BURST:
            self.victim(world, f)
        chest = self.chest(user, self.u)
        if f >= self.MASK:
            # Light coming out of him, in rays that get longer.
            grow = min(1.0, (f - self.MASK) / 70)
            for i in range(10):
                angle = math.tau * i / 10 + f * 0.02
                tip = chest + Vec2.from_angle(angle, 14 + 46 * grow)
                color = self.LIGHT if f >= self.BURST else self.HALO
                pygame.draw.line(world, color, chest.as_ints(), tip.as_ints(), 1)


# Stroheim: the German spirit ------------------------------------------------------------


class SelfDestruct(CutscenePlayer):
    """He opens the plate on his chest, says the line, and the whole machine goes off.
    What is left of him is standing, because of course it is."""

    length = 204
    OPEN = 46
    BLOW = 110
    FIRE = (255, 180, 70)
    WHITE = (255, 246, 214)

    def camera(self, f):
        if f < self.BLOW:
            return self.u + Vec2(0, -18), 3
        return (self.u + self.v) * 0.5, 2

    def cue(self, f):
        fx, chest = self.fx, self.chest(self.scene.user, self.u)
        if f == 1:
            self.shout(text.STROHEIM_LINE, scale=2, life=50)
        if self.OPEN <= f < self.BLOW and f % 8 == 0:
            spit = Vec2(self.rng.uniform(-1.0, 1.0), self.rng.uniform(-1.2, -0.2))
            fx.add(vfx.Dust(chest, spit, 2, 16, self.FIRE))
        if f == self.BLOW:
            fx.add(vfx.Flash(chest, 90, self.WHITE, 18))
            fx.add(vfx.Ring(chest, self.FIRE, 6.0, 30, 4))
            fx.focus(chest, heavy=True)
            self.world_words.add(sfx.DON, chest + Vec2(0, -14), "impact", 3, 50, 0.2, 2)
            self.flash, self.shake = 16, 22
        if f > self.BLOW and f % 7 == 0:
            fx.add(vfx.Ring(chest, self.FIRE, 3.4, 22, 2))
            blast = Vec2(self.rng.uniform(-1.8, 1.8), self.rng.uniform(-1.4, 0.2))
            fx.add(vfx.Dust(self.chest(self.scene.target, self.v), blast, 3, 20, self.FIRE))

    def negative(self, f):
        return self.BLOW <= f < self.BLOW + 4

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        self.body(world, user, self.u, "pose", 2, right)
        if f >= self.BLOW:
            self.victim(world, f)
        chest = self.chest(user, self.u)
        if self.OPEN <= f < self.BLOW:
            # The chest plate hinged open, the charge glowing inside it.
            plate = pygame.Rect(round(chest.x) - 5, round(chest.y) - 4, 10, 9)
            pygame.draw.rect(world, OUTLINE, plate.inflate(2, 2))
            pulse = 0.5 + 0.5 * math.sin(f * 0.4)
            pygame.draw.rect(world, tuple(round(c * pulse) for c in self.FIRE), plate)
        if f >= self.BLOW:
            grow = min(1.0, (f - self.BLOW) / 16)
            pygame.draw.circle(world, self.FIRE, chest.as_ints(), round(10 + 70 * grow), 2)


# Kars: the deluge of light ----------------------------------------------------------------


class LightDeluge(CutscenePlayer):
    """Every blade he has, out at once, and the light off them filling the screen until
    there is nothing in it but white."""

    length = 252
    OPEN = 54
    FLOOD = 150
    EDGE = (223, 230, 244)
    GLARE = (255, 250, 228)

    def camera(self, f):
        if f < self.OPEN:
            return self.u + Vec2(0, -18), 3
        return (self.u + self.v) * 0.5, 2

    def cue(self, f):
        fx = self.fx
        hit = self.chest(self.scene.target, self.v)
        if f == 1:
            self.shout(text.KARS_DELUGE_LINE, scale=2, life=46)
        if self.OPEN <= f < self.FLOOD and f % 6 == 0:
            spot = hit + Vec2(self.rng.randint(-22, 22), self.rng.randint(-20, 6))
            fx.add(vfx.Flash(spot, 10, self.EDGE, 6))
            if f % 18 == 0:
                self.world_words.add(sfx.BAKI, spot, "impact", 2, 26, 0.3, 2)
        if f == self.FLOOD:
            fx.add(vfx.Flash(hit, 90, self.GLARE, 20))
            fx.add(vfx.Ring(hit, self.GLARE, 6.0, 30, 4))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.DOGO, hit + Vec2(0, -16), "impact", 3, 48, 0.2, 2)
            self.flash, self.shake = 16, 20
        if f > self.FLOOD and f % 9 == 0:
            fx.add(vfx.Ring(hit, self.EDGE, 3.6, 24, 2))

    def negative(self, f):
        return self.FLOOD <= f < self.FLOOD + 4

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        self.body(world, user, self.u, "heavy", 2, right)
        self.victim(world, f)
        chest = self.chest(user, self.u)
        hit = self.chest(self.scene.target, self.v)
        if f < self.OPEN:
            return
        # Blades out of both arms, fanned at whoever is in front of him.
        blades = min(7, 1 + (f - self.OPEN) // 8)
        for i in range(blades):
            spread = (i - blades / 2) * 0.16
            toward = hit - chest
            if toward.length_sq() < 1:
                continue
            angle = toward.angle() + spread
            tip = chest + Vec2.from_angle(angle, min(toward.length() + 10, 120))
            vfx.draw_reach(world, chest, tip, self.EDGE, "blade", 2)


# Caesar: Burn Black ------------------------------------------------------------------------


class BurnBlack(CutscenePlayer):
    """The lenses settle round him one by one, each catching the sun, and every beam
    bends onto the same spot until he goes up. Caesar says it as he dies, so he says it
    here: burn... black."""

    length = 264
    LENSES = 8
    PLACED = 96  # all of them are in the air by now
    IGNITE = 168
    BUBBLE = (196, 228, 244)
    BEAM = (255, 232, 150)
    FIRE = (255, 140, 50)

    def lens(self, i: int, f: int) -> Vec2:
        """Where lens `i` sits: it drifts into its place on the ring and stays."""
        hit = self.chest(self.scene.target, self.v)
        angle = math.tau * i / self.LENSES - f * 0.006
        placed = min(1.0, max(0.0, (f - 10 - i * 8) / 26))
        return hit + Vec2.from_angle(angle, 10 + 30 * placed)

    def camera(self, f):
        if f < 30:
            return self.u + Vec2(0, -18), 3  # his hands, blowing them
        return self.v + Vec2(0, -10), 2

    def cue(self, f):
        fx = self.fx
        hit = self.chest(self.scene.target, self.v)
        if f == 1:
            self.shout(text.BURN_BLACK_LINE, scale=2, life=50)
        if 10 <= f < self.PLACED and (f - 10) % 8 == 0:
            i = (f - 10) // 8
            if i < self.LENSES:
                fx.add(vfx.Ring(self.lens(i, f), self.BUBBLE, 1.4, 10, 1))
        if f == self.PLACED:
            self.world_words.menace(self.head(self.scene.target, self.v), 1)
        if self.PLACED < f < self.IGNITE and f % 10 == 0:
            fx.add(vfx.Flash(hit, 12, self.BEAM, 6))
        if f == self.IGNITE:
            fx.add(vfx.Flash(hit, 60, self.FIRE, 16))
            fx.add(vfx.Ring(hit, self.FIRE, 5.0, 28, 3))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.CRACKLE, hit + Vec2(0, -16), sfx.HAMON, 3, 50, 0.2, 2)
            self.flash, self.shake = 14, 18
        if f > self.IGNITE and f % 6 == 0:
            spit = Vec2(self.rng.uniform(-1.2, 1.2), self.rng.uniform(-1.6, -0.4))
            fx.add(vfx.Dust(hit, spit, 2, 20, self.FIRE))

    def negative(self, f):
        return self.IGNITE <= f < self.IGNITE + 3

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        self.body(world, user, self.u, "special", 2, right)
        self.victim(world, f)
        hit = self.chest(self.scene.target, self.v)
        for i in range(self.LENSES):
            if f < 10 + i * 8:
                continue
            spot = self.lens(i, f)
            pygame.draw.circle(world, OUTLINE, spot.as_ints(), 4)
            pygame.draw.circle(world, self.BUBBLE, spot.as_ints(), 3)
            world.set_at((round(spot.x) - 1, round(spot.y) - 1), (255, 255, 255))
            if f >= self.PLACED:
                # Every lens bends the sunlight onto the same point.
                width = 1 if f < self.IGNITE else 2
                color = self.BEAM if f < self.IGNITE else self.FIRE
                pygame.draw.line(world, color, spot.as_ints(), hit.as_ints(), width)
        if f >= self.IGNITE:
            blaze = min(1.0, (f - self.IGNITE) / 20)
            pygame.draw.circle(world, self.FIRE, hit.as_ints(), round(6 + 18 * blaze), 2)


# Joseph: the tricks of the trade ------------------------------------------------------------


class OverdriveBeat(CutscenePlayer):
    """The string was already there. It catches him, Joseph walks in with both pairs of
    clackers, breathes once, and finishes with four of them at the same time."""

    length = 276
    CATCH = 44
    BEAT = 86
    BREATHE = 180
    FINISH = 214
    STRING = (228, 220, 196)
    HAMON = (255, 228, 120)

    def camera(self, f):
        if f < self.CATCH:
            return self.v + Vec2(0, 6), 3  # the string at his ankles
        if f < self.FINISH:
            return (self.u + self.v) * 0.5, 2
        return self.v + Vec2(0, -12), 2

    def cue(self, f):
        fx = self.fx
        hit = self.chest(self.scene.target, self.v)
        if f == 1:
            self.shout(text.JOSEPH_TRICKS_LINE, scale=2, life=46)
        if f == self.CATCH:
            self.world_words.add(sfx.GA, self.v + Vec2(0, -6), "impact", 2, 30, 0.3, 2)
            self.shake = 5
        if self.BEAT <= f < self.BREATHE and f % 7 == 0:
            spot = hit + Vec2(self.rng.randint(-10, 10), self.rng.randint(-12, 8))
            fx.add(vfx.Flash(spot, 9, self.HAMON, 5))
            self.world_words.add(sfx.BAKI, spot, "impact", 2, 20, 0.35, 2)
        if f == self.BREATHE:
            self.shout(text.OVERDRIVE_BEAT_LINE, scale=2, life=40)
            fx.add(vfx.Ring(self.chest(self.scene.user, self.u), self.HAMON, 2.4, 18, 2))
        if f == self.FINISH:
            fx.add(vfx.Flash(hit, 54, self.HAMON, 14))
            fx.add(vfx.Ring(hit, self.HAMON, 5.0, 26, 3))
            fx.focus(hit, heavy=True)
            self.world_words.add(sfx.DOGO, hit + Vec2(0, -16), "impact", 3, 48, 0.2, 2)
            self.flash, self.shake = 14, 18

    def negative(self, f):
        return self.FINISH <= f < self.FINISH + 3

    def scene_draw(self, world, f):
        user, right = self.scene.user, self.side > 0
        anim = "pose" if self.BREATHE <= f < self.FINISH else "light"
        self.body(world, user, self.u, anim, 2, right)
        self.victim(world, f)
        # The string, drawn taut between his hand and the opponent's feet.
        hand = self.chest(user, self.u) + Vec2(self.side * 5, 2)
        ankles = self.v + Vec2(-self.side * 4, -2)
        pygame.draw.line(world, OUTLINE, hand.as_ints(), ankles.as_ints(), 3)
        pygame.draw.line(world, self.STRING, hand.as_ints(), ankles.as_ints(), 1)
        if self.BEAT <= f < self.FINISH:
            # Clackers swinging on their cords, a pair in each hand.
            hit = self.chest(self.scene.target, self.v)
            for i in range(2 if f < self.FINISH - 20 else 4):
                swing = math.sin(f * 0.5 + i * 1.7) * 7
                ball = hit + Vec2(swing, -8 + i * 5)
                pygame.draw.line(world, self.STRING, hand.as_ints(), ball.as_ints(), 1)
                pygame.draw.circle(world, OUTLINE, ball.as_ints(), 3)
                pygame.draw.circle(world, (210, 60, 70), ball.as_ints(), 2)


CUTSCENES = {
    "road_roller": RoadRoller,
    "star_finish": StarFinish,
    "chariot_clones": ChariotClones,
    "hierophant_web": HierophantWeb,
    "hierophant_inside": HierophantInside,
    "sunlight_yellow_overdrive": SunlightYellowOverdrive,
    "tornado_overdrive": TornadoOverdrive,
    "absorption": Absorption,
    "hair_dance": HairDance,
    "neck_breaker": NeckBreaker,
    "scarf_trap": ScarfTrap,
    "eye_barrage": EyeBarrage,
    "atmospheric_rift": AtmosphericRift,
    "esidisi_tears": EsidisiTears,
    "ultimate_thing": UltimateThing,
    "light_deluge": LightDeluge,
    "burn_black": BurnBlack,
    "overdrive_beat": OverdriveBeat,
    "self_destruct": SelfDestruct,
}


def make_cutscene(view, match: Match, scene: Cutscene) -> CutscenePlayer:
    return CUTSCENES.get(scene.name, CutscenePlayer)(view, match, scene)
