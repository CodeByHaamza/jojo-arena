from pathlib import Path

import pygame
import pytest
from spritegen.look import ramp
from spritegen.raster import OUTLINE, Part, polygon, render
from spritegen.sheet import build_sheet
from spritegen.skeleton import DIRECTIONS, animations

from jojo_arena.characters import load_roster
from jojo_arena.engine.sprites import SheetSprites
from jojo_arena.paths import SPRITES_DIR

ROOT = Path(__file__).resolve().parents[1]
LOOKS = [ROOT / "tools" / "spritegen" / "mannequin.toml"] + sorted(
    (ROOT / "jojo_arena" / "characters" / "looks").glob("*.toml")
)


def lightness(color):
    return sum(color) / 3


def test_ramp_goes_from_dark_to_highlight():
    tones = ramp((45, 49, 96))
    assert [lightness(t) for t in tones] == sorted(lightness(t) for t in tones)
    assert tones[1] == (45, 49, 96)


def test_polygon_fills_pixel_centers_inside():
    square = polygon([(0, 0), (4, 0), (4, 4), (0, 4)])
    assert len(square) == 16 and (0, 0) in square and (4, 4) not in square


def test_render_outlines_and_layers():
    palette = {"a": [(10, 0, 0), (20, 0, 0), (30, 0, 0)], "b": [(0, 10, 0), (0, 20, 0), (0, 30, 0)]}
    back = Part("a", {(x, y) for x in range(10, 20) for y in range(10, 20)}, z=1)
    front = Part("b", {(x, y) for x in range(14, 16) for y in range(14, 16)}, z=2)
    image = render([front, back], palette)  # given out of order on purpose
    assert tuple(image.get_at((14, 14)))[:3][1] > 0  # the front part wins
    assert tuple(image.get_at((9, 15)))[:3] == OUTLINE


@pytest.mark.parametrize("look_path", LOOKS, ids=lambda p: p.stem)
def test_every_look_builds_a_complete_sheet(look_path):
    from spritegen.look import load_look

    look = load_look(look_path)
    sheet, spec = build_sheet(look)
    size = look.cell
    assert sheet.get_size() == (5 * size, 10 * len(DIRECTIONS) * size)
    rows = 0
    for name, (_, _, _, frames) in animations("down").items():
        for d, _view in enumerate(DIRECTIONS):
            for i in range(len(frames)):
                cell = sheet.subsurface((i * size, (rows + d) * size, size, size))
                box = cell.get_bounding_rect()
                assert box.width > 4 and box.height > 4, f"{name} frame {i} is empty"
                assert box.top > 0 and box.bottom < size, f"{name} frame {i} touches the edge"
                assert box.left > 0 and box.right < size, f"{name} frame {i} touches the edge"
        rows += len(DIRECTIONS)
    assert f"[anims.{name}]" in spec


def test_build_changes_the_silhouette():
    from spritegen.look import load_look
    from spritegen.sheet import body_heights

    looks = {p.stem: load_look(p) for p in LOOKS}
    _, jotaro = body_heights(looks["jotaro_p3"])
    _, mannequin = body_heights(looks["mannequin"])
    assert jotaro > mannequin  # Jotaro is taller than the standard body


def test_generated_sheets_are_up_to_date():
    """The PNG in assets must match its look file (run tools/make_sprites.py)."""
    from spritegen.look import load_look

    for path in LOOKS:
        look = load_look(path)
        sheet, _ = build_sheet(look)
        on_disk = pygame.image.load(str(SPRITES_DIR / look.id / f"{look.id}.png"))
        assert pygame.image.tobytes(sheet, "RGBA") == pygame.image.tobytes(on_disk, "RGBA"), (
            f"{look.id}: regenerate with python tools/make_sprites.py {look.id}"
        )


def test_every_roster_sprite_exists_and_loads():
    for fighter in load_roster():
        base = SPRITES_DIR / fighter.sprite
        sheet = SheetSprites.load(base.with_suffix(".png"), base.with_suffix(".toml"), None)
        assert sheet is not None, fighter.id
