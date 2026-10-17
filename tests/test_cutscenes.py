"""Ultimates with a cutscene: the opening blow must land; then the fight holds while the
cutscene plays, and the finishing blow lands at the end."""

from helpers import NONE, hold, kinds, make_duel, press, run, run_until

from jojo_arena.characters import get_fighter
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.rounds import Phase, Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2

GHA = press("heart_heat", move=(1.0, 0.0))
RULES = load_rules()


def test_road_roller_needs_the_opening_blow_to_land():
    match = make_duel("dio_p3", "jotaro_p3", p1=(100, 100), p2=(124, 100))
    match.fighters[0].hh = 200
    events = run(match, 60, p1=GHA)  # super flash, then the opening blow
    assert "cutscene_start" in kinds(events)
    assert match.cutscene is not None and match.cutscene.name == "road_roller"


def test_the_fight_holds_during_the_cutscene_then_the_finish_lands():
    match = make_duel("dio_p3", "jotaro_p3", p1=(100, 100), p2=(124, 100))
    dio, jotaro = match.fighters
    dio.hh = 200
    run_until(match, lambda m: m.cutscene is not None, 60, p1=GHA)
    hp, pos = jotaro.hp, jotaro.pos.copy()
    for _ in range(match.cutscene.frames_left - 1):
        match.step((NONE, press("light", move=(-1.0, 0.0))))  # nothing moves
    assert jotaro.hp == hp and jotaro.pos == pos
    events = match.step((NONE, NONE))
    assert "cutscene_end" in kinds(events)
    assert jotaro.hp < hp - 150  # the road roller
    run(match, 30)
    assert jotaro.pos.x > pos.x + 20  # sent flying


def test_an_ultimate_that_misses_does_nothing_more():
    # Out of range: the road roller falls as far out as it can, and lands on nothing.
    match = make_duel("dio_p3", "jotaro_p3", p1=(100, 100), p2=(340, 100))
    match.fighters[0].hh = 200
    events = run(match, 80, p1=GHA)
    assert "cutscene_start" not in kinds(events)
    assert match.fighters[1].hp == match.fighters[1].max_hp
    assert match.fighters[0].hh == 0  # the two bars are spent all the same


def test_a_blocked_ultimate_plays_no_cutscene():
    match = make_duel("jotaro_p3", "dio_p3", p1=(100, 100), p2=(124, 100))
    match.fighters[0].hh = 200
    guard = hold("guard")
    match.step((NONE, guard))
    events = []
    for i in range(40):
        events += match.step((GHA if i == 0 else NONE, guard))
    assert "block" in kinds(events) and "cutscene_start" not in kinds(events)


def test_every_great_heat_attack_has_a_cutscene():
    for fighter_id, name in (
        ("jotaro_p3", "star_finish"),
        ("dio_p3", "road_roller"),
        ("polnareff", "chariot_clones"),
        ("kakyoin", "hierophant_web"),
    ):
        assert get_fighter(fighter_id).kit.shared_moves["gha"].cinematic == name


def test_hierophant_web_covers_the_arena_and_fires_when_touched():
    match = make_duel("kakyoin", "jotaro_p3", p1=(100, 100), p2=(300, 100))
    match.fighters[0].hh = 200
    events = run(match, 10, p1=GHA)
    assert "cutscene_start" in kinds(events)  # no hit needed: it starts at once
    run_until(match, lambda m: m.cutscene is None, 400)
    assert len(match.webs) == 1
    web = match.webs[0]
    assert len(web.nodes) >= 12 and len(web.edges) >= 15
    # Jotaro walks into a thread: emeralds fly at him.
    jotaro = match.fighters[1]
    events = []
    for _ in range(200):
        events += match.step((NONE, press(move=(0.0, 1.0))))
        if "trap_triggered" in kinds(events):
            break
    assert "trap_triggered" in kinds(events)
    assert any(p.owner == 0 for p in match.projectiles) or jotaro.hp < jotaro.max_hp


def test_the_round_clock_waits_for_the_cutscene():
    kits = (get_fighter("dio_p3").kit, get_fighter("jotaro_p3").kit)

    def arena():
        from helpers import OPEN_BOUNDS

        return Arena(OPEN_BOUNDS, (Vec2(100, 100), Vec2(124, 100)))

    rounds = Rounds(kits, RULES, arena, 1)
    for _ in range(RULES.round_intro_f + 1):
        rounds.step((NONE, NONE))
    assert rounds.phase == Phase.FIGHT
    rounds.match.fighters[0].hh = 200
    rounds.step((GHA, NONE))
    while rounds.match.cutscene is None:
        rounds.step((NONE, NONE))
    clock = rounds.timer_f
    for _ in range(60):
        rounds.step((NONE, NONE))
    assert rounds.timer_f == clock
