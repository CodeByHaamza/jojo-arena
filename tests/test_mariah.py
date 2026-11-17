"""Mariah and Bastet: the outlet that makes a magnet of whoever touches it, levels of
magnetism that build with each touch and make her blows hit harder, the live wire that
draws them in, the metal that comes down on them, and the homing knives."""

from helpers import NONE, hold, kinds, make_duel, press, run, run_held, run_until, walk

from jojo_arena.combat.status import MAGNET


def test_bastet_is_laid_by_the_style_button_and_magnetizes_whoever_touches_it():
    match = make_duel("mariah", "mannequin_red", p1=(100, 100), p2=(260, 100))
    dummy = match.fighters[1]
    match.step((press("stand"), NONE))
    run_until(match, lambda m: m.traps, 60)
    run_until(match, lambda m: MAGNET in dummy.statuses, 240, p2=walk(-1))
    assert dummy.statuses.level(MAGNET) == 1


def test_each_new_touch_adds_a_level_up_to_the_third():
    match = make_duel("mariah", "mannequin_red")
    dummy = match.fighters[1]
    for level in (1, 2, 3, 3):
        dummy.statuses.apply(MAGNET, 60)
        assert dummy.statuses.level(MAGNET) == level
    run(match, 9 * 60 + 5)
    assert dummy.statuses.level(MAGNET) == 0  # it all goes when it runs out


def test_her_knives_hit_harder_for_each_level():
    def knife_damage(level: int) -> int:
        match = make_duel("mariah", "mannequin_red", p1=(100, 100), p2=(200, 100))
        dummy = match.fighters[1]
        for _ in range(level):
            dummy.statuses.apply(MAGNET, 600)
        run_until(match, lambda m: dummy.hp < dummy.max_hp, 120, p1=press("special"))
        return dummy.max_hp - dummy.hp

    assert knife_damage(0) < knife_damage(1) < knife_damage(3)


def test_the_live_wire_draws_them_in_and_shocks_them():
    match = make_duel("mariah", "mannequin_red", p1=(100, 100), p2=(230, 100))
    dummy = match.fighters[1]
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_until(match, lambda m: m.traps, 60)
    x = dummy.pos.x
    run(match, 30)
    assert dummy.pos.x < x - 5  # drawn toward the wire without moving a foot
    run_until(match, lambda m: "shock" in dummy.statuses, 240)


def test_metal_comes_down_on_them_where_they_stand():
    match = make_duel("mariah", "mannequin_red", p1=(100, 100), p2=(220, 100))
    dummy = match.fighters[1]
    move = match.fighters[0].kit.move("base", "heavy_alt")
    assert move.at_target and move.bonus_status == MAGNET
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 120)


def test_one_fine_specimen_is_a_grab_that_magnetizes():
    match = make_duel("mariah", "mannequin_red", p1=(150, 100), p2=(170, 100))
    dummy = match.fighters[1]
    match.step((press("heavy"), hold("guard")))
    run_held(match, 40, p2=hold("guard"))
    assert dummy.hp < dummy.max_hp and MAGNET in dummy.statuses


def test_she_is_a_woman_for_hol_horse():
    assert make_duel("hol_horse", "mariah").fighters[0].passive_on


def test_what_are_you_drooling_over_sprays_bolts():
    match = make_duel("mariah", "mannequin_red", p1=(100, 100), p2=(190, 100))
    mariah = match.fighters[0]
    mariah.hh = match.rules.hh_bar
    events = run(match, 120, p1=press("heart_heat"))
    assert kinds(events).count("hit") >= 5


def test_you_little_turds_comes_up_under_them_into_its_cutscene():
    match = make_duel("mariah", "mannequin_red", p1=(60, 100), p2=(340, 100))
    mariah, dummy = match.fighters
    gha = mariah.kit.move("base", "gha")
    assert gha.at_target and gha.reach == 0  # wherever they are
    mariah.hh = match.rules.hh_max
    events = run(match, 60, p1=press("heart_heat", move=(1.0, 0.0)))
    assert match.cutscene is not None and match.cutscene.name == "bastet_cars"
    assert "cutscene_start" in kinds(events)
    run(match, match.cutscene.frames_left + 2)
    assert dummy.statuses.level(MAGNET) >= 2  # the blow and the cars: a strong magnet
