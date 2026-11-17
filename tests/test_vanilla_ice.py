"""Vanilla Ice and Cream: the void steered by hand, unseen and untouchable, erasing what is
in its way; Cream rising from the floor under the opponent; the blood drained by "Lord
DIO!"; a vampire, whom the sun and the Ripple burn."""

from helpers import NONE, hold, kinds, make_duel, press, run, run_held, run_until

from jojo_arena.combat.arena import Obstacle
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Rect


def _stand(match) -> None:
    ice = match.fighters[0]
    match.step((press("stand"), NONE))
    run_until(match, lambda m: ice.stance == "stand" and ice.can_act(), 60)


def test_vanilla_ice_is_a_vampire():
    match = make_duel("vanilla_ice", "mannequin_red")
    assert match.fighters[0].kit.nature == "vampire"


def test_the_void_is_steered_by_hand():
    match = make_duel("vanilla_ice", "mannequin_red", p1=(100, 100), p2=(360, 40))
    ice = match.fighters[0]
    _stand(match)
    start = ice.pos.copy()
    match.step((press("special", move=(1.0, 0.0)), NONE))
    for _ in range(8):
        match.step((InputFrame((1.0, 0.0)), NONE))
    went_right = ice.pos - start
    assert went_right.x > 20 and abs(went_right.y) < 4
    turn = ice.pos.copy()
    for _ in range(10):
        match.step((InputFrame((0.0, 1.0)), NONE))  # it turns where it is steered
    assert ice.pos.y - turn.y > 15


def test_in_the_void_he_is_unseen_and_untouchable():
    match = make_duel("vanilla_ice", "mannequin_red", p1=(100, 100), p2=(300, 100))
    ice = match.fighters[0]
    _stand(match)
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_held(match, 4)
    move = ice.attack.move
    assert move.vanish and move.unblockable
    assert ice.vanished and ice.invincible
    hp = ice.hp

    run_until(match, lambda m: not ice.vanished, 120)
    assert ice.hp == hp


def test_the_void_goes_through_a_guard():
    match = make_duel("vanilla_ice", "mannequin_red", p1=(100, 100), p2=(170, 100))
    dummy = match.fighters[1]
    _stand(match)
    match.step((press("special", move=(1.0, 0.0)), hold("guard")))
    run_held(match, 40, p1=InputFrame((1.0, 0.0)), p2=hold("guard"))
    assert dummy.hp < dummy.max_hp


def test_the_void_erases_what_is_in_its_way():
    match = make_duel("vanilla_ice", "mannequin_red", p1=(60, 100), p2=(360, 30))
    ice = match.fighters[0]
    crate = Obstacle("crate", Rect(110, 92, 12, 14), 500)
    match.arena.obstacles.append(crate)
    _stand(match)
    match.step((press("special", move=(1.0, 0.0)), NONE))
    events = run_held(match, 30, p1=InputFrame((1.0, 0.0)))
    assert crate.broken and "prop_break" in kinds(events)
    assert ice.pos.x > 125  # straight through, not stopped by it


def test_he_peeks_out_after_the_void_and_can_be_hit_then():
    match = make_duel("vanilla_ice", "mannequin_red", p1=(100, 100), p2=(360, 40))
    ice = match.fighters[0]
    _stand(match)
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_until(match, lambda m: ice.attack is not None and ice.attack.phase == 2, 120)
    assert not ice.vanished and not ice.invincible  # out to look: open


def test_cream_comes_up_from_the_floor_under_the_opponent_through_a_guard():
    match = make_duel("vanilla_ice", "mannequin_red", p1=(80, 100), p2=(220, 100))
    dummy = match.fighters[1]
    match.step((press("special", move=(1.0, 0.0)), hold("guard")))
    run_held(match, 60, p2=hold("guard"))
    assert dummy.hp < dummy.max_hp


def test_lord_dio_drains_blood_to_heal_him():
    match = make_duel("vanilla_ice", "mannequin_red", p1=(150, 100), p2=(172, 100))
    ice, dummy = match.fighters
    ice.hp = ice.max_hp - 100
    run(match, 40, p1=press("heavy"))
    assert dummy.hp < dummy.max_hp and ice.hp > ice.max_hp - 100


def test_the_sun_burns_him():
    match = make_duel("vanilla_ice", "mannequin_red")
    ice = match.fighters[0]
    match.arena.sun_windows = [Rect(0, 0, 400, 200)]
    match.arena.sun_after_f = 0
    run(match, 30)
    assert ice.hp < ice.max_hp


def test_miasma_of_the_void_crosses_the_arena_into_its_cutscene():
    match = make_duel("vanilla_ice", "mannequin_red", p1=(60, 100), p2=(300, 100))
    ice = match.fighters[0]
    gha = ice.kit.move("base", "gha")
    assert gha.unblockable and gha.reach >= 200
    ice.hh = match.rules.hh_max
    events = run(match, 60, p1=press("heart_heat", move=(1.0, 0.0)))
    assert match.cutscene is not None and match.cutscene.name == "void_miasma"
    assert "cutscene_start" in kinds(events)
    events = run(match, match.cutscene.frames_left + 2)
    assert "cutscene_end" in kinds(events)


def test_the_great_void_rises_reaches_out_unblockable():
    match = make_duel("vanilla_ice", "mannequin_red", p1=(100, 100), p2=(150, 100))
    ice, dummy = match.fighters
    hha = ice.kit.move("base", "hha")
    assert hha.unblockable and hha.shape == "line"
    ice.hh = match.rules.hh_bar
    match.step((press("heart_heat"), hold("guard")))
    run_held(match, 50, p2=hold("guard"))
    assert dummy.max_hp - dummy.hp >= 150
