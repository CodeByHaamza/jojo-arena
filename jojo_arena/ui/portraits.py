"""Fighters drawn outside the fight: title screen, menus, character select, VS screen."""

from __future__ import annotations

import math

import pygame

from jojo_arena.characters import FighterDef
from jojo_arena.engine.effects import blit_glow, blit_shadow, radial_glow
from jojo_arena.engine.sprites import frame_index
from jojo_arena.ui.fight_view import STAND_ALPHA, FighterView

STAND_BEHIND = 13  # px (before scaling) the Stand stands behind its user in menus
STAND_RISE = 7


class FighterLook:
    """A fighter's sprites, and its Stand's, posed for menus (idle animation)."""

    def __init__(self, fighter_def: FighterDef) -> None:
        view = FighterView(fighter_def)
        self.fdef = fighter_def
        self.sprites = view.sprites
        self.stand = view.stand
        self.height = view.height
        self._face: pygame.Surface | None = None

    @staticmethod
    def _frame(sprites, tick: int, direction: str, flip: bool, anim: str = "idle"):
        name, spec = FighterView.resolve(sprites, anim)
        return sprites.frame(name, direction, flip, frame_index(spec, tick))

    @staticmethod
    def _blit(surface, sprites, image, feet, scale, flip, alpha=255) -> None:
        if scale != 1:
            image = pygame.transform.scale_by(image, scale)
        if alpha != 255:
            image = image.copy()
            image.set_alpha(alpha)
        ax, ay = sprites.anchor
        if flip:
            ax = image.get_width() // scale - 1 - ax
        surface.blit(image, (round(feet[0] - ax * scale), round(feet[1] - ay * scale)))

    def draw(
        self,
        surface: pygame.Surface,
        feet: tuple[float, float],
        tick: int,
        scale: int = 2,
        flip: bool = False,
        stand: bool = True,
        direction: str = "right",
        glow: bool = True,
        anim: str = "idle",
    ) -> None:
        """Draw the fighter standing at `feet`, facing right (left with `flip`)."""
        x, y = feet
        if glow:
            aura = tuple(round(c * 0.35) for c in self.fdef.aura)
            blit_glow(surface, radial_glow(18 * scale, aura), (x, y - self.height * scale * 0.55))
        if stand and self.stand is not None:
            back = 1 if flip else -1  # behind = away from where the fighter looks
            float_y = math.sin(tick * 0.06) * 1.5
            stand_feet = (x + back * STAND_BEHIND * scale, y - (STAND_RISE + float_y) * scale)
            image = self._frame(self.stand, tick, direction, flip, anim)
            self._blit(surface, self.stand, image, stand_feet, scale, flip, STAND_ALPHA)
        blit_shadow(surface, (x, y), round((14 + self.height * 0.25) * scale), 7 * scale)
        image = self._frame(self.sprites, tick, direction, flip, anim)
        self._blit(surface, self.sprites, image, (x, y), scale, flip)

    def face(self, size: int = 15) -> pygame.Surface:
        """Head close-up for the character grid (front view, first idle frame)."""
        if self._face is None:
            image = self._frame(self.sprites, 0, "down", False)
            ax, ay = self.sprites.anchor
            top = max(0, ay - self.height - 1)
            rect = pygame.Rect(ax - size // 2, top, size, size).clip(image.get_rect())
            self._face = image.subsurface(rect).copy()
        return self._face
