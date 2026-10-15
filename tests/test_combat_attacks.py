import pytest
from helpers import NONE, crate, kinds, make_match, press, run, run_held, walk

from jojo_arena.combat.fighter import State

LIGHT = 35
HEAVY = 90
SPECIAL = 55


def test_walking_moves_at_walk_speed():
    match = make_match(p1=(100, 100), p2=(300, 100))
    run_held(match, 60, p1=walk(1, 0))
    assert match.fighters[0].pos.x == pytest.approx(196)  # 96 px/s for one second
    assert match.fighters[0].state == State.WALK
    assert match.fighters[0].facing.x == 1


def test_light_attack_hits_in_range():
    match = make_match()
    events = run(match, 30, p1=press("light"))
    defender = match.fighters[1]
    assert defender.hp == defender.max_hp - LIGHT
    assert "hit" in kinds(events)


def test_attack_aims_at_the_opponent_whatever_the_facing():
    match = make_match(p1=(150, 100), p2=(150, 125))  # opponent below
    match.fighters[0].facing.x = -1  # looking away
    run(match, 30, p1=press("light"))
    assert match.fighters[1].hp == match.fighters[1].max_hp - LIGHT


def test_attack_out_of_range_misses():
    match = make_match(p1=(100, 100), p2=(200, 100))
    events = run(match, 40, p1=press("light"))
    assert match.fighters[1].hp == match.fighters[1].max_hp
    assert "hit" not in kinds(events)


def test_hit_causes_hitstun_and_hitstop():
    match = make_match()
    run(match, 6, p1=press("light"))  # startup 5 -> hit on the 6th step
    defender = match.fighters[1]
    assert defender.state == State.HITSTUN
    assert match.hitstop > 0
    before = defender.pos.copy()
    run(match, 2)
    assert defender.pos == before  # frozen during hitstop


def test_hitstun_wears_off():
    match = make_match()
    run(match, 60, p1=press("light"))
    assert match.fighters[1].state == State.IDLE


def test_attack_pressed_during_recovery_is_buffered():
    match = make_match(p1=(100, 100), p2=(300, 100))
    attacker = match.fighters[0]
    run(match, 12, p1=press("light"))  # in recovery (light ends at 18)
    run(match, 1, p1=press("light"))
    run(match, 6)
    assert attacker.state == State.ATTACK and attacker.attack.serial == 2


def test_light_cancels_into_heavy_on_hit():
    match = make_match()
    run(match, 6, p1=press("light"))
    assert match.fighters[0].attack.connected
    run(match, 1, p1=press("heavy"))  # pressed during the hitstop freeze...
    assert match.fighters[0].attack.move.name == "light"
    run(match, match.hitstop + 1)  # ...and it comes out as soon as the freeze ends
    assert match.fighters[0].attack.move.name == "heavy"
    run(match, 40)
    assert match.fighters[1].hp == match.fighters[1].max_hp - LIGHT - HEAVY


def test_heavy_sends_into_the_wall_and_bounces():
    match = make_match(p1=(340, 100), p2=(370, 100))  # right wall at x = 400
    events = run(match, 60, p1=press("heavy"))
    defender = match.fighters[1]
    assert "wall_bounce" in kinds(events)
    assert defender.hp < defender.max_hp - HEAVY  # bounce adds damage
    assert defender.pos.x < 400 - 8


def test_light_does_not_wall_bounce():
    match = make_match(p1=(360, 100), p2=(385, 100))
    events = run(match, 60, p1=press("light"))
    assert "wall_bounce" not in kinds(events)


def test_projectile_travels_and_hits():
    match = make_match(p1=(60, 100), p2=(260, 100))
    events = run(match, 90, p1=press("special"))
    assert match.fighters[1].hp == match.fighters[1].max_hp - SPECIAL
    assert "hit" in kinds(events)
    assert match.projectiles == []


def test_projectile_breaks_a_crate_and_stops():
    box = crate(150, 95, hp=40)
    match = make_match(p1=(60, 100), p2=(300, 100), obstacles=[box])
    events = run(match, 120, p1=press("special"))
    assert box.broken
    assert "prop_break" in kinds(events)
    assert match.fighters[1].hp == match.fighters[1].max_hp


def test_projectiles_cancel_each_other():
    match = make_match(p1=(60, 100), p2=(340, 100))
    events = run(match, 120, p1=press("special"), p2=press("special"))
    assert "projectile_clash" in kinds(events)
    assert all(f.hp == f.max_hp for f in match.fighters)


def test_melee_damages_props():
    box = crate(170, 95, hp=40)
    match = make_match(p1=(150, 100), p2=(320, 100), obstacles=[box])
    run(match, 30, p1=press("heavy"))
    assert box.broken


def test_bodies_do_not_overlap():
    match = make_match(p1=(100, 100), p2=(140, 100))
    run_held(match, 60, p1=walk(1, 0))
    a, b = match.fighters
    assert a.pos.distance_to(b.pos) >= 2 * match.rules.body_radius - 0.01


def test_ko_when_life_runs_out():
    match = make_match()
    match.fighters[1].hp = 10
    events = run(match, 30, p1=press("light"))
    assert match.fighters[1].state == State.KO
    assert "ko" in kinds(events)
    run(match, 30, p2=press("light"))
    assert match.fighters[1].state == State.KO  # a KO'd fighter does nothing


def test_same_inputs_same_fight():
    script = [press("light"), walk(1, 0), NONE, press("heavy"), press("special")] * 20

    def play():
        match = make_match(p1=(120, 100), p2=(200, 100))
        for frame in script:
            match.step((frame, walk(-1, 0.5)))
        return [(f.pos.x, f.pos.y, f.hp, f.state) for f in match.fighters]

    assert play() == play()
