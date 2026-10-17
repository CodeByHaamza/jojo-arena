"""Straizo: the sniper stance and its jets from the eyes, the eye barrage, and the Hamon
that burns him."""

from helpers import NONE, kinds, make_duel, press, run, run_held, run_until

from jojo_arena.characters import get_fighter

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


def test_the_ripple_is_not_his_to_hold():
    """He drank from the stone mask: the Ripple burns him. No Hamon tool, no Hamon move -
    and the scarf of Satiporoja beetle silk is Lisa Lisa's, not his."""
    kit = get_fighter("straizo").kit
    for move in kit.all_moves():
        assert not move.hamon, move.name
        assert move.hamon_cost == 0, move.name
        assert "SATIPOROJA" not in (move.label or "").upper(), move.name
    assert get_fighter("straizo").kit.nature == "vampire"  # and the sun and Hamon say so


def test_he_puts_himself_back_together_and_pays_for_it():
    regeneration = get_fighter("straizo").kit.move("base", "special_alt")
    assert regeneration.buff == "regeneration"
    buff = get_fighter("straizo").kit.buffs["regeneration"]
    assert buff.heal_per_s > 0  # the flesh comes back...
    assert buff.damage_taken_mult > 1  # ...and he is weak while it does
