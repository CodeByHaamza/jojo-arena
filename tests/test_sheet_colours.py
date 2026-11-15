"""A sheet's colours: repainted in one pass when the sheet is loaded, read from the sheet's
own description, and only a few repainted sheets kept in memory."""

import pygame

from jojo_arena.engine import sprites
from jojo_arena.engine.sprites import REPAINTED_KEPT, ColorInfo, SheetSprites, recolor

GREY = (120, 120, 130)


def colored_sheet(tmp_path, colors: int, name: str = "sheet"):
    """A one-animation sheet of one flat tone, with `colors` colours: c0 is the sheet as it
    is, cN paints the body (N * 20, 10, 10)."""
    image = pygame.Surface((64, 192), pygame.SRCALPHA)
    image.fill((*GREY, 255), (20, 20, 24, 24))
    png, spec = tmp_path / f"{name}.png", tmp_path / f"{name}.toml"
    pygame.image.save(image, str(png))
    lines = [
        "frame_size = [64, 64]",
        "anchor = [32, 60]",
        'directions = ["down", "up", "right"]',
        "",
        "[anims.idle]",
        "row = 0",
        "frames = 1",
    ]
    if colors:
        lines += ["", "[costume]", 'label = "Tenue"', 'label_en = "Outfit"', 'source = "S"']
        lines += ["", "[recolor]", f"body = [{list(GREY)}]"]
    for n in range(colors):
        lines += ["", f"[colors.c{n}]", f'label = "C{n}"', f'label_en = "C{n} en"']
        lines += [f'source = "source {n}"', f'stand = "{"s1" if n == 1 else ""}"']
        if n:
            lines += [f"[colors.c{n}.palette]", f"body = [[{n * 20}, 10, 10]]"]
    spec.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return png, spec


def body(sheet: SheetSprites):
    return tuple(sheet.frame("idle", "down", False, 0).get_at((30, 30)))[:3]


def test_a_tone_already_repainted_is_not_repainted_again():
    # shirt: red -> green; trousers: green -> blue. One pass: red ends green, green ends blue.
    sheet = pygame.Surface((2, 1), pygame.SRCALPHA)
    sheet.set_at((0, 0), (200, 0, 0, 255))
    sheet.set_at((1, 0), (0, 200, 0, 255))
    keys = {"shirt": [[200, 0, 0]], "trousers": [[0, 200, 0]]}
    result = recolor(sheet, keys, {"shirt": [(0, 200, 0)], "trousers": [(0, 0, 200)]})
    assert tuple(result.get_at((0, 0)))[:3] == (0, 200, 0)
    assert tuple(result.get_at((1, 0)))[:3] == (0, 0, 200)


def test_two_materials_can_swap_their_colours():
    sheet = pygame.Surface((2, 1), pygame.SRCALPHA)
    sheet.set_at((0, 0), (200, 0, 0, 255))
    sheet.set_at((1, 0), (0, 200, 0, 255))
    keys = {"a": [[200, 0, 0]], "b": [[0, 200, 0]]}
    result = recolor(sheet, keys, {"a": [(0, 200, 0)], "b": [(200, 0, 0)]})
    assert tuple(result.get_at((0, 0)))[:3] == (0, 200, 0)
    assert tuple(result.get_at((1, 0)))[:3] == (200, 0, 0)


def test_transparent_pixels_stay_transparent_whatever_the_key():
    sheet = pygame.Surface((2, 1), pygame.SRCALPHA)  # (0, 0, 0, 0) everywhere
    sheet.set_at((1, 0), (0, 0, 0, 255))  # and one opaque black pixel
    result = recolor(sheet, {"ink": [[0, 0, 0]]}, {"ink": [(250, 250, 250)]})
    assert result.get_at((0, 0)).a == 0
    assert tuple(result.get_at((1, 0))) == (250, 250, 250, 255)


