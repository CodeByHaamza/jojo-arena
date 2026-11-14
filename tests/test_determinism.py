"""The same inputs give the same fight, for every fighter in the roster.

The whole project rests on this: a fixed step with no hidden randomness is what makes
replays exact and what would make rollback netplay possible later. One matchup was
checked (test_replay.py); a kit, a mechanic or an effect added later can break it for
one character only, so every one of them is checked here.

What breaks determinism in practice: reading the clock, iterating a set, using `random`
instead of the match's own generator, or keeping state on a class instead of an
instance. All of those show up as a different state after the same inputs.
"""

import random

from helpers import OPEN_BOUNDS

from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.rounds import Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Vec2

RULES = load_rules()
ACTIONS = ("light", "heavy", "special", "stand", "dash", "guard", "heart_heat", "pose", "power_up")


def scripted(seed: int, steps: int) -> list[tuple[InputFrame, InputFrame]]:
    """A fixed sequence of inputs for both sides: the same list every time it is asked."""
    rng = random.Random(seed)
    frames = []
    for _ in range(steps):
        pair = []
        for _ in range(2):
            pressed = {a: 1 for a in ACTIONS if rng.random() < 0.09}
            held = {a for a in ACTIONS if rng.random() < 0.08} | set(pressed)
            move = rng.choice(((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (0.7071, 0.7071)))
            pair.append(InputFrame(move, frozenset(held), pressed))
        frames.append((pair[0], pair[1]))
    return frames


def play(who: str, frames: list[tuple[InputFrame, InputFrame]]) -> tuple:
    """Run the fight and return everything that should come out the same."""

    def arena():
        return Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(230, 100)))

    kits = (get_fighter(who).kit, get_fighter("mannequin_blue").kit)
    rounds = Rounds(kits, RULES, arena, 2)
    kinds = []
    for step, pair in enumerate(frames):
        if step % 150 == 0:
            for fighter in rounds.match.fighters:
                fighter.hh = RULES.hh_max  # supers, cutscenes and awakenings take part
        for event in rounds.step(pair):
            kinds.append((event.kind, event.fighter, round(event.value or 0, 6)))
    match = rounds.match
    return (
        rounds.round_number,
        tuple(rounds.wins),
        tuple(
            (
                f.hp,
                round(f.pos.x, 6),
                round(f.pos.y, 6),
                f.state,
                f.stance,
                round(f.hh, 6),
                round(f.hamon, 6),
                round(f.blood, 6),
                f.awakened,
            )
            for f in match.fighters
        ),
        tuple((round(p.pos.x, 6), round(p.pos.y, 6), p.life) for p in match.projectiles),
        tuple(o.hp for o in match.arena.obstacles),
        tuple(kinds),
    )


def test_every_fighter_plays_the_same_fight_twice():
    frames = scripted(seed=7, steps=420)
    for entry in load_roster():
        if not entry.selectable:
            continue
        first = play(entry.id, frames)
        again = play(entry.id, frames)
        assert first == again, f"{entry.id} does not play the same fight twice"


def test_a_different_seed_really_is_a_different_fight():
    """If every fight came out the same whatever the inputs, the test above would pass
    for the wrong reason."""
    one = play("jotaro_p3", scripted(seed=1, steps=200))
    two = play("jotaro_p3", scripted(seed=2, steps=200))
    assert one != two
