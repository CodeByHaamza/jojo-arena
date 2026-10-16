"""Tiny 5x7 pixel font drawn in code (uppercase, digits, French accented capitals).

No font file is needed. Lowercase letters are drawn as capitals. Each glyph is 7 rows
("#" = lit pixel), placed in a 9-row line: one row above for accents, one below for
the cedilla. Glyphs may be narrower than 5 pixels.
"""

from __future__ import annotations

from functools import lru_cache

import pygame

Color = tuple[int, int, int]

_RAW = {
    "A": ".###. #...# #...# ##### #...# #...# #...#",
    "B": "####. #...# #...# ####. #...# #...# ####.",
    "C": ".###. #...# #.... #.... #.... #...# .###.",
    "D": "####. #...# #...# #...# #...# #...# ####.",
    "E": "##### #.... #.... ####. #.... #.... #####",
    "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .###.",
    "H": "#...# #...# #...# ##### #...# #...# #...#",
    "I": "### .#. .#. .#. .#. .#. ###",
    "J": "..### ...#. ...#. ...#. ...#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    "N": "#...# ##..# #.#.# #..## #...# #...# #...#",
    "O": ".###. #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# ####. #.... #.... #....",
    "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#",
    "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".#### #.... #.... .###. ....# ....# ####.",
    "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
    "W": "#...# #...# #...# #.#.# #.#.# #.#.# .#.#.",
    "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
    "1": "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    "2": ".###. #...# ....# ...#. ..#.. .#... #####",
    "3": "####. ....# ....# .###. ....# ....# ####.",
    "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": ".###. #.... #.... ####. #...# #...# .###.",
    "7": "##### ....# ...#. ..#.. .#... .#... .#...",
    "8": ".###. #...# #...# .###. #...# #...# .###.",
    "9": ".###. #...# #...# .#### ....# ....# .###.",
    " ": "... ... ... ... ... ... ...",
    ".": ". . . . . . #",
    ",": ". . . . . # #",
    "!": "# # # # # . #",
    "?": ".###. #...# ....# ...#. ..#.. ..... ..#..",
    ":": ". # . . . # .",
    ";": ". # . . . # #",
    "-": "... ... ... ### ... ... ...",
    "'": "# # . . . . .",
    "/": "....# ....# ...#. ..#.. .#... #.... #....",
    "%": "##..# ##.#. ...#. ..#.. .#... .#.## #..##",
    "(": ".# #. #. #. #. #. .#",
    ")": "#. .# .# .# .# .# #.",
    "+": "..... ..#.. ..#.. ##### ..#.. ..#.. .....",
    "&": ".##.. #..#. #.#.. .#... #.#.# #..#. .##.#",
    "=": ".... .... #### .... #### .... ....",
    "<": "...# ..#. .#.. #... .#.. ..#. ...#",
    ">": "#... .#.. ..#. ...# ..#. .#.. #...",
    "∞": "....... ....... .##.##. #..#..# .##.##. ....... .......",
    # A few katakana, for sound effects written in comic-book style.
    "ゴ": ".....#.# .....#.# #####... ....#... ....#... ....#... #####...",
    "ド": ".#...#.# .#...#.# .#...... .##..... .#.##... .#...... .#......",
    "ン": "#...... .#....# ......# .....#. ....#.. ..##... ##.....",
    "バ": ".....#.# .....#.# ..#..#.. ..#...#. .#....#. .#.....# #......#",
    "ガ": ".....#.# ..#..#.# ######.. ..#..#.. ..#..#.. .#...#.. #..##...",
    "キ": "..#.... ######. ..#.... ####### ...#... ...#... ...#...",
    "ク": ".#..... .#####. #....#. .....#. ....#.. ..##... ##.....",
    "ー": "....... ....... ....... ####### ....... ....... .......",
    "カ": "..#.... ######. ..#..#. ..#..#. .#...#. .#...#. #...##.",
    "パ": ".....### .....#.# ..#..### ..#...#. .#....#. .#.....# #......#",
    "コ": "######. .....#. .....#. .....#. .....#. .....#. ######.",
    "チ": "..####. ####... ...#... ####### ...#... ..#.... ##.....",
    "ピ": "#....#. #...#.# #....#. #####.. #...... #...... .#####.",
    "ジ": "##...#.# ..#....# ##....#. ..#..#.. ....#... ..##.... ##......",
    "ュ": "...... ...... ...... .####. ....#. ....#. ######",
    "ウ": "...#... ####### #.....# .....#. ....#.. ...#... .##....",
    "ャ": "....... ....... ..#.... #####.. ..#..#. ...#... ...#...",
    "ラ": ".#####. ....... ####### ......# .....#. ....#.. .##....",
    "ォ": "..... ..... ...#. ##### ..##. .#.#. #..#.",
    "ッ": "..... ..... #.#.# #.#.# ....# ...#. .##..",
    "←": "..... ..#.. .#... ##### .#... ..#.. .....",
    "→": "..... ..#.. ...#. ##### ...#. ..#.. .....",
    "↑": "..#.. .###. #.#.# ..#.. ..#.. ..#.. ..#..",
    "↓": "..#.. ..#.. ..#.. ..#.. #.#.# .###. ..#..",
}