def test_the_original_sheet_is_left_as_it_was():
    sheet = pygame.Surface((1, 1), pygame.SRCALPHA)
    sheet.set_at((0, 0), (200, 0, 0, 255))
    recolor(sheet, {"a": [[200, 0, 0]]}, {"a": [(1, 2, 3)]})
    assert tuple(sheet.get_at((0, 0)))[:3] == (200, 0, 0)


def test_a_sheet_knows_its_colours_and_its_costume(tmp_path):
    sheet = SheetSprites.load(*colored_sheet(tmp_path, 3))
    assert list(sheet.colors) == ["c0", "c1", "c2"]  # in the order of the file
    assert sheet.colors["c0"] == ColorInfo("c0", "C0", "C0 en", "source 0", "", {})
    second = sheet.colors["c1"]
    assert (second.label, second.label_en, second.source, second.stand) == (
        "C1",
        "C1 en",
        "source 1",
        "s1",
    )
    assert second.palette == {"body": [(20, 10, 10)]}
    assert sheet.costume == ("Tenue", "Outfit", "S")


def test_a_sheet_is_loaded_in_the_colour_asked(tmp_path):
    png, spec = colored_sheet(tmp_path, 3)
    assert body(SheetSprites.load(png, spec)) == GREY
    assert body(SheetSprites.load(png, spec, color="c2")) == (40, 10, 10)
    assert body(SheetSprites.load(png, spec, color="c1")) == (20, 10, 10)
    assert body(SheetSprites.load(png, spec, color="c0")) == GREY  # the first: as it is


def test_a_sheet_without_colors_ignores_the_colour_asked(tmp_path):
    png, spec = colored_sheet(tmp_path, 0)
    sheet = SheetSprites.load(png, spec, color="c2")
    assert sheet.colors == {} and sheet.costume == ("", "", "")
    assert body(sheet) == GREY


def test_an_unknown_colour_is_the_sheet_as_it_is(tmp_path):
    png, spec = colored_sheet(tmp_path, 2)
    assert body(SheetSprites.load(png, spec, color="gone")) == GREY
    assert SheetSprites.load(png, spec, color="gone") is SheetSprites.load(png, spec)


def test_a_colour_goes_over_the_palette_given_by_hand(tmp_path):
    """The dummies' palette (roster.toml) and a sheet's colours are one system."""
    png, spec = colored_sheet(tmp_path, 2)
    by_hand = SheetSprites.load(png, spec, palette={"body": [(1, 2, 3)]})
    assert body(by_hand) == (1, 2, 3)
    both = SheetSprites.load(png, spec, palette={"body": [(1, 2, 3)]}, color="c1")
    assert body(both) == (20, 10, 10)


def test_the_same_colour_asked_twice_is_decoded_once(tmp_path):
    png, spec = colored_sheet(tmp_path, 2)
    assert SheetSprites.load(png, spec, color="c1") is SheetSprites.load(png, spec, color="c1")


def test_only_a_few_repainted_sheets_are_kept(tmp_path):
    count = REPAINTED_KEPT + 3
    png, spec = colored_sheet(tmp_path, count + 1)
    plain = SheetSprites.load(png, spec)
    first = SheetSprites.load(png, spec, color="c1")
    for n in range(2, count + 1):
        SheetSprites.load(png, spec, color=f"c{n}")
    assert len(sprites._REPAINTED) == REPAINTED_KEPT
    assert SheetSprites.load(png, spec, color="c1") is not first  # dropped: decoded again
    assert SheetSprites.load(png, spec) is plain  # a sheet as it is stays for good


def test_a_sheet_without_an_alpha_channel_is_repainted_just_as_safely():
    """An image saved without transparency: its black pixels are not a stand-in."""
    sheet = pygame.Surface((2, 1))  # no per-pixel alpha
    sheet.set_at((0, 0), (200, 0, 0))
    sheet.set_at((1, 0), (0, 0, 0))
    result = recolor(sheet, {"a": [[200, 0, 0]]}, {"a": [(9, 9, 9)]})
    assert tuple(result.get_at((0, 0)))[:3] == (9, 9, 9)
    assert tuple(result.get_at((1, 0)))[:3] == (0, 0, 0)
