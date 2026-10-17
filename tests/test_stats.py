"""What a fight counts about itself, for the screen at the end."""

from helpers import press

from jojo_arena.characters import get_fighter
from jojo_arena.combat.events import Event
from jojo_arena.combat.rounds import Phase, Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.combat.stats import FightStats
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Vec2
from jojo_arena.stages import load_stage

RULES = load_rules()


def duel(p1: str = "jotaro_p3", p2: str = "kakyoin") -> Rounds:
    kits = (get_fighter(p1).kit, get_fighter(p2).kit)
    return Rounds(kits, RULES, load_stage("cairo_night").build_arena, 1)


def test_a_hit_is_counted_for_whoever_landed_it():
    stats = FightStats()
    rounds = duel()
    fighters = rounds.match.fighters
    stats.update([Event("hit", None, 1, 40)], fighters)  # player 2 was hit
    assert stats.sides[0].damage == 40 and stats.sides[0].hits == 1
    assert stats.sides[1].taken == 40 and stats.sides[1].damage == 0


def test_the_biggest_blow_and_the_supers_are_remembered():
    stats = FightStats()
    fighters = duel().match.fighters
    for damage in (30, 160, 70):
        stats.update([Event("hit", None, 1, damage)], fighters)
    stats.update([Event("gha", None, 0)], fighters)
    assert stats.sides[0].biggest_hit == 160
    assert stats.sides[0].supers == 1


def test_a_whole_fight_fills_the_sheet():
    rounds = duel()
    for i in range(600):
        a, b = rounds.match.fighters
        if rounds.phase == Phase.FIGHT:
            b.pos = Vec2(a.pos.x + 20, a.pos.y)  # keep them in each other's face
        rounds.step((press("light") if i % 14 == 0 else InputFrame(), InputFrame()))
    side = rounds.stats.sides[0]
    assert side.hits > 5 and side.damage > 100
    assert side.best_combo_hits >= 2 and side.best_combo_damage > 0
    assert rounds.stats.seconds >= 5


def test_the_best_combo_of_the_fight_is_kept_not_the_last_one():
    stats = FightStats()
    rounds = duel()
    attacker, defender = rounds.match.fighters
    for _ in range(4):  # a four-hit combo while he is stuck in hitstun
        defender.state = defender.state.__class__.HITSTUN
        stats.update([Event("hit", None, 1, 25)], rounds.match.fighters)
    assert stats.sides[0].best_combo_hits == 4
    defender.state = defender.state.__class__.IDLE
    stats.update([], rounds.match.fighters)  # the combo ends
    stats.update([Event("hit", None, 1, 10)], rounds.match.fighters)  # a lone later hit
    assert stats.sides[0].best_combo_hits == 4  # the best one stands
