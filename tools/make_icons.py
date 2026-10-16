"""Turn the pixel-art drawings of tools/icons/ into PNG icons (part emblems, glossary).

    python tools/make_icons.py

Each drawing is a TOML file: a palette (one letter per color, "." is transparent) and
`pixels`, the rows of letters. The icons go to jojo_arena/assets/icons/<id>.png.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DRAWINGS_DIR = ROOT / "tools" / "icons"
ICONS_DIR = ROOT / "jojo_arena" / "assets" / "icons"


def parse_color(value: str) -> tuple[int, int, int]:
    text = value.lstrip("#")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def render_icon(path: Path) -> pygame.Surface:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    palette = {key: parse_color(value) for key, value in data["palette"].items()}
    rows = data["pixels"]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError(f"{path.name}: every row of pixels needs {width} letters")
    image = pygame.Surface((width, len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, letter in enumerate(row):
            if letter == ".":
                continue
            if letter not in palette:
                raise ValueError(f"{path.name}: letter '{letter}' is not in the palette")
            image.set_at((x, y), (*palette[letter], 255))
    return image


def drawings() -> list[Path]:
    return sorted(DRAWINGS_DIR.glob("*.toml"))


def main() -> None:
    pygame.init()
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for path in drawings():
        image = render_icon(path)
        pygame.image.save(image, str(ICONS_DIR / f"{path.stem}.png"))
        print(f"{path.stem}: {image.get_width()}x{image.get_height()}")


if __name__ == "__main__":
    main()
