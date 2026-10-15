"""The fight view can draw every state and every move of every character, and its Stand."""

import pytest

from jojo_arena.characters import load_roster
from jojo_arena.ui.fight_view import STATE_ANIMS, FighterView

DIRECTIONS = ("down", "up", "right")


@pytest.mark.parametrize("fighter", load_roster(), ids=lambda f: f.id)
def test_every_move_and_state_has_a_drawable_animation(fighter):
    view = FighterView(fighter)
    sheets = [view.sprites] + ([view.stand] if view.stand is not None else [])
    anims = {move.anim for move in fighter.kit.all_moves()} | set(STATE_ANIMS.values())
    for sprites in sheets:
        for anim in sorted(anims):
            name, spec = FighterView.resolve(sprites, anim)
            assert sprites.spec(name) is not None, (fighter.id, anim)
            for direction in DIRECTIONS:
                for index in range(spec.frames):
                    for flip in (False, True):
                        image = sprites.frame(name, direction, flip, index)
                        assert image.get_width() > 0


def test_an_unknown_animation_falls_back_to_idle():
    view = FighterView(load_roster()[0])
    name, _ = FighterView.resolve(view.sprites, "a_move_nobody_drew")
    assert name == "idle"
