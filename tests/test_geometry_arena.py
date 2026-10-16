import pytest

from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.engine.geometry import (
    Rect,
    RoundedRect,
    Vec2,
    circle_overlaps_rect,
    push_circle_out_of_rect,
)
from jojo_arena.stages import load_stage

BOUNDS = RoundedRect(Rect(0, 0, 200, 100), 20)


def test_vector_reflect_on_wall():
    v = Vec2(3, -2).reflect(Vec2(1, 0))
    assert (v.x, v.y) == (-3, -2)


def test_push_out_from_outside_and_inside():
    rect = Rect(10, 10, 20, 20)
    pos, normal = push_circle_out_of_rect(Vec2(33, 20), 5, rect)
    assert pos.x == pytest.approx(35) and normal == Vec2(1, 0)
    pos, normal = push_circle_out_of_rect(Vec2(12, 20), 5, rect)  # center inside, near left
    assert pos.x == pytest.approx(5) and normal == Vec2(-1, 0)
    assert push_circle_out_of_rect(Vec2(50, 50), 5, rect) is None


def test_rounded_rect_leaves_inside_points_alone():
    pos, normal = BOUNDS.constrain_circle(Vec2(100, 50), 8)
    assert pos == Vec2(100, 50) and normal is None


def test_rounded_rect_flat_wall_gives_inward_normal():
    pos, normal = BOUNDS.constrain_circle(Vec2(-5, 50), 8)
    assert pos == Vec2(8, 50)
    assert normal == Vec2(1, 0)


def test_rounded_rect_corner_follows_the_arc():
    pos, normal = BOUNDS.constrain_circle(Vec2(0, 0), 8)
    arc_center = Vec2(20, 20)  # inner rect corner (8, 8) + corner radius (20 - 8)
    assert pos.distance_to(arc_center) == pytest.approx(12)
    assert normal.x > 0 and normal.y > 0  # pushes back toward the middle


def test_obstacle_breaks_once_and_stops_blocking():
    crate = Obstacle("crate", Rect(50, 40, 10, 10), max_hp=40)
    assert not crate.damage(30)
    assert crate.damage(30)
    assert crate.broken and not crate.solid
    assert not crate.damage(30)  # already broken: no second "break" event


def test_unbreakable_obstacle_ignores_damage():
    pillar = Obstacle("pillar", Rect(50, 40, 10, 10), max_hp=0)
    assert not pillar.damage(999)
    assert pillar.solid


def test_arena_constrain_reports_obstacle_hit():
    crate = Obstacle("crate", Rect(50, 40, 10, 10), max_hp=40)
    arena = Arena(BOUNDS, (Vec2(20, 50), Vec2(180, 50)), [crate])
    pos, normal, hit = arena.constrain(Vec2(47, 45), 5)
    assert hit is crate
    assert not circle_overlaps_rect(pos, 5, crate.rect)
    crate.damage(100)
    pos, normal, hit = arena.constrain(Vec2(47, 45), 5)
    assert hit is None and pos == Vec2(47, 45)


def test_cairo_stage_is_playable():
    stage = load_stage("cairo_night")
    arena = stage.build_arena()
    assert len(arena.obstacles) == 11  # 4 stalls, 3 crates, 4 jars
    for spawn in arena.spawns:
        assert not arena.outside_walls(spawn, 8)
        assert arena.obstacle_at(spawn, 8) is None
    # Each round gets fresh, unbroken props.
    arena.obstacles[0].damage(999)
    assert not stage.build_arena().obstacles[0].broken
