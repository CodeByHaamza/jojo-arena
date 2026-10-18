"""What the arena does on its own: the chandelier, the spikes, oil and snow underfoot,
and the options chosen before the fight (sun, events)."""

from helpers import NONE, hold, walk

from jojo_arena.characters import get_fighter
from jojo_arena.combat.fighter import State
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2
from jojo_arena.stages import load_stage
from jojo_arena.stages.base import StageOptions

RULES = load_rules()


def duel(stage_id: str, p1: str, p2: str, options=None, at=((200, 150), (280, 150))) -> Match:
    stage = load_stage(stage_id)
    match = Match((get_fighter(p1).kit, get_fighter(p2).kit), RULES, stage.build_arena(options))
    for fighter, spot in zip(match.fighters, at, strict=True):
        fighter.pos = Vec2(*spot)
    return match


def step_until(match: Match, kind: str, limit: int, p1=NONE, p2=NONE) -> list:
    events = []
    for _ in range(limit):
        step = match.step((p1, p2))
        events += step
        if any(e.kind == kind for e in step):
            return events
    raise AssertionError(f"no '{kind}' in {limit} steps")


# Options ------------------------------------------------------------------------------


def test_the_sun_can_be_left_out_or_up_from_the_start():
    stage = load_stage("joestar_mansion")
    assert not stage.build_arena(StageOptions(sun="off")).sun_windows
    dawn = stage.build_arena(StageOptions(sun="dawn"))
    day = stage.build_arena(StageOptions(sun="day"))
    assert dawn.sun_after_f > 0
    assert day.sun_windows and day.sun_after_f == 0 and day.sun_spread(0) == 1.0


def test_options_survive_a_replay_file():
    options = StageOptions(sun="day", events=False)
    assert StageOptions.from_data(options.to_data()) == options


def test_events_off_means_nothing_falls():
    arena = load_stage("joestar_mansion").build_arena(StageOptions(events=False))
    assert not arena.hazards.drops and not arena.hazards.zones


# The chandelier -----------------------------------------------------------------------


def test_the_chandelier_marks_its_spot_then_crushes_through_a_guard():
    match = duel("joestar_mansion", "jonathan", "dio_p1", at=((240, 146), (420, 220)))
    drop = match.arena.hazards.drops[0]
    events = step_until(match, "hazard_warn", drop.defn.first_f + 2, p1=hold("guard"))
    warned = next(e for e in events if e.kind == "hazard_warn")
    assert warned.pos == Vec2(240, 146), "over whoever's turn it is: Jonathan, first"
    hp = match.fighters[0].hp
    events = step_until(match, "hazard_drop", drop.defn.warning_f + 2, p1=hold("guard"))
    jonathan = match.fighters[0]
    assert jonathan.hp == hp - drop.defn.damage, "no guard holds against it"
    assert jonathan.state == State.HITSTUN
    assert match.fighters[1].hp == match.fighters[1].max_hp, "far from it, nothing"


def test_the_chandelier_takes_turns_and_keeps_falling():
    match = duel("joestar_mansion", "jonathan", "dio_p1", at=((150, 128), (330, 128)))
    drop = match.arena.hazards.drops[0]
    first = next(
        e
        for e in step_until(match, "hazard_warn", drop.defn.first_f + 2)
        if e.kind == "hazard_warn"
    )
    second = next(
        e
        for e in step_until(match, "hazard_warn", drop.defn.every_f + 2)
        if e.kind == "hazard_warn"
    )
    assert first.pos != second.pos, "the second one is for the other fighter"


# Air Supplena -------------------------------------------------------------------------


def spikes_on(target: str) -> tuple[int, list]:
    """The target, knocked fast into the west pit."""
    match = duel("air_supplena", "jotaro_p3", target, at=((300, 150), (90, 150)))
    victim = match.fighters[1]
    victim.take_hit(0, 30, Vec2(-6, 0), False)
    events = []
    for _ in range(20):
        events += match.step((NONE, NONE))
    return victim.max_hp - victim.hp, events


def test_knocked_into_the_pit_the_spikes_come_up():
    hurt, events = spikes_on("dio_p1")
    assert any(e.kind == "hazard_spikes" for e in events)
    assert hurt > 0


def test_the_spikes_spare_a_ripple_user():
    """Eyes of Heaven: the spikes of Air Supplena hurt everyone but Ripple users."""
    hurt, events = spikes_on("caesar")
    assert any(e.kind == "hazard_spikes" for e in events)
    assert hurt == 0


def slide_after_walking(fighter_id: str, stage_id: str, at) -> float:
    """Walk right for a while, let go, and measure how far the body still goes."""
    match = duel(stage_id, fighter_id, "mannequin_blue", at=(at, (440, 240)))
    for _ in range(30):
        match.step((walk(1.0), NONE))
    stop = match.fighters[0].pos.x
    for _ in range(30):
        match.step((NONE, NONE))
    return match.fighters[0].pos.x - stop


def test_oil_carries_you_on_unless_you_breathe_the_ripple():
    assert slide_after_walking("jotaro_p3", "air_supplena", (186, 110)) > 10
    assert slide_after_walking("joseph_p2", "air_supplena", (186, 110)) == 0
    assert slide_after_walking("jotaro_p3", "cairo_night", (186, 110)) == 0


def test_in_st_moritz_nobody_keeps_their_footing():
    assert slide_after_walking("joseph_p2", "st_moritz", (100, 160)) > 10


def test_a_body_starts_slowly_on_snow():
    match = duel("st_moritz", "jotaro_p3", "mannequin_blue", at=((100, 160), (440, 240)))
    start = match.fighters[0].pos.x
    match.step((walk(1.0), NONE))
    first_step = match.fighters[0].pos.x - start
    assert 0 < first_step < match.fighters[0].walk_speed() * 0.5


def test_a_stage_without_hazards_plays_exactly_as_before():
    """No surface: walking is the old one-to-one walk, to the bit."""
    match = duel("cairo_night", "jotaro_p3", "mannequin_blue")
    jotaro = match.fighters[0]
    start = jotaro.pos.copy()
    match.step((walk(1.0), NONE))
    assert jotaro.pos == start + Vec2(1.0, 0) * jotaro.walk_speed()
