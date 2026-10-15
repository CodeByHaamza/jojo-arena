import pygame
import pytest

from jojo_arena.engine.effects import radial_glow
from jojo_arena.engine.sprites import (
    AnimSpec,
    PlaceholderSprites,
    SheetSprites,
    frame_index,
    parse_color,
    recolor,
    sprite_direction,
)
from jojo_arena.paths import SPRITES_DIR

MANNEQUIN_PNG = SPRITES_DIR / "mannequin" / "mannequin.png"
MANNEQUIN_SPEC = SPRITES_DIR / "mannequin" / "mannequin.toml"
REQUIRED_ANIMS = ["idle", "walk", "light", "heavy", "special", "dash", "guard", "hurt", "ko"]


def test_parse_color_accepts_hex_and_lists():
    assert parse_color("#ff8000") == (255, 128, 0)
    assert parse_color([1, 2, 3]) == (1, 2, 3)


def test_looping_and_one_shot_animations():
    walk = AnimSpec("walk", 4, fps=10, loop=True)
    assert frame_index(walk, 0) == 0
    assert frame_index(walk, 6) == 1
    assert frame_index(walk, 24) == 0  # 4 frames at 10 fps loop every 24 steps
    ko = AnimSpec("ko", 3, fps=10, loop=False)
    assert frame_index(ko, 600) == 2


def test_attack_animation_follows_move_phases():
    heavy = AnimSpec("heavy", 5, phases=(2, 1, 2))
    assert frame_index(heavy, 0, phase=(0, 0, 10)) == 0
    assert frame_index(heavy, 0, phase=(0, 6, 10)) == 1
    assert frame_index(heavy, 0, phase=(1, 0, 3)) == 2  # active frame
    assert frame_index(heavy, 0, phase=(2, 19, 20)) == 4


def test_sprite_direction_uses_side_view_for_diagonals():
    assert sprite_direction(0, 1) == ("down", False)
    assert sprite_direction(0, -1) == ("up", False)
    assert sprite_direction(-1, 0) == ("right", True)
    assert sprite_direction(0.7, -0.7) == ("right", False)


def test_mannequin_sheet_has_every_required_animation():
    sheet = SheetSprites.load(MANNEQUIN_PNG, MANNEQUIN_SPEC)
    assert sheet is not None
    for anim in REQUIRED_ANIMS:
        spec = sheet.spec(anim)
        assert spec is not None, anim
        for direction in ("down", "up", "right"):
            for i in range(spec.frames):
                assert sheet.frame(anim, direction, False, i).get_size() == sheet.cell
    assert sheet.frame("idle", "right", True, 0).get_size() == sheet.cell
    assert 0 < sheet.chest < sheet.height < sheet.cell[1]


def test_missing_sheet_returns_none(tmp_path):
    assert SheetSprites.load(tmp_path / "nope.png", tmp_path / "nope.toml") is None


def test_recolor_swaps_key_colors_only():
    sheet = pygame.Surface((3, 1), pygame.SRCALPHA)
    sheet.set_at((0, 0), (116, 116, 124))
    sheet.set_at((1, 0), (23, 18, 31))
    result = recolor(
        sheet, {"body": [[68, 68, 76], [116, 116, 124]]}, {"body": [(1, 1, 1), (200, 0, 0)]}
    )
    assert tuple(result.get_at((0, 0)))[:3] == (200, 0, 0)
    assert tuple(result.get_at((1, 0)))[:3] == (23, 18, 31)
    assert result.get_at((2, 0)).a == 0


def test_placeholder_draws_every_state():
    sprites = PlaceholderSprites((200, 60, 60))
    for anim in REQUIRED_ANIMS + ["pose"]:
        spec = sprites.spec(anim)
        image = sprites.frame(anim, "right", True, spec.frames - 1)
        assert image.get_size() == (48, 48)
        assert image.get_bounding_rect().width > 0


@pytest.mark.parametrize("radius", [4, 20])
def test_glow_is_brightest_in_the_middle_and_black_at_the_edge(radius):
    glow = radial_glow(radius, (200, 100, 50))
    center = glow.get_at((radius, radius))
    assert center.r > 100
    assert tuple(glow.get_at((0, 0)))[:3] == (0, 0, 0)
