"""Straizo: the sniper stance and its jets from the eyes, the eye barrage, and the Hamon
that burns him."""

from helpers import NONE, kinds, make_duel, press, run, run_held, run_until

GHA = press("heart_heat", move=(1.0, 0.0))


def test_straizo_takes_aim_and_snipes_across_the_arena():
    match = make_duel("straizo", "mannequin_red", p1=(60, 100), p2=(250, 100))
    straizo, dummy = match.fighters
    straizo.blood = 100
    match.step((press("stand"), NONE))
    run_until(match, lambda m: straizo.stance == "sniper", 30)
    match.step((press("light"), NONE))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 40)


def test_the_eye_barrage_plays_its_cutscene():
    match = make_duel("straizo", "mannequin_red", p1=(100, 100), p2=(250, 100))
    match.fighters[0].hh = match.rules.hh_max
    events = run(match, 80, p1=GHA)
    assert match.cutscene is not None and match.cutscene.name == "eye_barrage"
    assert "cutscene_start" in kinds(events)


def test_lisa_lisas_hamon_riposte_burns_straizo():
    match = make_duel("lisa_lisa", "straizo", p1=(150, 100), p2=(172, 100))
    lisa, straizo = match.fighters
    match.step((press("special"), NONE))
    run_held(match, 4)
    run(match, 40, p2=press("light"))
    riposte = lisa.kit.move("base", "muffler_strike")
    burned = round(riposte.damage * match.rules.hamon_vs_weak_mult)
    assert straizo.max_hp - straizo.hp == burned
