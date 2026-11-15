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


# The select screen ---------------------------------------------------------------------

import pygame  # noqa: E402
import pytest  # noqa: E402

from jojo_arena import controls  # noqa: E402
from jojo_arena.context import GameContext  # noqa: E402
from jojo_arena.engine.display import Display  # noqa: E402
from jojo_arena.engine.input import KEY_SCANCODES, InputManager  # noqa: E402
from jojo_arena.engine.scene import SceneManager  # noqa: E402
from jojo_arena.ui.select_scene import CharacterSelectScene  # noqa: E402


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    config, _ = controls.parse_controls(None)
    context = GameContext(
        Display("test", (480, 270)), InputManager(), SceneManager(), config, tmp_path / "c.json"
    )
    yield context
    pygame.display.quit()


def keys(ctx, *names: str):
    for name in names:
        code = KEY_SCANCODES[name]
        ctx.inputs.handle_event(pygame.event.Event(pygame.KEYDOWN, scancode=code, key=0, mod=0))
        ctx.inputs.handle_event(pygame.event.Event(pygame.KEYUP, scancode=code, key=0, mod=0))
        ctx.inputs.begin_step()
        ctx.scenes.current.update()
        ctx.scenes.apply_pending()
        ctx.scenes.current.draw(ctx.display.surface)


def select_on(ctx, tmp_path, mode="versus", fighter="jotaro_p3"):
    """The select screen, the cursor on a fighter whose sheets have the test poses."""
    select = CharacterSelectScene(ctx, mode, cursor=fighter)
    index = [f.id for f in select.roster].index(fighter)
    select.looks[index].sprites = posed_sheet(tmp_path)
    select.looks[index].stand = posed_sheet(tmp_path, "[[poses.together.down]]\nlean = -2\n")
    ctx.scenes.switch(select)
    ctx.scenes.apply_pending()
    keys(ctx)  # one step, nothing pressed
    return select


def test_picking_a_fighter_with_poses_opens_the_pose_step(ctx, tmp_path):
    select = select_on(ctx, tmp_path)
    keys(ctx, "Return")
    assert select.choosing == 0 and select.picks == []
    assert select.loadout == Loadout("alone", "together")


def test_left_right_change_the_pose_up_down_the_line_enter_confirms(ctx, tmp_path):
    select = select_on(ctx, tmp_path)
    keys(ctx, "Return", "Right")
    assert select.loadout.pose == "alone_too"
    keys(ctx, "Right")  # around again
    assert select.loadout.pose == "alone"
    keys(ctx, "Left", "Down", "Right")  # only one pose with the Stand: it stays
    assert select.loadout == Loadout("alone_too", "together")
    keys(ctx, "Return")
    assert select.choosing is None and select.fighter_ids == ("jotaro_p3",)
    assert ctx.loadouts[0] == Loadout("alone_too", "together")
    assert ctx.settings.poses["jotaro_p3"] == ["alone_too", "together"]


def test_back_leaves_the_pose_step_without_picking(ctx, tmp_path):
    select = select_on(ctx, tmp_path)
    keys(ctx, "Return", "Escape")
    assert select.choosing is None and select.picks == []


def test_the_last_choice_is_offered_first(ctx, tmp_path):
    ctx.settings.poses = {"jotaro_p3": ["alone_too", "together"]}
    select = select_on(ctx, tmp_path)
    keys(ctx, "Return")
    assert select.loadout == Loadout("alone_too", "together")


def test_a_fighter_without_poses_is_picked_at_once(ctx, tmp_path):
    select = select_on(ctx, tmp_path)
    keys(ctx, "Right")  # the next fighter, given a sheet with no poses at all
    hovered = select.roster[select.cursor]
    select.looks[select.cursor].sprites = posed_sheet(tmp_path, "")
    keys(ctx, "Return")
    assert select.choosing is None and select.fighter_ids == (hovered.id,)


def test_the_computer_side_skips_the_pose_step(ctx, tmp_path):
    select = select_on(ctx, tmp_path, mode="vs_cpu")
    keys(ctx, "Return", "Return")  # player 1: pick, then confirm the poses
    assert select.picking == 1
    index = [f.id for f in select.roster].index("jotaro_p3")
    select.cell = select.grid().index(index)  # the computer gets Jotaro too
    keys(ctx, "Return")
    assert select.choosing is None


def test_the_settings_keep_the_poses(tmp_path):
    from jojo_arena.settings import load_settings, parse_settings, save_settings

    settings = parse_settings({"poses": {"jotaro_p3": ["a", "b"], "bad": "x", "worse": [1, 2]}})
    assert settings.poses == {"jotaro_p3": ["a", "b"]}
    save_settings(settings, tmp_path / "s.json")
    assert load_settings(tmp_path / "s.json").poses == {"jotaro_p3": ["a", "b"]}


# The poses of the roster ---------------------------------------------------------------

