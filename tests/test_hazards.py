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


# The Swiss castle: its event is the way out --------------------------------------------


def slammed_north(options=None) -> tuple[Match, list]:
    """Wamuu sent hard into the north wall of the hall, where the windows are."""
    match = duel("swiss_castle", "joseph_p2", "wamuu", options, at=((300, 160), (300, 70)))
    match.fighters[1].take_hit(0, 30, Vec2(0, -9), True)
    events = []
    for _ in range(20):
        events += match.step((NONE, NONE))
    return match, events


def test_slammed_through_the_north_wall_the_fight_goes_on_outside():
    match, events = slammed_north()
    assert any(e.kind == "arena_exit" for e in events)
    assert match.arena.name == "st_moritz"
    joseph, wamuu = match.fighters
    assert joseph.pos.y > wamuu.pos.y, "both keep their distance from the broken wall"
    assert match.arena.hazards.surfaces, "and outside, the snow does not grip"


def test_with_events_off_the_wall_holds():
    match, events = slammed_north(StageOptions(events=False))
    assert not any(e.kind == "arena_exit" for e in events)
    assert match.arena.name == "swiss_castle"


def test_st_moritz_is_reached_not_picked():
    from jojo_arena.stages import REACHED_IDS, STAGE_IDS

    assert "st_moritz" in REACHED_IDS and "st_moritz" not in STAGE_IDS


def test_the_view_comes_back_inside_when_the_next_round_starts(monkeypatch):
    import pygame

    from jojo_arena.characters import get_fighter as fighter
    from jojo_arena.ui.fight_view import FightView

    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    try:
        match, _ = slammed_north()
        view = FightView(load_stage("swiss_castle"), [fighter("joseph_p2"), fighter("wamuu")])
        view.update(match)
        assert view.renderer.stage.id == "st_moritz"
        again = duel("swiss_castle", "joseph_p2", "wamuu")  # what a new round builds
        view.update(again)
        assert view.renderer.stage.id == "swiss_castle"
    finally:
        pygame.display.quit()


def test_arenas_with_events_play_the_same_fight_twice():
    """The chandelier, the spikes and the way out depend on nothing but the fight."""
    from test_determinism import scripted

    frames = scripted(seed=11, steps=2400)

    def play(stage_id: str) -> tuple:
        match = duel(stage_id, "jotaro_p3", "wamuu")
        kinds = []
        for pair in frames:
            kinds += [(e.kind, e.fighter) for e in match.step(pair)]
        bodies = tuple((f.hp, f.pos.x, f.pos.y) for f in match.fighters)
        return match.arena.name, tuple(kinds), bodies

    for stage_id in ("joestar_mansion", "air_supplena", "swiss_castle"):
        assert play(stage_id) == play(stage_id), stage_id


def test_a_prop_carried_through_the_wall_stays_in_the_room_it_came_from():
    """Props are counted per arena: holding one of the hall's outside would point at
    nothing (or at the wrong thing) in the courtyard."""
    match = duel("swiss_castle", "joseph_p2", "wamuu", at=((300, 160), (300, 70)))
    joseph = match.fighters[0]
    joseph.carrying = len(match.arena.obstacles) - 1  # the last prop of the hall
    match.arena.obstacles[-1].carried_by = 0
    match.fighters[1].take_hit(0, 30, Vec2(0, -9), True)
    for _ in range(40):
        match.step((NONE, NONE))
    assert match.arena.name == "st_moritz"
    assert joseph.carrying is None
