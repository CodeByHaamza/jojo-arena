"""Hitting with what you are carrying, and carrying it with your hair."""

from helpers import kinds, press, run

from jojo_arena.characters import get_fighter
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2
from jojo_arena.stages import load_stage

RULES = load_rules()


def street(who: str, foe: str = "dio_p3", gap: float = 30.0) -> Match:
    """A fight in the Cairo street, `who` standing against the first crate."""
    arena = load_stage("cairo_night").build_arena()
    match = Match((get_fighter(who).kit, get_fighter(foe).kit), RULES, arena)
    crate = next(o for o in arena.obstacles if o.throwable)
    a, b = match.fighters
    a.pos = Vec2(crate.rect.center.x + 6, crate.rect.center.y)
    b.pos = Vec2(a.pos.x + gap, a.pos.y)
    return match


def test_the_heavy_button_swings_what_you_are_carrying():
    match = street("jotaro_p3")
    a, b = match.fighters
    run(match, 2, p1=press("pose"))
    assert a.carrying is not None
    events = run(match, 40, p1=press("heavy"))
    assert "prop_swing" in kinds(events)
    assert b.hp < b.max_hp
    assert a.carrying is not None  # he still has it: he can swing again, or throw it


def test_bruford_swings_it_at_the_length_of_his_hair():
    arms = street("jotaro_p3", gap=52)
    hair = street("bruford", gap=52)
    for match in (arms, hair):
        run(match, 2, p1=press("pose"))
        run(match, 40, p1=press("heavy"))
    assert arms.fighters[1].hp == arms.fighters[1].max_hp  # an arm does not reach that far
    assert hair.fighters[1].hp < hair.fighters[1].max_hp  # his hair does


def test_his_hair_holds_it_so_his_hands_stay_free():
    assert get_fighter("bruford").kit.prop_hold == "hair"
    assert get_fighter("jonathan").kit.prop_hold == "hands"


def test_being_hit_still_drops_it():
    match = street("bruford", gap=26)
    a, b = match.fighters
    run(match, 2, p1=press("pose"))
    assert a.carrying is not None
    run(match, 30, p2=press("light"))
    assert a.carrying is None


def test_hair_reaches_further_but_cannot_throw_as_hard():
    arms = street("jonathan", gap=120)
    hair = street("bruford", gap=120)
    for match in (arms, hair):
        run(match, 2, p1=press("pose"))  # pick it up
        run(match, 2, p1=press("pose"))  # and throw it
        run(match, 60)
    by_arms = arms.fighters[1].max_hp - arms.fighters[1].hp
    by_hair = hair.fighters[1].max_hp - hair.fighters[1].hp
    assert by_arms > by_hair > 0, (by_arms, by_hair)
