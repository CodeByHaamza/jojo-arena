"""Hamon (GDD "Hamon en détail"): breathing, boosted moves, Hamon against vampires, and
the Part 1 fighters' signature moves."""

import pygame
from helpers import NONE, hold, make_duel, press, run_held, run_until

from jojo_arena.characters import load_roster
from jojo_arena.combat.fighter import State
from jojo_arena.engine.geometry import Vec2
from jojo_arena.ui.cutscenes import CUTSCENES


def hp_lost(fighter) -> int:
    return fighter.max_hp - fighter.hp


def test_breathing_fills_the_gauge_and_holds_the_fighter_still():
    match = make_duel("jonathan", "mannequin_red")
    jonathan = match.fighters[0]
    rules = match.rules
    assert jonathan.hamon == rules.hamon_start
    jonathan.hamon = 0
    start = jonathan.pos.copy()
    match.step((press("stand", hold=("stand",)), NONE))
    assert jonathan.state == State.BREATHE
    breathing = hold("stand", move=(1.0, 0.0))  # walking while breathing: no
    run_held(match, 60, p1=breathing)
    assert abs(jonathan.hamon - rules.hamon_breath_per_f * 60) < 1
    assert jonathan.pos == start
    run_held(match, 2)
    assert jonathan.state == State.IDLE  # released: free again


def test_a_boosted_move_spends_the_hamon_and_hits_harder():
    def scarlet_overdrive(hamon: float) -> tuple[int, float]:
        match = make_duel("jonathan", "mannequin_red", p2=(172, 100))
        jonathan, dummy = match.fighters
        jonathan.hamon = hamon
        match.step((press("special"), NONE))
        run_until(match, lambda m: dummy.hp < dummy.max_hp, 80)
        return hp_lost(dummy), jonathan.hamon

    move_cost = 30
    plain, left_plain = scarlet_overdrive(10)  # not enough: a plain blow, nothing spent
    boosted, left_boosted = scarlet_overdrive(100)
    assert left_plain == 10 and left_boosted == 100 - move_cost
    assert boosted > plain * 1.3


def test_hamon_burns_a_vampire_twice_as_hard():
    def overdrive_on(victim_id: str) -> int:
        match = make_duel("jonathan", victim_id, p2=(172, 100))
        jonathan, victim = match.fighters
        jonathan.hamon = 100
        match.step((press("special"), NONE))
        run_until(match, lambda m: victim.hp < victim.max_hp, 80)
        return hp_lost(victim)

    human, vampire = overdrive_on("jotaro_p3"), overdrive_on("dio_p3")
    assert abs(vampire - 2 * human) <= 2


def test_the_passing_ripple_goes_through_the_guard_only_with_hamon():
    def ripple(hamon: float) -> int:
        match = make_duel("jonathan", "mannequin_red", p2=(172, 100))
        jonathan, dummy = match.fighters
        jonathan.hamon = hamon
        guard = hold("guard")
        match.step((press("special", move=(1.0, 0.0)), guard))
        for _ in range(60):
            match.step((NONE, guard))
        return hp_lost(dummy)

    blocked, through = ripple(0), ripple(100)
    assert through > 3 * max(1, blocked)


def test_zeppeli_cutters_carry_the_hamon():
    match = make_duel("zeppeli", "dio_p3", p2=(230, 100))
    zeppeli, dio = match.fighters
    zeppeli.hamon = 100
    match.step((press("special"), NONE))
    run_until(match, lambda m: m.projectiles, 40)
    assert all(p.hamon and p.boost > 1 for p in match.projectiles)
    events = run_until(match, lambda m: dio.hp < dio.max_hp, 80)
    events += match.step((NONE, NONE))
    assert any(e.kind == "hamon" and e.value == 1 for e in events)  # it burns DIO


def test_jonathan_barrage_clashes_with_star_platinum():
    match = make_duel("jonathan", "jotaro_p3", p1=(150, 100), p2=(186, 100))
    jotaro = match.fighters[1]
    match.step((NONE, press("stand")))
    run_until(match, lambda m: jotaro.can_act(), 60)
    match.step((press("heavy"), press("heavy")))
    run_until(match, lambda m: m.clash is not None, 40)
    assert all(f.state == State.CLASH for f in match.fighters)


def test_the_part_1_ultimates_have_their_cutscenes():
    for fighter in load_roster():
        for move in fighter.kit.all_moves():
            if move.cinematic:
                assert move.cinematic in CUTSCENES, (fighter.id, move.cinematic)


def test_the_part_1_cutscenes_play_to_the_end(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    from jojo_arena.combat.match import Match
    from jojo_arena.combat.rules import load_rules
    from jojo_arena.stages import load_stage
    from jojo_arena.ui.fight_view import FightView

    stage = load_stage("cairo_night")
    for user_id in ("jonathan", "zeppeli"):
        defs = [f for f in load_roster() if f.id in (user_id, "dio_p3")]
        defs.sort(key=lambda f: f.id != user_id)
        match = Match((defs[0].kit, defs[1].kit), load_rules(), stage.build_arena())
        user, dio = match.fighters
        dio.pos = user.pos + Vec2(26, 0)
        user.hh = match.rules.hh_max
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
        assert started, user_id
        assert dio.hp < dio.max_hp - 200  # the finish landed, Hamon on a vampire
    pygame.display.quit()
