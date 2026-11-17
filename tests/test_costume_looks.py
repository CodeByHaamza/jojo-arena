"""Look files that are costumes of another look, and the colours a look carries: what the
generator reads, what it refuses, and what it writes into the sheet for the game."""

import tomllib
from pathlib import Path

import pygame
import pytest
from spritegen.look import load_look, ramp
from spritegen.sheet import build_sheet, check_recolor_keys, recolor_slots

from jojo_arena.engine.sprites import SheetSprites, parse_color
from jojo_arena.paths import SPRITES_DIR

ROOT = Path(__file__).resolve().parents[1]
MANNEQUIN = ROOT / "tools" / "spritegen" / "mannequin.toml"
LOOKS = [MANNEQUIN, *sorted((ROOT / "jojo_arena" / "characters" / "looks").glob("*.toml"))]

BASE = """
name = "Hero"
pose = "point"

[build]
torso = 14

[palette]
skin = "#e8b890"
shirt = "#3d63c8"
trousers = "#8c909e"
boots = "#3a2c28"

[body]
head = "skin"
torso = "shirt"
arms = "skin"
hands = "skin"
legs = "trousers"
feet = "boots"

[face]
eyes = "outline"
brows = true

[[parts]]
type = "belt"
material = "boots"

[poses.point]
label = "Le doigt"
label_en = "The finger"
source = "ch. 1"

[[poses.point.down]]
lean = 1
"""

COLORS = """
[costume]
label = "Tenue du voyage"
label_en = "Travelling clothes"
source = "ch. 1"

[colors.anime]
label = "Anime"
label_en = "Anime"
source = "the anime"

[colors.cover]
label = "Tome 4"
label_en = "Volume 4"
source = "cover of volume 4"
stand = "gold"

[colors.cover.palette]
shirt = "#40a040"
trousers = ["#101010", "#202020", "#303030", "#404040"]
"""


def write(tmp_path, name: str, text: str):
    path = tmp_path / f"{name}.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_costume_starts_from_its_base_and_says_only_what_changes(tmp_path):
    write(tmp_path, "hero", BASE)
    costume = load_look(
        write(
            tmp_path,
            "hero_bare",
            'base = "hero"\n\n[palette]\ntrousers = "#704020"\n\n[body]\ntorso = "skin"\n\n'
            '[face]\nbrows = false\n\n[build]\nlegs = 20\n\n[[parts]]\ntype = "boots"\n'
            'material = "boots"\n',
        )
    )
    base = load_look(tmp_path / "hero.toml")
    assert costume.id == "hero_bare" and costume.base == "hero"
    assert costume.name == "Hero" and costume.pose == "point"  # the base's
    assert costume.palette["trousers"] == ramp(parse_color("#704020"))  # its own
    assert costume.palette["shirt"] == base.palette["shirt"]  # the base's, untouched
    assert costume.body["torso"] == "skin" and costume.body["legs"] == "trousers"
    assert costume.face == {"eyes": "outline", "brows": False}
    assert costume.build.legs == 20 and costume.build.torso == 14
    assert [p["type"] for p in costume.parts] == ["boots"]  # its list, not the base's plus it
    assert list(costume.poses) == ["point"] and costume.poses["point"].source == "ch. 1"


def test_a_costume_without_parts_keeps_the_bases(tmp_path):
    write(tmp_path, "hero", BASE)
    costume = load_look(
        write(tmp_path, "hero_white", 'base = "hero"\n\n[palette]\nshirt = "#eeeeee"\n')
    )
    assert [p["type"] for p in costume.parts] == ["belt"]


@pytest.mark.parametrize(
    "extra, message",
    [
        ("[[anims.heavy.down]]\nlean = 1\n", "moves as its base does"),
        (
            "[poses.new]\nlabel='A'\nlabel_en='A'\nsource='s'\n[[poses.new.down]]\nlean=1\n",
            "moves as",
        ),
    ],
)
def test_a_costume_cannot_bring_its_own_animations(tmp_path, extra, message):
    write(tmp_path, "hero", BASE)
    with pytest.raises(ValueError, match=message):
        load_look(write(tmp_path, "hero_bad", 'base = "hero"\n\n' + extra))


def test_a_costume_of_a_look_that_is_not_there_is_refused(tmp_path):
    with pytest.raises(ValueError, match="nobody"):
        load_look(write(tmp_path, "lost", 'base = "nobody"\n'))


def test_a_costume_does_not_inherit_its_bases_colours(tmp_path):
    write(tmp_path, "hero", BASE + COLORS)
    costume = load_look(
        write(tmp_path, "hero_white", 'base = "hero"\n\n[palette]\nshirt = "#eeeeee"\n')
    )
    assert costume.colors == {} and costume.costume is None


