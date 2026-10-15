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
