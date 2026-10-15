from jojo_arena.engine.display import best_window_scale, compute_viewport
from jojo_arena.engine.loop import FixedStep

INTERNAL = (480, 270)


def test_viewport_exact_fit_1080p():
    scale, rect = compute_viewport((1920, 1080), INTERNAL)
    assert scale == 4
    assert tuple(rect) == (0, 0, 1920, 1080)


def test_viewport_letterboxes_when_window_does_not_fit():
    scale, rect = compute_viewport((1600, 900), INTERNAL)
    assert scale == 3
    assert rect.size == (1440, 810)
    assert rect.topleft == (80, 45)


def test_viewport_never_below_scale_one():
    scale, rect = compute_viewport((300, 200), INTERNAL)
    assert scale == 1
    assert rect.size == INTERNAL


def test_window_scale_leaves_room_for_taskbar():
    assert best_window_scale((1920, 1080), INTERNAL, (0, 120)) == 3
    assert best_window_scale((2560, 1440), INTERNAL, (0, 120)) == 4


def test_fixed_step_runs_sixty_steps_per_second():
    clock = FixedStep(hz=60)
    total = sum(clock.advance(16) for _ in range(1000))
    # 1000 frames of 16 ms = 16 s -> exactly 60 steps per second, no float drift.
    assert total == 60 * 16


def test_fixed_step_keeps_remainder_between_frames():
    clock = FixedStep(hz=60)
    assert clock.advance(10) == 0
    assert clock.advance(7) == 1  # 17 ms >= 16.67 ms


def test_fixed_step_drops_backlog_after_long_freeze():
    clock = FixedStep(hz=60, max_steps_per_frame=5)
    assert clock.advance(2000) == 5
    assert clock.advance(0) == 0
