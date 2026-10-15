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


def test_a_rush_clash_cuts_to_the_duel_screen_and_back():
    import os

    import pygame
    from helpers import NONE, press, run_until

    from jojo_arena.combat.match import Match
    from jojo_arena.combat.rules import load_rules
    from jojo_arena.engine.geometry import Vec2
    from jojo_arena.stages import load_stage
    from jojo_arena.ui.fight_view import FightView

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    stage = load_stage("cairo_night")
    defs = [f for f in load_roster() if f.id in ("jotaro_p3", "dio_p3")]
    arena = stage.build_arena()
    match = Match((defs[0].kit, defs[1].kit), load_rules(), arena)
    match.fighters[1].pos = match.fighters[0].pos + Vec2(36, 0)
    view = FightView(stage, defs)
    surface = pygame.Surface((480, 270))

    def step(p1=NONE, p2=NONE):
        events = match.step((p1, p2))
        view.on_events(events, match)
        view.update(match)
        view.draw(surface, match)

    for i in range(2):
        frames = [NONE, NONE]
        frames[i] = press("stand")
        step(*frames)
        run_until(match, lambda m, i=i: m.fighters[i].can_act(), 60)
    step(press("heavy"), press("heavy"))
    for _ in range(30):
        if match.clash is not None:
            break
        step()
    assert match.clash is not None and view.duel is not None
    for _ in range(match.clash.frames_left + 5):
        step(press("light"), NONE)
    assert match.clash is None and view.duel is None
    pygame.display.quit()