def test_colours_go_into_the_sheet_with_their_tones(tmp_path):
    look = load_look(write(tmp_path, "hero", BASE + COLORS))
    assert list(look.colors) == ["anime", "cover"]
    assert look.costume.label_en == "Travelling clothes"
    sheet, spec = build_sheet(look)
    data = tomllib.loads(spec)
    assert data["costume"] == {
        "label": "Tenue du voyage",
        "label_en": "Travelling clothes",
        "source": "ch. 1",
    }
    # The key tones of every material a colour changes, and of those only.
    assert set(data["recolor"]) == {"shirt", "trousers"}
    assert data["recolor"]["shirt"] == [list(c) for c in look.palette["shirt"]]
    cover = data["colors"]["cover"]
    assert (cover["label"], cover["label_en"], cover["source"], cover["stand"]) == (
        "Tome 4",
        "Volume 4",
        "cover of volume 4",
        "gold",
    )
    assert cover["palette"]["shirt"] == [list(c) for c in ramp(parse_color("#40a040"))]
    assert cover["palette"]["trousers"][0] == [16, 16, 16]  # the four tones given by hand
    sprites = SheetSprites(sheet, data)
    assert list(sprites.colors) == ["anime", "cover"] and sprites.colors["cover"].stand == "gold"


def test_the_first_colour_is_the_look_itself(tmp_path):
    look = load_look(write(tmp_path, "hero", BASE + COLORS))
    assert look.colors["anime"].palette == {}
    _, spec = build_sheet(look)
    assert "palette" not in tomllib.loads(spec)["colors"]["anime"]


def test_the_game_repaints_the_generated_sheet_with_a_colour(tmp_path):
    look = load_look(write(tmp_path, "hero", BASE + COLORS))
    sheet, spec = build_sheet(look)
    png, toml = tmp_path / "hero.png", tmp_path / "hero_sheet.toml"
    pygame.image.save(sheet, str(png))
    toml.write_text(spec, encoding="utf-8")
    plain = SheetSprites.load(png, toml)
    green = SheetSprites.load(png, toml, color="cover")
    shirt, painted = set(look.palette["shirt"]), set(ramp(parse_color("#40a040")))

    def tones(sprites):
        frame = sprites.frame("idle", "down", False, 0)
        size = frame.get_size()
        pixels = {tuple(frame.get_at((x, y))) for x in range(size[0]) for y in range(size[1])}
        return {p[:3] for p in pixels if p[3]}

    assert tones(plain) & shirt and not tones(plain) & painted
    assert tones(green) & painted and not tones(green) & shirt
    assert tones(green) & set(look.palette["skin"])  # what no colour names stays


@pytest.mark.parametrize(
    "colors, message",
    [
        ("[colors.a]\nlabel = 'A'\nlabel_en = 'A'\n", "label, label_en and source"),
        (
            "[colors.a]\nlabel='A'\nlabel_en='A'\nsource='s'\n[colors.a.palette]\nshirt='#111111'\n",
            "first colour is the look itself",
        ),
        (
            "[colors.a]\nlabel='A'\nlabel_en='A'\nsource='s'\n"
            "[colors.b]\nlabel='B'\nlabel_en='B'\nsource='s'\n",
            "needs a palette",
        ),
        (
            "[colors.a]\nlabel='A'\nlabel_en='A'\nsource='s'\n"
            "[colors.b]\nlabel='B'\nlabel_en='B'\nsource='s'\n[colors.b.palette]\ncape='#111111'\n",
            "unknown color 'cape'",
        ),
        ("[costume]\nlabel = 'A'\n", "label, label_en and source"),
    ],
)
def test_bad_colours_are_refused_with_a_clear_message(tmp_path, colors, message):
    with pytest.raises(ValueError, match=message):
        load_look(write(tmp_path, "hero", BASE + colors))


def test_two_materials_sharing_a_tone_are_refused_by_name(tmp_path):
    same = BASE.replace('boots = "#3a2c28"', 'boots = "#3d63c8"')  # the shirt's very blue
    look = load_look(write(tmp_path, "hero", same + COLORS))
    with pytest.raises(ValueError, match="'shirt' and 'boots' share the tone #"):
        check_recolor_keys(look)
    with pytest.raises(ValueError, match="share the tone"):
        build_sheet(look)


def test_materials_no_colour_touches_may_share_tones(tmp_path):
    same = BASE.replace('boots = "#3a2c28"', 'boots = "#e8b890"')  # the skin's tone
    look = load_look(write(tmp_path, "hero", same + COLORS))
    assert recolor_slots(look) == ["shirt", "trousers"]
    check_recolor_keys(look)  # neither skin nor boots is repainted: nothing to mix up


def test_a_look_without_colours_writes_no_colour_tables(tmp_path):
    look = load_look(write(tmp_path, "hero", BASE))
    _, spec = build_sheet(look)
    data = tomllib.loads(spec)
    assert "colors" not in data and "costume" not in data and "recolor" not in data


@pytest.mark.parametrize("path", LOOKS, ids=lambda p: p.stem)
def test_generated_sheet_descriptions_are_up_to_date(path):
    """The TOML beside each PNG must match its look file too: the colours live there."""
    look = load_look(path)
    _, spec = build_sheet(look)
    on_disk = (SPRITES_DIR / look.id / f"{look.id}.toml").read_text(encoding="utf-8")
    assert spec == on_disk.replace("\r\n", "\n"), (
        f"{look.id}: regenerate with python tools/make_sprites.py {look.id}"
    )
