"""Lisa Lisa: the Snake Muffler (a parry that catches blows and sends projectiles back),
the scarf that reels in, the acrobatic leap, and the scarf trap."""

from helpers import NONE, kinds, make_duel, press, run, run_held, run_until

GHA = press("heart_heat", move=(1.0, 0.0))


def test_lisa_lisa_sends_a_projectile_back():
    match = make_duel("lisa_lisa", "speedwagon", p1=(100, 100), p2=(220, 100))
    lisa, speedwagon = match.fighters
    match.step((NONE, press("special")))
    run_until(match, lambda m: m.projectiles, 30)
    run_until(match, lambda m: (m.projectiles[0].pos - lisa.pos).length() < 60, 60)
    match.step((press("special"), NONE))
    events = run_until(match, lambda m: speedwagon.hp < speedwagon.max_hp, 90)
    assert "reflect" in kinds(events)
    assert lisa.hp == lisa.max_hp


def test_the_snake_muffler_catches_a_blow():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(150, 100), p2=(172, 100))
    lisa, dummy = match.fighters
    match.step((press("special"), NONE))
    run_held(match, 4)
    events = run(match, 30, p2=press("light"))
    assert "counter" in kinds(events)
    assert lisa.hp == lisa.max_hp and dummy.hp < dummy.max_hp


def test_the_binding_scarf_reels_the_opponent_in():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(100, 100), p2=(150, 100))
    dummy = match.fighters[1]
    match.step((press("heavy"), NONE))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 30)
    run_held(match, 20)
    assert dummy.pos.x < 140


def test_lisa_lisa_flips_through_the_air_untouchable_and_lands_a_heel():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(100, 100), p2=(230, 100))
    lisa, dummy = match.fighters
    lisa.hamon = 100
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_held(match, 6)
    assert lisa.invincible and lisa.pos.x > 110  # in the air, on her way
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 30)
    assert lisa.pos.x > 200


def test_the_scarf_trap_plays_its_cutscene():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(100, 100), p2=(150, 100))
    match.fighters[0].hh = match.rules.hh_max
    events = run(match, 80, p1=GHA)
    assert match.cutscene is not None and match.cutscene.name == "scarf_trap"
    assert "cutscene_start" in kinds(events)
