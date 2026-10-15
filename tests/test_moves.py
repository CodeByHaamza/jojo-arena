"""Move mechanics beyond plain hits: line hitboxes, homing projectiles, projectile looks."""

import math

import pytest
from helpers import NONE, make_duel, press, run, run_until

from jojo_arena.characters import get_fighter
from jojo_arena.combat.kit import ProjectileDef
from jojo_arena.combat.projectile import Projectile
from jojo_arena.engine.geometry import Vec2


def stand_out(match, index=0):
    """Bring fighter `index`'s Stand out and wait until it can act again."""
    frames = [NONE, NONE]
    frames[index] = press("stand")
    match.step(tuple(frames))
    run_until(match, lambda m: m.fighters[index].can_act(), 100)
    assert match.fighters[index].stance == "stand"


@pytest.mark.parametrize("distance", [16, 30, 50, 70])
def test_star_finger_hits_all_along_the_finger(distance):
    match = make_duel("jotaro_p3", "kakyoin", p1=(100, 100), p2=(100 + distance, 100))
    stand_out(match)
    events = run(match, 40, p1=press("special", move=(1.0, 0.0)))
    assert any(e.kind == "hit" and e.fighter == 1 for e in events)


def test_star_finger_has_a_limit():
    match = make_duel("jotaro_p3", "kakyoin", p1=(100, 100), p2=(200, 100))
    stand_out(match)
    events = run(match, 40, p1=press("special", move=(1.0, 0.0)))
    assert not any(e.kind == "hit" for e in events)


def test_line_moves_cover_the_whole_reach():
    match = make_duel("jotaro_p3", "kakyoin")
    jotaro = match.fighters[0]
    stand_out(match)
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_until(match, lambda m: m.fighters[0].attack.active, 30)
    boxes = jotaro.hitboxes()
    assert len(boxes) > 5
    nearest = min((c - jotaro.pos).length() for c, _ in boxes)
    farthest = max((c - jotaro.pos).length() for c, _ in boxes)
    assert nearest < 10 and farthest == pytest.approx(jotaro.attack.move.reach)


def test_homing_projectiles_turn_toward_the_target():
    defn = ProjectileDef(4, 3, 10, 60, 10, 1, 2, homing=math.radians(6))
    shot = Projectile(0, Vec2(0, 0), Vec2(4, 0), defn, 60)
    for _ in range(20):
        shot.steer(Vec2(0, 100), defn.homing)
    assert shot.velocity.y > 3.5  # now flies mostly downward
    assert shot.velocity.length() == pytest.approx(4)


def test_projectile_looks():
    looks = {
        "dio_p3": "knife",
        "kakyoin": "gem",
        "polnareff": "blade",
    }
    for fighter_id, look in looks.items():
        kit = get_fighter(fighter_id).kit
        projectiles = [m.projectile for m in kit.all_moves() if m.projectile is not None]
        assert projectiles and all(p.look == look for p in projectiles), fighter_id


# Move mechanics on small test kits ----------------------------------------------------

from helpers import OPEN_BOUNDS, hold, kinds  # noqa: E402

from jojo_arena.combat.arena import Arena  # noqa: E402
from jojo_arena.combat.fighter import State  # noqa: E402
from jojo_arena.combat.kit import parse_kit  # noqa: E402
from jojo_arena.combat.match import Match  # noqa: E402
from jojo_arena.combat.rules import load_rules  # noqa: E402
from jojo_arena.engine.actions import InputFrame  # noqa: E402

RULES = load_rules()
JAB = {
    "startup_f": 3,
    "active_f": 2,
    "recovery_f": 10,
    "damage": 20,
    "reach": 14,
    "radius": 9,
    "hitstun_f": 20,
    "knockback": 20,
    "hitstop_f": 0,
}


def kit(moves: dict, shared: dict | None = None):
    return parse_kit(
        {"name": "Test", "stances": {"base": {"moves": moves}}, "moves": shared or {}}, "test"
    )


def duel(kit_a, kit_b=None, p1=(150, 100), p2=(170, 100)) -> Match:
    arena = Arena(OPEN_BOUNDS, (Vec2(*p1), Vec2(*p2)), [])
    return Match((kit_a, kit_b or kit_a), RULES, arena)


def test_chains_continue_on_the_same_button():
    k = kit(
        {
            "light": {**JAB, "chain": "light2", "cancel_on_hit": ["light"]},
            "light2": {**JAB, "chain": "light3", "cancel_on_hit": ["light"], "damage": 25},
            "light3": {**JAB, "damage": 40, "knockback": 300},
            "heavy": {**JAB, "damage": 60},
        }
    )
    match = duel(k)
    used = []
    for _ in range(40):
        match.step((press("light"), NONE))
        attack = match.fighters[0].attack
        if attack is not None and (not used or used[-1] != attack.move.name):
            used.append(attack.move.name)
    assert used[:3] == ["light", "light2", "light3"]


def test_chains_need_the_hit():
    k = kit({"light": {**JAB, "chain": "light2", "cancel_on_hit": ["light"]}, "light2": JAB})
    match = duel(k, p2=(260, 100))  # out of reach: the jab whiffs
    for _ in range(12):
        match.step((press("light"), NONE))
    assert match.fighters[0].attack.move.name == "light"


