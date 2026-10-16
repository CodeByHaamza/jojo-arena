import tomllib
from pathlib import Path

import pygame
import pytest
from spritegen.look import ramp
from spritegen.raster import OUTLINE, Part, polygon, render
from spritegen.sheet import build_sheet, look_animations
from spritegen.skeleton import DIRECTIONS, KeyAnim, Pose, blend

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
    table = look_animations(look, "down")
    longest = max(len(frames) for _, _, _, frames in table.values())
    assert sheet.get_size() == (longest * size, len(table) * len(DIRECTIONS) * size)
    rows = 0
    for name, (_, _, phases, frames) in table.items():
        if phases:
            assert sum(phases) == len(frames), name
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
        for sprite in filter(None, (fighter.sprite, fighter.stand_sprite)):
            base = SPRITES_DIR / sprite
            sheet = SheetSprites.load(base.with_suffix(".png"), base.with_suffix(".toml"), None)
            assert sheet is not None, f"{fighter.id}: {sprite}"


# Key-pose animations in look files ----------------------------------------------------

MANNEQUIN = ROOT / "tools" / "spritegen" / "mannequin.toml"


def look_with(tmp_path, anims: str):
    from spritegen.look import load_look

    path = tmp_path / "keyed.toml"
    path.write_text(MANNEQUIN.read_text(encoding="utf-8") + "\n" + anims, encoding="utf-8")
    return load_look(path)


SWING = """
[anims.heavy]
fps = 12
phases = [1, 1, 1]
tween = 2

[[anims.heavy.right]]
lean = -2
hand_r = [-6, -4]

[[anims.heavy.right]]
lean = 3
hand_r = [12, -8]
foot_r = [4, 0]

[[anims.heavy.right]]
hand_r = [3, -3]

[[anims.heavy.down]]
hand_r = [2, -6]

[[anims.heavy.down]]
hand_r = [-6, -3]
big_hand_r = true

[[anims.heavy.down]]
hand_r = [-1, -2]

[anims.special_wave]
loop = true

[[anims.special_wave.down]]
hand_r = [0, -18]
"""


def test_blend_goes_from_one_key_to_the_next():
    a, b = Pose(lean=-2, hand_r=(0, 0)), Pose(lean=2, hand_r=(10, -4), big_hand_r=True)
    middle = blend(a, b, 0.5)
    assert middle.lean == 0 and middle.hand_r == (5, -2)
    assert blend(a, b, 0) == a and blend(a, b, 1) == b
    assert not blend(a, b, 0.25).big_hand_r and blend(a, b, 0.75).big_hand_r


def test_in_betweens_follow_each_key_and_count_in_its_phase():
    keys = (Pose(lean=0), Pose(lean=3), Pose(lean=6))
    anim = KeyAnim({v: keys for v in DIRECTIONS}, phases=(1, 1, 1), tween=2)
    assert [round(p.lean, 3) for p in anim.frames("down")] == [0, 1, 2, 3, 4, 5, 6]
    assert anim.frame_phases() == [3, 3, 1]
    looping = KeyAnim({v: keys[:2] for v in DIRECTIONS}, loop=True, tween=1)
    assert [p.lean for p in looping.frames("right")] == [0, 1.5, 3, 1.5]


def test_a_look_replaces_a_generated_animation_and_adds_new_ones(tmp_path):
    look = look_with(tmp_path, SWING)
    sheet, spec = build_sheet(look)
    table = look_animations(look, "right")
    fps, loop, phases, frames = table["heavy"]
    assert len(frames) == 7 and phases == [3, 3, 1] and not loop
    assert frames[3].hand_r == (12, -8)  # the second key, after two in-betweens
    assert "[anims.special_wave]" in spec and "kick" in table  # generated ones stay
    sprites = SheetSprites(sheet, tomllib.loads(spec))
    assert sprites.spec("heavy").frames == 7 and sprites.spec("heavy").phases == (3, 3, 1)


def test_a_view_left_out_copies_another(tmp_path):
    look = look_with(tmp_path, SWING)
    heavy = look.anims["heavy"]
    assert heavy.views["up"] == heavy.views["down"]  # up copies down before profile
    wave = look.anims["special_wave"]
    assert wave.views["right"] == wave.views["up"] == wave.views["down"]


@pytest.mark.parametrize(
    "bad, message",
    [
        ("[anims.heavy]\nfps = 12\n", "no key poses"),
        ("[[anims.heavy.down]]\nhand = [1, 2]\n", "unknown pose settings"),
        ("[[anims.heavy.down]]\nhand_r = [1]\n", "two numbers"),
        ("[anims.heavy]\nspeed = 2\n[[anims.heavy.down]]\nlean = 1\n", "unknown settings"),
        (
            "[[anims.heavy.down]]\nlean = 1\n[[anims.heavy.right]]\nlean = 1\n"
            "[[anims.heavy.right]]\nlean = 2\n",
            "same number",
        ),
        ("[anims.heavy]\nphases = [1, 1]\n[[anims.heavy.down]]\nlean = 1\n", "phases"),
        ("[anims.heavy]\ntween = -1\n[[anims.heavy.down]]\nlean = 1\n", "tween"),
    ],
)
def test_bad_key_poses_are_refused_with_a_clear_message(tmp_path, bad, message):
    with pytest.raises(ValueError, match=message):
        look_with(tmp_path, bad)
