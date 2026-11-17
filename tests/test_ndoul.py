"""N'Doul and Geb: blind, he strikes where he last heard the opponent move, so standing
still fools him; Geb is steered from afar while he sits defenseless, and a blow on him
brings it back; the water rises from the floor under them; the water shell sends shots
back."""

from helpers import NONE, hold, kinds, make_duel, press, run, run_until, walk

from jojo_arena.engine.geometry import Vec2


def test_he_is_blind_and_strikes_where_he_last_heard_them():
    match = make_duel("ndoul", "mannequin_red", p1=(80, 100), p2=(240, 100))
    dummy = match.fighters[1]
    run(match, 2)
    dummy.pos = Vec2(240, 170)  # moved without a sound: he still hears them at (240, 100)
    run(match, 70, p1=press("special"))
    assert dummy.hp == dummy.max_hp


def test_a_step_gives_them_away():
    match = make_duel("ndoul", "mannequin_red", p1=(80, 100), p2=(240, 100))
    dummy = match.fighters[1]
    run(match, 2)
    dummy.pos = Vec2(240, 170)
    match.step((NONE, walk(0.0, 1.0)))  # one step: heard
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 90, p1=press("special"))


def test_geb_is_steered_from_afar_while_he_sits():
    match = make_duel("ndoul", "mannequin_red", p1=(60, 100), p2=(320, 100))
    ndoul, dummy = match.fighters
    run_until(match, lambda m: ndoul.remote, 90, p1=hold("stand"))
    start = ndoul.pos.copy()
    run(match, 1)
    for _ in range(80):
        match.step((walk(1.0), NONE))
    assert ndoul.pos == start  # he sits still
    assert ndoul.remote_pos.x > 250  # Geb went across the arena
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 60, p1=press("light"))


def test_a_blow_on_him_brings_geb_back():
    match = make_duel("ndoul", "jotaro_p3", p1=(150, 100), p2=(175, 100))
    ndoul = match.fighters[0]
    run_until(match, lambda m: ndoul.remote, 90, p1=hold("stand"))
    run_until(match, lambda m: not ndoul.remote, 60, p2=press("light"))


def test_the_water_shell_sends_shots_back():
    move = make_duel("ndoul", "mannequin_red").fighters[0].kit.move("base", "heavy_alt")
    assert move.reflect and move.radius > 0


def test_shoot_him_seizes_them_into_its_cutscene():
    match = make_duel("ndoul", "mannequin_red", p1=(60, 100), p2=(300, 100))
    ndoul = match.fighters[0]
    gha = ndoul.kit.move("base", "gha")
    assert gha.at_target and gha.unblockable
    ndoul.hh = match.rules.hh_max
    events = run(match, 60, p1=press("heart_heat", move=(1.0, 0.0)))
    assert match.cutscene is not None and match.cutscene.name == "geb_spike"
    assert "cutscene_start" in kinds(events)
