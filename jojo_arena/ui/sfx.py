"""Comic-book sound effects written on screen: big outlined words that pop, float, fade.

Words can be katakana (ゴゴゴ, ドン, バーン...) or plain letters (ORA, MUDA, shouts).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from functools import lru_cache

import pygame

from jojo_arena.engine import font
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.sprites import shade

Color = tuple[int, int, int]

# name -> (light, dark, outline)
STYLES: dict[str, tuple[Color, Color, Color]] = {
    "menace": ((226, 140, 255), (120, 44, 196), (28, 8, 40)),
    "impact": ((255, 244, 140), (255, 120, 40), (54, 16, 8)),
    "ko": ((255, 120, 110), (176, 18, 40), (30, 4, 10)),
    "block": ((190, 220, 255), (70, 120, 230), (12, 18, 44)),
    "white": ((255, 255, 255), (190, 184, 214), (23, 18, 31)),
}

MENACE = "ゴ"
DODODO = "ドドドド"
DON = "ドン"
DOGO = "ドゴォ"
BAAN = "バーン"
BAKI = "バキッ"
GA = "ガッ"
HEARTBEAT = "ドクン"
BREATH = "コォォォ"  # Hamon breathing
CRACKLE = "バチッ"  # Hamon sparks on a hit
HAMON = ((255, 236, 120), (220, 140, 30), (60, 30, 10))  # word colors for Hamon
FREEZE = "ピキッ"  # frozen solid
SIZZLE = "ジュウ"  # burning in the sun
RATTLE = "ジャラ"  # chains
ICE = ((236, 250, 255), (120, 190, 240), (20, 40, 70))
BLOOD = ((255, 150, 160), (190, 20, 50), (50, 6, 16))


def shout_style(aura: Color) -> tuple[Color, Color, Color]:
    """Colors for a fighter's own shouts, from its aura."""
    return shade(aura, 70), shade(aura, -50), (23, 18, 31)


@lru_cache(maxsize=256)
def render_word(text: str, style: tuple[Color, Color, Color], scale: int) -> pygame.Surface:
    """A word with a top-to-bottom gradient, a thick outline and a drop shadow."""
    light, dark, outline = style
    mask = font.render(text, (255, 255, 255), 1, outline=None)
    width, height = mask.get_size()
    colored = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(light, dark, strict=True))
        for x in range(width):
            if mask.get_at((x, y)).a:
                colored.set_at((x, y), color)
    big = pygame.transform.scale_by(colored, scale)
    silhouette = big.copy()
    silhouette.fill((*outline, 255), special_flags=pygame.BLEND_RGBA_MIN)
    silhouette.fill((*outline, 0), special_flags=pygame.BLEND_RGB_MAX)
    thick = max(1, scale - 1)
    pad = thick + 2
    out = pygame.Surface((big.get_width() + 2 * pad, big.get_height() + 2 * pad), pygame.SRCALPHA)
    shadow = silhouette.copy()
    shadow.set_alpha(120)
    out.blit(shadow, (pad + thick + 1, pad + thick + 1))
    for dx in range(-thick, thick + 1):
        for dy in range(-thick, thick + 1):
            if dx or dy:
                out.blit(silhouette, (pad + dx, pad + dy))
    out.blit(big, (pad, pad))
    return out


@dataclass
class Word:
    text: str
    pos: Vec2
    style: tuple[Color, Color, Color]
    scale: int
    life: int
    max_life: int
    rise: float
    shake: int = 0  # jitter amplitude in pixels

    def update(self) -> None:
        self.life -= 1
        self.pos = self.pos + Vec2(0, -self.rise)

    def draw(self, surface: pygame.Surface, rng: random.Random) -> None:
        age = self.max_life - self.life
        scale = self.scale + (1 if age < 3 else 0)  # pops in slightly bigger
        image = render_word(self.text, self.style, scale)
        if self.life < 10:
            image = image.copy()
            image.set_alpha(round(255 * self.life / 10))
        x, y = self.pos.x, self.pos.y
        if self.shake:
            x += rng.randint(-self.shake, self.shake)
            y += rng.randint(-self.shake, self.shake)
        surface.blit(image, (round(x - image.get_width() / 2), round(y - image.get_height() / 2)))


class SfxLayer:
    """All the words currently on screen."""

    def __init__(self, seed: int = 7) -> None:
        self.words: list[Word] = []
        self.rng = random.Random(seed)

    def add(
        self,
        text: str,
        pos: Vec2,
        style: str | tuple[Color, Color, Color] = "impact",
        scale: int = 2,
        life: int = 36,
        rise: float = 0.35,
        shake: int = 0,
    ) -> None:
        colors = STYLES[style] if isinstance(style, str) else style
        self.words.append(Word(text, pos, colors, scale, life, life, rise, shake))

    def scatter(self, text: str, center: Vec2, spread: float, **kwargs) -> None:
        """Add a word somewhere around `center` (rush shouts, menacing marks)."""
        offset = Vec2(self.rng.uniform(-spread, spread), self.rng.uniform(-spread, spread) * 0.6)
        self.add(text, center + offset, **kwargs)

    def menace(self, center: Vec2, side: int) -> None:
        """The famous menacing ゴ, rising beside a fighter one mark at a time."""
        x = center.x + side * self.rng.uniform(14, 24)
        y = center.y + self.rng.uniform(-14, 6)
        self.add(MENACE, Vec2(x, y), "menace", scale=2, life=46, rise=0.45)

    def update(self) -> None:
        for word in self.words:
            word.update()
        self.words = [w for w in self.words if w.life > 0]

    def draw(self, surface: pygame.Surface) -> None:
        for word in self.words:
            word.draw(surface, self.rng)