from jojo_arena.characters import load_roster  # noqa: E402
from jojo_arena.paths import SPRITES_DIR  # noqa: E402

# The parts whose fighters strike their real poses.
POSED_PARTS = {1, 2, 3}
# Three poses alone, except where the sources run out (15/11/2026): nothing is invented to
# fill the gap, the owner is told instead. Bruford, Tarkus, Straizo and Santana have no
# gallery on JoJo Wiki and are in neither All-Star Battle R nor Eyes of Heaven: they keep
# the generic pose. Zeppeli, Speedwagon, Wamuu and Esidisi have one or two sourced poses.
POSES_ALONE = {
    "bruford": 0,
    "tarkus": 0,
    "straizo": 0,
    "santana": 0,
    "zeppeli": 1,
    "speedwagon": 2,
    "wamuu": 2,
    "esidisi": 2,
}


def _sheet(name: str) -> SheetSprites:
    base = SPRITES_DIR / name
    return SheetSprites.load(base.with_suffix(".png"), base.with_suffix(".toml"))


@pytest.mark.parametrize(
    "fighter",
    [f for f in load_roster() if f.selectable and f.part in POSED_PARTS],
    ids=lambda f: f.id,
)
def test_every_fighter_of_a_posed_part_has_its_poses(fighter):
    poses = _sheet(fighter.sprite).poses
    alone = [p for p in poses.values() if not p.stand]
    wanted = POSES_ALONE.get(fighter.id, 3)
    assert len(alone) >= wanted, f"{fighter.id}: {len(alone)} poses alone"
    for pose in poses.values():
        assert pose.label and pose.label_en and pose.source, f"{fighter.id}: {pose.id}"
    if fighter.stand_sprite:
        together = [p for p in poses.values() if p.stand]
        assert len(together) >= 2, f"{fighter.id}: {len(together)} poses with the Stand"
        stand = _sheet(fighter.stand_sprite)
        for pose in together:
            assert f"pose_{pose.id}" in stand.specs, f"{fighter.stand_sprite} lacks {pose.id}"


# Final review fixes ---------------------------------------------------------------------


def test_a_posing_stand_is_layered_where_it_is_drawn(tmp_path):
    from jojo_arena.stages import load_stage
    from jojo_arena.ui.fight_view import FightView

    match = make_duel("jotaro_p3", "mannequin_blue")
    stand_out(match)
    view = FightView(
        load_stage("cairo_night"), [get_fighter("jotaro_p3"), get_fighter("mannequin_blue")]
    )
    jotaro_view = view.fighter_views[0]
    jotaro_view.sprites = posed_sheet(tmp_path)
    jotaro_view.loadout = resolve_loadout(jotaro_view.sprites, None)
    fighter = posing(match)
    spot = jotaro_view.stand_draw_spot(fighter)
    assert spot != fighter.stand_spot()
    assert view.stand_layer_y(fighter) == spot.y


def test_the_stand_keeps_its_side_when_its_user_turns(tmp_path):
    match = make_duel("jotaro_p3", "mannequin_blue")
    stand_out(match)
    view = view_with("jotaro_p3", posed_sheet(tmp_path), None)
    fighter = posing(match)
    fighter.facing = Vec2(1, 0)
    right = view.stand_draw_spot(fighter) - fighter.pos
    fighter.facing = Vec2(-1, 0)
    left = view.stand_draw_spot(fighter) - fighter.pos
    # Ahead follows the facing; aside stays on the same side of the screen (the profile
    # sprite is mirrored, the composition must not flip from behind to in front).
    assert right.x == -left.x and right.y == left.y == 6


def test_the_preview_puts_the_stand_where_the_pose_does():
    from jojo_arena.ui.portraits import stand_feet

    feet = (100.0, 150.0)
    ahead = stand_feet(feet, 2, flip=False, offset=(9, 6))
    behind = stand_feet(feet, 2, flip=False, offset=(-9, 6))
    assert ahead[0] > feet[0] > behind[0]
    assert stand_feet(feet, 2, flip=True, offset=(9, 6))[0] < feet[0]  # facing left
    assert stand_feet(feet, 2, flip=False, offset=None)[0] < feet[0]  # the usual: behind


def test_kars_keeps_his_pose_once_he_is_the_ultimate_life_form():
    kars = _sheet(get_fighter("kars").sprite)
    ultimate = _sheet(get_fighter("kars").body_sprites["ultimate"])
    for pose_id in kars.poses:
        assert f"pose_{pose_id}" in ultimate.specs, pose_id


def test_the_engine_names_no_jojo():
    from pathlib import Path

    engine = Path(__file__).resolve().parents[1] / "jojo_arena" / "engine"
    for path in engine.glob("*.py"):
        text = path.read_text(encoding="utf-8").replace("jojo_arena", "")
        assert "jojo" not in text.lower(), path.name
