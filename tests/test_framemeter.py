"""The frame meter: the bands it draws, and the advantage it measures."""

from helpers import NONE, hold, make_duel, make_match, press

from jojo_arena.combat.framedata import frame_data
from jojo_arena.combat.framemeter import WIDTH, Advantage, Band, FrameMeter
from jojo_arena.combat.rules import load_rules

RULES = load_rules()


def run(meter: FrameMeter, match, frames: int, p1=NONE, guard: bool = False) -> None:
    """Step the match and feed the meter; p1 presses once, the dummy guards throughout."""
    for i in range(frames):
        p2 = hold("guard") if guard else NONE
        events = match.step((p1 if i == 0 else NONE, p2))
        meter.update(match, events)


def runs(bands: list[Band]) -> list[tuple[Band, int]]:
    """The bands in a row, grouped: [(FREE, 4), (STARTUP, 4), (ACTIVE, 3)...]."""
    grouped: list[tuple[Band, int]] = []
    for band in bands:
        if grouped and grouped[-1][0] == band:
            grouped[-1] = (band, grouped[-1][1] + 1)
        else:
            grouped.append((band, 1))
    return grouped


def test_a_move_shows_its_startup_active_and_recovery_frames():
    match = make_match(p1=(150, 100), p2=(320, 100))  # far apart: nothing connects
    meter = FrameMeter()
    move = match.fighters[0].kit.move("base", "light")
    run(meter, match, move.total_f + 4, p1=press("light"))
    phases = [(band, n) for band, n in runs(meter.row(0)) if band != Band.FREE]
    assert phases == [
        (Band.STARTUP, move.startup_f),
        (Band.ACTIVE, move.active_f),
        (Band.RECOVERY, move.recovery_f),
    ]


def test_the_dummy_shows_hitstun_while_the_other_shows_its_move():
    match = make_match()
    meter = FrameMeter()
    run(meter, match, 40, p1=press("light"))
    assert Band.HITSTUN in meter.row(1)
    assert Band.ACTIVE in meter.row(0)
    assert Band.HITSTUN not in meter.row(0)


def test_holding_guard_is_a_band_of_its_own_and_blocking_is_another():
    match = make_match()
    meter = FrameMeter()
    run(meter, match, 40, p1=press("light"), guard=True)
    assert Band.GUARD in meter.row(1) and Band.BLOCKSTUN in meter.row(1)


def test_an_impact_freezes_both_rows_alike():
    match = make_match()
    meter = FrameMeter()
    run(meter, match, 40, p1=press("heavy"))  # a heavy blow: hitstop
    columns = meter.bands
    assert any(a == Band.FROZEN and b == Band.FROZEN for a, b in columns)


def test_the_strip_never_grows_past_its_width():
    match = make_match()
    meter = FrameMeter(width=30)
    run(meter, match, 100)
    assert len(meter.bands) == 30
    assert WIDTH > 60  # the real one holds a second or more


# The measured advantage -----------------------------------------------------------------


def measure(slot: str, guard: bool) -> tuple[int, int | None]:
    """(measured, announced) advantage for one of Jotaro's bare-handed moves."""
    match = make_duel("jotaro_p3", "jotaro_p3", p1=(150, 100), p2=(172, 100))
    meter = FrameMeter()
    move = match.fighters[0].kit.move("base", slot)
    run(meter, match, 200, p1=press(slot), guard=guard)
    assert meter.advantage is not None, f"{slot}: nothing was measured"
    data = frame_data(move, RULES)
    return meter.advantage.frames, data.on_block if guard else data.on_hit


def test_a_blow_that_lands_measures_the_advantage_its_data_announces():
    # What matters is that the two agree: the meter measures what the data computes.
    # (The numbers themselves move when a move's frames are tuned.)
    for slot, expected in (("heavy", 11), ("light", 7)):
        measured, announced = measure(slot, guard=False)
        assert measured == announced == expected, slot


def test_a_blocked_blow_measures_the_advantage_its_data_announces():
    for slot, expected in (("heavy", -3), ("light", -1)):
        measured, announced = measure(slot, guard=True)
        assert measured == announced == expected, slot


def test_the_measured_advantage_says_who_it_belongs_to():
    match = make_duel("jotaro_p3", "jotaro_p3", p1=(150, 100), p2=(172, 100))
    meter = FrameMeter()
    run(meter, match, 120, p1=press("heavy"), guard=True)
    assert meter.advantage is not None
    assert meter.advantage.attacker == 0 and meter.advantage.blocked


def test_nothing_is_measured_while_no_blow_has_landed():
    match = make_match(p1=(150, 100), p2=(320, 100))
    meter = FrameMeter()
    run(meter, match, 60, p1=press("light"))
    assert meter.advantage is None


def test_a_measured_advantage_leaves_the_screen_after_a_while():
    advantage = Advantage(frames=4, shown_f=2)
    assert advantage.visible
    advantage.shown_f = 0
    assert not advantage.visible


def test_resetting_clears_the_strip_and_the_advantage():
    match = make_match()
    meter = FrameMeter()
    run(meter, match, 40, p1=press("light"))
    meter.reset()
    assert not meter.bands and meter.advantage is None