def test_a_counter_catches_a_blow_and_answers():
    counter_kit = kit(
        {
            "light": JAB,
            "special": {"startup_f": 2, "active_f": 30, "recovery_f": 10, "counter": "riposte"},
            "riposte": {**JAB, "damage": 90, "invincible_f": 8, "reach": 16, "radius": 12},
        }
    )
    match = duel(counter_kit, kit({"light": JAB}))
    match.step((press("special"), NONE))
    run(match, 4)
    events = run(match, 30, p2=press("light"))
    assert "counter" in kinds(events)
    hits = [e for e in events if e.kind == "hit"]
    assert hits and hits[0].fighter == 1 and hits[0].value >= 90  # the jabber is hit
    assert match.fighters[0].hp == match.fighters[0].max_hp


def test_counters_ignore_projectiles():
    counter_kit = kit(
        {"special": {"startup_f": 2, "active_f": 60, "recovery_f": 5, "counter": "r"}, "r": JAB}
    )
    shooter = kit(
        {
            "special": {
                "startup_f": 2,
                "active_f": 1,
                "recovery_f": 5,
                "projectile": {
                    "speed": 300,
                    "radius": 3,
                    "damage": 30,
                    "lifetime_s": 1,
                    "hitstun_f": 10,
                },
            }
        }
    )
    match = duel(counter_kit, shooter, p2=(220, 100))
    match.step((press("special"), NONE))
    events = run(match, 30, p2=press("special"))
    assert "counter" not in kinds(events) and "hit" in kinds(events)


def test_leap_lands_next_to_the_opponent():
    k = kit(
        {
            "special": {
                **JAB,
                "startup_f": 16,
                "leap": 140,
                "leap_height": 20,
                "invincible_f": 16,
                "reach": 0,
                "radius": 14,
            }
        }
    )
    match = duel(k, p2=(260, 100))
    events = run(match, 30, p1=press("special"))
    leaper = match.fighters[0]
    assert 200 < leaper.pos.x < 260  # traveled about 100 px, stopped beside the target
    assert "hit" in kinds(events)


def test_leaps_are_limited():
    k = kit({"special": {**JAB, "startup_f": 16, "leap": 60}})
    match = duel(k, p2=(330, 100))
    run(match, 20, p1=press("special"))
    assert match.fighters[0].pos.x == pytest.approx(210, abs=1)


def test_cursor_leap_goes_where_the_player_aims():
    k = kit(
        {
            "special": {
                "startup_f": 12,
                "active_f": 1,
                "recovery_f": 8,
                "leap": 120,
                "leap_to": "cursor",
            }
        }
    )
    match = duel(k)
    aim = InputFrame(press_counts={"special": 1}, cursor=(150.0, 30.0))
    match.step((aim, NONE))
    run(match, 20)
    assert match.fighters[0].pos.x == pytest.approx(150, abs=1)
    assert match.fighters[0].pos.y < 50  # pulled up toward the aimed point, at most 120 px


def test_cursor_leap_falls_back_on_the_stick_and_the_held_direction():
    k = kit(
        {
            "special": {
                "startup_f": 12,
                "active_f": 1,
                "recovery_f": 8,
                "leap": 80,
                "leap_to": "cursor",
            }
        }
    )
    match = duel(k)
    match.step((InputFrame(press_counts={"special": 1}, stick=(0.0, 1.0)), NONE))
    run(match, 20)
    assert match.fighters[0].pos.y == pytest.approx(180, abs=1)
    match = duel(k)
    match.step((InputFrame((-1.0, 0.0), press_counts={"special": 1}), NONE))
    run(match, 20)
    assert match.fighters[0].pos.x == pytest.approx(70, abs=1)


def test_armor_takes_the_damage_but_not_the_stagger():
    armored = kit({"heavy": {**JAB, "startup_f": 20, "armor": 1, "damage": 80}})
    match = duel(armored, kit({"light": JAB}))
    match.step((press("heavy"), NONE))
    events = run(match, 12, p2=press("light"))
    tank = match.fighters[0]
    assert "armor" in kinds(events)
    assert tank.hp < tank.max_hp and tank.state == State.ATTACK


def test_guard_crush_empties_the_guard_faster():
    def gauge_after(mult):
        crusher = kit({"heavy": {**JAB, "damage": 60, "guard_damage": mult}})
        match = duel(crusher)
        guard = hold("guard")
        match.step((NONE, guard))
        match.step((press("heavy"), guard))
        for _ in range(30):
            match.step((NONE, guard))
        return match.fighters[1].guard_gauge

    assert gauge_after(3.0) < gauge_after(1.0)


def test_long_combos_hit_softer():
    k = kit({"light": {**JAB, "cancel_on_hit": ["light"], "hitstun_f": 30}})
    match = duel(k)
    damages = []
    for _ in range(80):
        events = match.step((press("light"), NONE))
        damages += [e.value for e in events if e.kind == "hit"]
    assert len(damages) >= 5
    assert damages[0] == damages[1] == 20  # the first moves deal full damage...
    assert damages[4] < damages[2] < 20  # ...then each one a bit less
    assert min(damages) >= 20 * RULES.combo_min_scale - 1


def test_a_rush_counts_as_one_move_for_combo_scaling():
    match = make_duel("jotaro_p3", "mannequin_red")
    stand_out(match)
    rush = match.fighters[0].kit.move("stand", "heavy")
    events = run(match, 100, p1=press("heavy"))
    hits = [e.value for e in events if e.kind == "hit"]
    assert hits[:-1] == [rush.damage] * (rush.hits - 1)
