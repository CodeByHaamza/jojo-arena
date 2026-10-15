"""Crash hunt: every pairing fights with random inputs, and every frame is drawn.

Random presses and held buttons reach odd corners (supers mid-stance-switch, time
stops during clashes...) that hand-written tests miss. Seeded, so a failure replays.
"""

import random

import pygame
import pytest

from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.combat.rounds import Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.actions import InputFrame
from jojo_arena.stages import load_stage
from jojo_arena.ui.fight_view import FightView
from jojo_arena.ui.hud import Hud

ACTIONS = ("light", "heavy", "special", "stand", "dash", "guard", "heart_heat", "pose")
DIRECTIONS = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (0.7071, 0.7071), (-0.7071, -0.7071))
FIGHTERS = [f.id for f in load_roster() if f.selectable]
FRAMES = 1200


def random_frame(rng: random.Random) -> InputFrame:
    pressed = {a: 1 for a in ACTIONS if rng.random() < 0.07}
    held = {a for a in ACTIONS if rng.random() < 0.08} | set(pressed)
    return InputFrame(rng.choice(DIRECTIONS), frozenset(held), pressed)


@pytest.fixture(scope="module")
def screen(tmp_path_factory):
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    pygame.display.set_mode((480, 270))
    yield pygame.Surface((480, 270))
    pygame.display.quit()


@pytest.mark.parametrize("p1", FIGHTERS)
@pytest.mark.parametrize("p2", FIGHTERS)
def test_random_fights_never_crash(screen, p1, p2):
    rng = random.Random(f"{p1}-{p2}")
    rules = load_rules()
    stage = load_stage("cairo_night")
    defs = [get_fighter(p1), get_fighter(p2)]
    rounds = Rounds((defs[0].kit, defs[1].kit), rules, stage.build_arena, 3)
    view = FightView(stage, defs)
    hud = Hud(defs, [v.height for v in view.fighter_views])
    for step in range(FRAMES):
        if step % 120 == 0:  # plenty of gauge: supers and time stops come out
            for fighter in rounds.match.fighters:
                fighter.hh = rules.hh_max
        events = rounds.step((random_frame(rng), random_frame(rng)))
        view.on_events(events, rounds.match)
        hud.on_events(events, rounds)
        view.update(rounds.match)
        hud.update(rounds)
        view.draw(screen, rounds.match)
        hud.draw(screen, rounds)
