"""DIO's mansion: daylight outside, curtains that keep it out until they are torn down,
and Nukesaku jumping down on whoever is in reach, again and again."""

from helpers import NONE

from jojo_arena.characters import get_fighter
from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Rect, RoundedRect, Vec2
from jojo_arena.stages import STAGE_IDS, load_stage, stage_for_part
from jojo_arena.stages.base import StageOptions

RULES = load_rules()


# The engine: a window shaded by something ------------------------------------------------------


def shaded_arena() -> Arena:
    window = Rect(100, 10, 40, 30)
    curtain = Obstacle("curtain", Rect(100, 40, 40, 6), 30)
    return Arena(
        RoundedRect(Rect(0, 0, 400, 200), 10),
        (Vec2(120, 100), Vec2(300, 100)),
        [curtain],
        sun_windows=[window],
        sun_blinds={0: 0},
    )


def test_a_window_shaded_by_something_standing_lets_no_sun_in():
    arena = shaded_arena()
    under = Vec2(120, 100)
    assert not arena.in_sun(under)
    assert arena.lit_windows() == []
    arena.obstacles[0].broken = True  # torn down
    assert arena.in_sun(under)
    assert arena.lit_windows() == [arena.sun_windows[0]]


def test_a_window_with_nothing_in_front_is_lit_as_before():
    arena = shaded_arena()
    arena.sun_blinds = {}
    assert arena.in_sun(Vec2(120, 100))


# The stage --------------------------------------------------------------------------------


def duel(p1="dio_p3", p2="jotaro_p3", options=None, at=((240, 120), (300, 120))) -> Match:
    stage = load_stage("dio_mansion")
    match = Match((get_fighter(p1).kit, get_fighter(p2).kit), RULES, stage.build_arena(options))
    for fighter, spot in zip(match.fighters, at, strict=True):
        fighter.pos = Vec2(*spot)
    return match


def test_the_mansion_is_an_arena_of_part_three_that_cairo_still_opens():
    assert "dio_mansion" in STAGE_IDS
    stage = load_stage("dio_mansion")
    assert stage.part == 3 and stage.has_sun and stage.has_events
    assert stage_for_part(3) == "cairo_night"  # the part's first arena stays Cairo


def test_every_window_of_the_mansion_has_its_curtain():
    arena = duel().arena
    assert arena.sun_windows and set(arena.sun_blinds) == set(range(len(arena.sun_windows)))
    for obstacle_index in arena.sun_blinds.values():
        assert arena.obstacles[obstacle_index].kind == "curtain"


def test_it_is_broad_daylight_outside_but_the_curtains_keep_it_out():
    match = duel(at=((0, 0), (0, 0)))
    arena = match.arena
    window = arena.sun_windows[0]
    spot = Vec2(window.x + window.w / 2, window.bottom + 20)
    match.fighters[0].pos = spot.copy()
    match.fighters[1].pos = Vec2(spot.x + 200, spot.y + 60)
    for _ in range(10):
        match.step((NONE, NONE))
    assert match.sun_active and not match.fighters[0].in_sun  # DIO, safe behind the curtain
    arena.obstacles[arena.sun_blinds[0]].broken = True
    for _ in range(10):
        match.step((NONE, NONE))
    assert match.fighters[0].in_sun


def test_a_torn_curtain_stays_down_for_the_round():
    arena = duel().arena
    curtain = arena.obstacles[arena.sun_blinds[0]]
    assert curtain.respawn_f == 0 and not curtain.throwable


def test_with_the_sun_off_there_is_no_window_at_all():
    arena = duel(options=StageOptions(sun="off")).arena
    assert arena.sun_windows == [] and arena.sun_blinds == {}


def test_nukesaku_jumps_down_on_whoever_is_there_and_comes_back():
    match = duel()
    drop = next(d for d in match.arena.hazards.drops if d.defn.look == "nukesaku")
    landed = 0
    for _ in range(drop.defn.first_f + 2 * drop.defn.every_f + 5):
        events = match.step((NONE, NONE))
        landed += sum(1 for e in events if e.kind == "hazard_drop")
    assert landed >= 3  # unlimited: again and again
    assert any(f.hp < f.max_hp for f in match.fighters)


def test_with_events_off_nukesaku_stays_away():
    match = duel(options=StageOptions(events=False))
    assert match.arena.hazards.drops == []
