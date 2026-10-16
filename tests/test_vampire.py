"""Vampires (GDD "Vampire / Pillar Man"): the blood gauge, healing, Vaporization Freezing,
Space Ripper Stingy Eyes, sunlight, and Dio Brando's Absorption."""

import pygame
from helpers import NONE, OPEN_BOUNDS, hold, make_duel, press, run_held, run_until

from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.fighter import State
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Rect, Vec2


def test_draining_fills_the_blood_gauge():
    match = make_duel("dio_p1", "mannequin_red", p2=(172, 100))
    dio, dummy = match.fighters
    dio.blood = 0
    fingers = dio.kit.move("base", "heavy")
    match.step((press("heavy"), NONE))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 60)
    drained = round((dummy.max_hp - dummy.hp) * fingers.drain)
    assert dio.blood == drained * match.rules.blood_per_drain


def test_untouched_a_vampire_heals_on_his_blood():
    match = make_duel("dio_p1", "mannequin_red", p2=(300, 100))
    dio = match.fighters[0]
    rules = match.rules
    dio.hurt(400)
    dio.blood = 60
    run_held(match, rules.vampire_regen_delay_f)
    assert dio.hp == dio.max_hp - 400  # still waiting
    run_held(match, 120)
    healed = dio.hp - (dio.max_hp - 400)
    assert healed > 20
    assert abs((60 - dio.blood) - healed * rules.regen_blood_per_hp) < 1


def test_hamon_stops_a_vampire_from_healing():
    match = make_duel("jonathan", "dio_p1", p2=(172, 100))
    jonathan, dio = match.fighters
    jonathan.hamon = 100
    match.step((press("special"), NONE))
    run_until(match, lambda m: dio.hp < dio.max_hp, 80)
    assert dio.regen_wait >= match.rules.hamon_regen_block_f - 2


def test_the_freezing_stance_needs_blood_and_ends_when_it_runs_dry():
    match = make_duel("dio_p1", "mannequin_red", p2=(300, 100))
    dio = match.fighters[0]
    dio.blood = 0
    match.step((press("stand"), NONE))
    run_held(match, 20)
    assert dio.stance == "base"  # no blood, no freezing
    dio.blood = 12
    match.step((press("stand"), NONE))
    run_until(match, lambda m: dio.stance == "freeze", 30)
    run_until(match, lambda m: dio.stance == "base", 60 * 4)  # dry: back to normal
    assert dio.blood == 0


def test_a_freezing_touch_freezes_the_opponent_solid():
    match = make_duel("dio_p1", "mannequin_red", p2=(172, 100))
    dio, dummy = match.fighters
    dio.stance = "freeze"
    dio.blood = 100
    touch = dio.kit.move("freeze", "light")
    match.step((press("light"), NONE))
    events = run_until(match, lambda m: dummy.iced_f > 0, 30)
    events += match.step((NONE, NONE))
    assert any(e.kind == "freeze" for e in events)
    assert dummy.state == State.HITSTUN and dummy.stun_f >= touch.freeze_f - 3


def test_the_eye_beams_need_blood_and_reach_far():
    match = make_duel("dio_p1", "mannequin_red", p1=(100, 100), p2=(250, 100))
    dio, dummy = match.fighters
    dio.blood = 10
    match.step((press("special"), NONE))
    assert dio.state != State.ATTACK  # not enough blood
    dio.blood = 30
    run_held(match, 2)
    match.step((press("special"), NONE))
    assert dio.state == State.ATTACK and dio.blood == 10
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 40)  # 150 px away


def sunny_duel(p1_id: str, p2_id: str) -> Match:
    arena = Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(330, 100)), [])
    arena.sun_windows = [Rect(120, 70, 60, 60)]
    kits = (get_fighter(p1_id).kit, get_fighter(p2_id).kit)
    return Match(kits, load_rules(), arena)


def test_the_sun_boils_a_vampires_blood_then_burns_him():
    match = sunny_duel("dio_p1", "mannequin_red")
    dio = match.fighters[0]
    rules = match.rules
    dio.blood = 10
    events = run_held(match, 60)
    assert dio.in_sun and dio.blood == 0
    assert dio.hp < dio.max_hp
    assert any(e.kind == "sunburn" for e in events)
    shade = sunny_duel("mannequin_red", "dio_p1")  # Dio out of the light
    run_held(shade, 60)
    assert shade.fighters[1].hp == shade.fighters[1].max_hp
    assert rules.sun_damage_per_f > 0


def test_hamon_breathing_fills_faster_in_the_sun():
    def breathe(sunny: bool) -> float:
        match = sunny_duel("jonathan", "mannequin_red")
        if not sunny:
            match.arena.sun_windows = []
        jonathan = match.fighters[0]
        jonathan.hamon = 0
        match.step((press("stand", hold=("stand",)), NONE))
        run_held(match, 60, p1=hold("stand"))
        return jonathan.hamon

    assert breathe(True) > breathe(False) * 1.3


def test_absorption_drains_a_big_share_of_life(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    from jojo_arena.stages import load_stage
    from jojo_arena.ui.fight_view import FightView

    stage = load_stage("cairo_night")
    defs = [f for f in load_roster() if f.id in ("dio_p1", "jotaro_p3")]
    defs.sort(key=lambda f: f.id != "dio_p1")
    match = Match((defs[0].kit, defs[1].kit), load_rules(), stage.build_arena())
    dio, jotaro = match.fighters
    jotaro.pos = dio.pos + Vec2(24, 0)
    dio.hp = 500
    dio.hh = match.rules.hh_max
    view = FightView(stage, defs)
    surface = pygame.Surface((480, 270))
    started = False
    for i in range(400):
        frame = press("heart_heat", move=(1.0, 0.0)) if i == 0 else NONE
        events = match.step((frame, NONE))
        view.on_events(events, match)
        view.update(match)
        view.draw(surface, match)
        started = started or match.cutscene is not None
        if started and match.cutscene is None:
            break
    assert started
    finish = dio.kit.shared_moves["gha"]
    assert jotaro.hp < jotaro.max_hp - finish.finish_damage * 0.9
    assert dio.hp > 500 + finish.finish_damage * finish.finish_drain * 0.8
    pygame.display.quit()