# Accented capitals: the accent goes in the row above the letter.
_ACCENTS = {"acute": "...#.", "grave": ".#...", "circ": "..#..", "uml": ".#.#."}
_ACCENTED = {
    "É": ("acute", "E"),
    "È": ("grave", "E"),
    "Ê": ("circ", "E"),
    "Ë": ("uml", "E"),
    "À": ("grave", "A"),
    "Â": ("circ", "A"),
    "Î": ("circ", "I"),
    "Ï": ("uml", "I"),
    "Ô": ("circ", "O"),
    "Ù": ("grave", "U"),
    "Û": ("circ", "U"),
}


def _build_glyphs() -> dict[str, list[str]]:
    """Every glyph as 9 rows: accent row, 7 letter rows, cedilla row."""
    glyphs = {}
    for char, rows in _RAW.items():
        body = rows.split()
        blank = "." * len(body[0])
        glyphs[char] = [blank, *body, blank]
    for char, (accent, base) in _ACCENTED.items():
        body = _RAW[base].split()
        width = len(body[0])
        offset = (5 - width) // 2
        glyphs[char] = [_ACCENTS[accent][offset : offset + width], *body, "." * width]
    glyphs["Ç"] = [".....", *_RAW["C"].split(), "..#.."]
    return glyphs


GLYPHS = _build_glyphs()
HEIGHT = 9
SPACING = 1


def _glyph(char: str) -> list[str]:
    return GLYPHS.get(char.upper(), GLYPHS.get(char, GLYPHS["?"]))


def text_width(text: str, scale: int = 1) -> int:
    if not text:
        return 0
    width = sum(len(_glyph(c)[0]) for c in text) + SPACING * (len(text) - 1)
    return width * scale


def wrap(text: str, max_width: int, scale: int = 1) -> list[str]:
    """Split text into lines no wider than `max_width` pixels, at spaces."""
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if line and text_width(candidate, scale) > max_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


@lru_cache(maxsize=1024)
def render(
    text: str, color: Color, scale: int = 1, outline: Color | None = (23, 18, 31)
) -> pygame.Surface:
    """Text as a transparent surface, with an optional 1-pixel outline (before scaling)."""
    pad = 1 if outline else 0
    base = pygame.Surface((text_width(text) + 2 * pad, HEIGHT + 2 * pad), pygame.SRCALPHA)
    lit: list[tuple[int, int]] = []
    x = pad
    for char in text:
        rows = _glyph(char)
        for y, row in enumerate(rows):
            for dx, cell in enumerate(row):
                if cell == "#":
                    lit.append((x + dx, y + pad))
        x += len(rows[0]) + SPACING
    if outline:
        for px, py in lit:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                base.set_at((px + ox, py + oy), outline)
    for point in lit:
        base.set_at(point, color)
    if scale != 1:
        base = pygame.transform.scale_by(base, scale)
    return base


def draw(
    surface: pygame.Surface,
    text: str,
    pos: tuple[int, int],
    color: Color,
    *,
    scale: int = 1,
    align: str = "left",
    outline: Color | None = (23, 18, 31),
) -> pygame.Rect:
    """Draw text; `pos` is the top-left, top-center or top-right corner per `align`."""
    image = render(text, color, scale, outline)
    x, y = pos
    if align == "center":
        x -= image.get_width() // 2
    elif align == "right":
        x -= image.get_width()
    return surface.blit(image, (x, y))
