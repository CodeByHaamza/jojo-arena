"""The rush duel screen: when two barrages meet, the fight leaves the arena for a face-off.

Each half of the screen takes its fighter's color, the two face each other in close-up,
their Stands' fists collide in the middle, and their shouts (ORA, MUDA...) fly off in
every direction behind them. The duel bar and the MASH prompt are drawn by the HUD.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from jojo_arena.combat.match import Match
from jojo_arena.engine.effects import blit_glow, radial_glow
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.sprites import frame_index, shade
from jojo_arena.ui import sfx, vfx

SCALE = 3
FEET_Y = 246
USER_X = (92, 388)  # each fighter stands well back...
STAND_X = (178, 302)  # ...its Stand throws the barrage in front
CENTER = Vec2(240, 150)
OUTLINE = (23, 18, 31)


@dataclass
class FlyingWord:
    text: str
    pos: Vec2
    velocity: Vec2
    scale: int
    life: int
    max_life: int
    style: tuple


class DuelScreen:
    def __init__(self, fighter_views, fighter_defs, shouts: tuple[str, str]) -> None:
        self.views = fighter_views
        self.defs = fighter_defs
        self.shouts = shouts
        self.words: list[FlyingWord] = []
        self.rng = random.Random(3)
        self._background: pygame.Surface | None = None

    # Words flying off -------------------------------------------------------------------

    def update(self, tick: int) -> None:
        rng = self.rng
        for side in (0, 1):
            if tick % 3 != side:
                continue
            # Burst out of the fighter's half, toward its own edge of the screen.
            direction = -1 if side == 0 else 1
            start = Vec2(240 + direction * rng.uniform(20, 120), rng.uniform(40, 240))
            angle = rng.uniform(-1.2, 1.2) + (math.pi if side == 0 else 0)
            velocity = Vec2.from_angle(angle, rng.uniform(1.5, 4.0))
            scale = rng.choice((1, 2, 2, 3))
            life = rng.randint(24, 40)
            style = sfx.shout_style(self.defs[side].aura)
            self.words.append(
                FlyingWord(self.shouts[side], start, velocity, scale, life, life, style)
            )
        for word in self.words:
            word.pos = word.pos + word.velocity
            word.life -= 1
        self.words = [w for w in self.words if w.life > 0]

    # Drawing -----------------------------------------------------------------------------

    def _halves(self, size: tuple[int, int]) -> pygame.Surface:
        """Each fighter's color on its own side, split by a jagged line, darker outside."""
        if self._background is None or self._background.get_size() != size:
            width, height = size
            back = pygame.Surface(size)
            for side in (0, 1):
                aura = self.defs[side].aura
                for x in range(width // 2):
                    t = x / (width / 2)  # 0 at the edge, 1 at the middle
                    color = tuple(round(c * (0.18 + 0.42 * t)) for c in aura)
                    column = x if side == 0 else width - 1 - x
                    back.fill(color, (column, 0, 1, height))
            # A jagged lightning seam where the two sides meet.
            points = []
            for i in range(10):
                y = i * height / 9
                points.append((width // 2 + (6 if i % 2 else -6), y))
            pygame.draw.lines(back, OUTLINE, False, points, 5)
            pygame.draw.lines(back, (255, 255, 255), False, points, 1)
            self._background = back
        return self._background

    def _speed_lines(self, surface: pygame.Surface, tick: int) -> None:
        rng = random.Random(tick // 2)
        for _ in range(28):
            angle = rng.uniform(0, math.tau)
            inner = rng.uniform(60, 120)
            outer = inner + rng.uniform(40, 140)
            a = CENTER + Vec2.from_angle(angle, inner)
            b = CENTER + Vec2.from_angle(angle, outer)
            pygame.draw.line(surface, (255, 255, 255), a.as_ints(), b.as_ints(), 1)

    def _sprite(self, sprites, anim: str, index: int, flip: bool) -> pygame.Surface:
        from jojo_arena.ui.fight_view import FighterView

        name, spec = FighterView.resolve(sprites, anim)
        image = sprites.frame(name, "right", flip, min(index, spec.frames - 1))
        return pygame.transform.scale_by(image, SCALE)

    def _blit_feet(self, surface, image, sprites, x: float, y: float, flip: bool, alpha=255):
        ax, ay = sprites.anchor
        if flip:
            ax = image.get_width() // SCALE - 1 - ax
        if alpha != 255:
            image = image.copy()
            image.set_alpha(alpha)
        surface.blit(image, (round(x - ax * SCALE), round(y - ay * SCALE)))

    def draw(self, surface: pygame.Surface, match: Match, tick: int) -> None:
        surface.blit(self._halves(surface.get_size()), (0, 0))
        self._speed_lines(surface, tick)
        for word in self.words:
            image = sfx.render_word(word.text, word.style, word.scale)
            if word.life < 10:
                image = image.copy()
                image.set_alpha(round(220 * word.life / 10))
            rect = image.get_rect(center=word.pos.as_ints())
            surface.blit(image, rect)

        chests = []
        for side in (0, 1):
            view = self.views[side]
            flip = side == 1
            toward = 1 if side == 0 else -1
            # The user, braced, well behind.
            idle_spec = view.sprites.spec("idle")
            idle = frame_index(idle_spec, tick) if idle_spec else 0
            user = self._sprite(view.sprites, "idle", idle, flip)
            self._blit_feet(surface, user, view.sprites, USER_X[side], FEET_Y, flip)
            # The Stand (or the user's own fists), throwing punches as fast as it can.
            punch = 1 + (tick // 3 + side) % 2
            stand_sheet = view.stand or view.sprites
            stand = self._sprite(stand_sheet, "light", punch, flip)
            bob = math.sin(tick * 0.3 + side) * 2
            stand_x = STAND_X[side]
            self._blit_feet(surface, stand, stand_sheet, stand_x, FEET_Y - 16 + bob, flip, 235)
            chests.append(Vec2(stand_x + toward * 18, FEET_Y - 16 - stand_sheet.chest * SCALE))
        # The two barrages, drawn in turns so that neither hides the other.
        for side in (0, 1) if tick % 2 else (1, 0):
            aim = Vec2(1 if side == 0 else -1, 0)
            kind = "blade" if self._is_blade(match, side) else "fists"
            aura, chest, seed = self.defs[side].aura, chests[side], tick * 17 + side * 5
            vfx.draw_flurry(surface, chest, aim, aura, seed, 74, 16, kind, size=2)
            vfx.draw_flurry(surface, chest + Vec2(0, 18), aim, aura, seed + 1, 64, 10, kind, 2)

        # Where the barrages meet.
        flicker = 0.7 + 0.3 * ((tick // 2) % 2)
        blit_glow(surface, radial_glow(34, tuple(round(255 * flicker) for _ in range(3))), CENTER)
        for i in range(14):
            angle = tick * 0.4 + i * math.tau / 14
            end = CENTER + Vec2.from_angle(angle, 14 + (i * 7 + tick) % 22)
            pygame.draw.line(surface, OUTLINE, CENTER.as_ints(), end.as_ints(), 3)
            pygame.draw.line(surface, (255, 250, 220), CENTER.as_ints(), end.as_ints(), 1)
        # A white rim so the duel reads as its own panel.
        pygame.draw.rect(surface, shade((255, 255, 255), 0), surface.get_rect(), 2)

    def _is_blade(self, match: Match, side: int) -> bool:
        """Fencers (Polnareff) thrust with the blade instead of punching."""
        kit = match.fighters[side].kit
        return any(m.hits > 1 and m.fx == "blade" for m in kit.all_moves())
