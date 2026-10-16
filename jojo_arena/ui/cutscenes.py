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
from jojo_arena.ui import sfx, vfx

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
            self.shout("L'HEURE DU CHÂTIMENT !", (240, 56), 2, 50)
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


CUTSCENES = {
    "road_roller": RoadRoller,
    "star_finish": StarFinish,
    "chariot_clones": ChariotClones,
    "hierophant_web": HierophantWeb,
    "hierophant_inside": HierophantInside,
}


def make_cutscene(view, match: Match, scene: Cutscene) -> CutscenePlayer:
    return CUTSCENES.get(scene.name, CutscenePlayer)(view, match, scene)
