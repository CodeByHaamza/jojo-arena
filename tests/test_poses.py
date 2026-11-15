"""Poses: the one picked on the select screen is the one the Pose key plays, the Stand
strikes its own beside its user, and nothing breaks when a pose is missing."""

import random
import tomllib

from helpers import hold, make_duel, press, run, run_held
from spritegen.look import load_look
from spritegen.sheet import build_sheet

from jojo_arena.characters import get_fighter
from jojo_arena.combat.fighter import State
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.sprites import SheetSprites
from jojo_arena.ui.fight_view import FighterView
from jojo_arena.ui.loadout import Loadout, random_loadout, resolve_loadout

MANNEQUIN_LOOK = "tools/spritegen/mannequin.toml"

POSES = """
[poses.alone]
label = "Seul"
label_en = "Alone"
source = "test"
[[poses.alone.down]]
lean = 1

[poses.alone_too]
label = "Seul aussi"
label_en = "Alone too"
source = "test"
[[poses.alone_too.down]]
lean = -1

[poses.together]
label = "Ensemble"
label_en = "Together"
source = "test"
stand = true
stand_offset = [-10, 6]
[[poses.together.down]]
lean = 2
"""


def posed_sheet(tmp_path, extra=POSES) -> SheetSprites:
    path = tmp_path / "posed.toml"
    with open(MANNEQUIN_LOOK, encoding="utf-8") as handle:
        path.write_text(handle.read() + "\n" + extra, encoding="utf-8")
    sheet, spec = build_sheet(load_look(path))
    return SheetSprites(sheet, tomllib.loads(spec))


def view_with(fighter_id, sprites, loadout, stand_sprites=None) -> FighterView:
    view = FighterView(get_fighter(fighter_id))
    view.sprites = sprites
    if stand_sprites is not None:
        view.stand = stand_sprites
    view.loadout = resolve_loadout(sprites, loadout)
    return view


def stand_out(match) -> None:
    """Call the Stand out (one press), and let the switch finish."""
    run(match, 40, press("stand"), hold())
    assert match.fighters[0].aura_active


def posing(match, side=0):
    p = (hold("pose"), hold()) if side == 0 else (hold(), hold("pose"))
    run_held(match, 3, *p)
    fighter = match.fighters[side]
    assert fighter.state == State.POSE
    return fighter


def test_a_loadout_fills_itself_from_the_sheet(tmp_path):
    sprites = posed_sheet(tmp_path)
    assert resolve_loadout(sprites, None) == Loadout("alone", "together")
    assert resolve_loadout(sprites, Loadout("alone_too", "")) == Loadout("alone_too", "together")


def test_a_pose_that_is_gone_falls_back(tmp_path):
    sprites = posed_sheet(tmp_path)
    # An old settings.json names poses this sheet does not have any more.
    assert resolve_loadout(sprites, Loadout("deleted", "gone")) == Loadout("alone", "together")
    # A solo pose cannot stand in for a duo one, nor the reverse.
    assert resolve_loadout(sprites, Loadout("together", "alone")) == Loadout("alone", "together")
    # A sheet with no poses at all: nothing to name, the generic pose plays.
    assert resolve_loadout(posed_sheet(tmp_path, ""), Loadout("alone", "")) == Loadout("", "")


def test_the_computer_picks_one_of_each_kind(tmp_path):
    sprites = posed_sheet(tmp_path)
    picks = {random_loadout(sprites, random.Random(seed)) for seed in range(30)}
    assert {p.pose for p in picks} == {"alone", "alone_too"}
    assert {p.stand_pose for p in picks} == {"together"}


def test_the_pose_key_plays_the_chosen_pose(tmp_path):
    match = make_duel("mannequin_red", "mannequin_blue")
    view = view_with("mannequin_red", posed_sheet(tmp_path), Loadout("alone_too", ""))
    fighter = posing(match)
    assert view.pose_anim(fighter) == "pose_alone_too"
    assert view.resolve(view.sprites, view.pose_anim(fighter))[0] == "pose_alone_too"


def test_with_no_pose_named_the_generic_one_plays(tmp_path):
    match = make_duel("mannequin_red", "mannequin_blue")
    view = view_with("mannequin_red", posed_sheet(tmp_path, ""), None)
    assert view.pose_anim(posing(match)) == "pose"


def test_with_the_stand_out_it_plays_the_duo_pose_and_the_stand_its_own(tmp_path):
    match = make_duel("jotaro_p3", "mannequin_blue")
    stand_out(match)
    stand_sheet = posed_sheet(tmp_path, "[[poses.together.down]]\nlean = -2\n")
    view = view_with("jotaro_p3", posed_sheet(tmp_path), None, stand_sprites=stand_sheet)
    fighter = posing(match)
    assert view.pose_anim(fighter) == "pose_together"
    assert view.resolve(view.stand, view.pose_anim(fighter))[0] == "pose_together"


def test_a_stand_without_that_pose_plays_its_generic_one(tmp_path):
    match = make_duel("jotaro_p3", "mannequin_blue")
    stand_out(match)
    view = view_with(
        "jotaro_p3", posed_sheet(tmp_path), None, stand_sprites=posed_sheet(tmp_path, "")
    )
    fighter = posing(match)
    assert view.resolve(view.stand, view.pose_anim(fighter))[0] == "pose"


def test_the_stand_stands_where_the_pose_puts_it(tmp_path):
    match = make_duel("jotaro_p3", "mannequin_blue")
    stand_out(match)
    view = view_with("jotaro_p3", posed_sheet(tmp_path), None)
    fighter = posing(match)
    facing = fighter.facing
    beside = Vec2(-facing.y, facing.x)
    expected = fighter.pos + facing * -10 + beside * 6
    spot = view.stand_draw_spot(fighter)
    assert abs(spot.x - expected.x) < 1e-6 and abs(spot.y - expected.y) < 1e-6
    # Not posing: where the simulation keeps it.
    fighter.state = State.IDLE
    assert view.stand_draw_spot(fighter) == fighter.stand_spot()


def test_each_side_of_a_mirror_match_has_its_own_pose(tmp_path):
    match = make_duel("mannequin_red", "mannequin_red")
    sprites = posed_sheet(tmp_path)
    left = view_with("mannequin_red", sprites, Loadout("alone", ""))
    right = view_with("mannequin_red", sprites, Loadout("alone_too", ""))
    run_held(match, 3, hold("pose"), hold("pose"))
    assert left.pose_anim(match.fighters[0]) == "pose_alone"
    assert right.pose_anim(match.fighters[1]) == "pose_alone_too"
