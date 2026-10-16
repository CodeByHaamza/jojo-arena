"""Every ultimate's cutscene is played, frame by frame, and drawn.

The other cutscene tests check the rules around them (the opening blow has to land, the
fight holds, the finish lands). This one makes sure each one actually *runs*: a script
that reaches for a method that is not there, or draws outside the surface, fails here
instead of in the middle of someone's fight.
"""

import pygame
import pytest
from helpers import make_duel

from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.combat.cutscene import Cutscene
from jojo_arena.stages import load_stage
from jojo_arena.ui.cutscenes import CUTSCENES, make_cutscene
from jojo_arena.ui.fight_view import FightView

SCREEN = (480, 270)


def owners() -> list[tuple[str, str]]:
    """(cutscene name, the fighter whose move plays it) for every cutscene in the game."""
    found: dict[str, str] = {}
    for fighter in load_roster():
        for move in fighter.kit.all_moves():
            if move.cinematic:
                found.setdefault(move.cinematic, fighter.id)
    return sorted(found.items())


def test_every_cutscene_in_the_registry_belongs_to_somebody():
    assert {name for name, _ in owners()} == set(CUTSCENES)


@pytest.mark.parametrize(("name", "fighter_id"), owners(), ids=[n for n, _ in owners()])
def test_a_cutscene_plays_and_draws_from_end_to_end(name, fighter_id, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    try:
        opponent = "jotaro_p3" if fighter_id != "jotaro_p3" else "dio_p3"
        match = make_duel(fighter_id, opponent, p1=(170, 130), p2=(240, 130))
        defs = [get_fighter(fighter_id), get_fighter(opponent)]
        view = FightView(load_stage("cairo_night"), defs)
        move = next(m for m in defs[0].kit.all_moves() if m.cinematic == name)
        scene = Cutscene(name, 0, 1, move.cinematic_f, move.cinematic_f, move, serial=1)
        player = make_cutscene(view, match, scene)
        surface = pygame.Surface(SCREEN)
        for frame in range(move.cinematic_f + 1):
            player.update(frame)
            player.draw(surface)
    finally:
        pygame.display.quit()
