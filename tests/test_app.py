"""Smoke tests through the real entry point: every screen starts, runs and draws.

Hidden window (SDL dummy driver) and a temporary controls file: the player's own
settings are never touched.
"""

import pygame
import pytest
import screenshot_tour

from jojo_arena import app
from jojo_arena.characters import load_roster

SELECTABLE = [f.id for f in load_roster() if f.selectable]


@pytest.fixture(autouse=True)
def hidden_window(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setattr(app, "controls_path", lambda: tmp_path / "controls.json")


def run_game(tmp_path, *args: str, frames: int = 30) -> pygame.Surface:
    """Run the game for a few frames and return the last picture."""
    shot = tmp_path / "shot.png"
    app.main([*args, "--frames", str(frames), "--screenshot", str(shot)])
    return pygame.image.load(str(shot))


def colors(image: pygame.Surface) -> set:
    return {image.get_at((x, y))[:3] for x in range(0, 480, 12) for y in range(0, 270, 12)}


@pytest.mark.parametrize("scene", app.SCENES)
def test_every_screen_starts_and_draws(tmp_path, scene):
    image = run_game(tmp_path, "--scene", scene)
    assert image.get_size() == app.INTERNAL_SIZE
    assert len(colors(image)) >= 3  # something was drawn, not a blank screen


def test_the_controls_file_is_created_with_the_defaults(tmp_path):
    run_game(tmp_path, frames=1)
    assert (tmp_path / "controls.json").exists()


def test_computer_against_computer_demo(tmp_path):
    image = run_game(tmp_path, "--demo", "--p1", "dio_p3", "--p2", "polnareff", frames=600)
    assert len(colors(image)) >= 3


@pytest.mark.parametrize("fighter", SELECTABLE)
def test_every_fighter_in_training(tmp_path, fighter):
    rival = SELECTABLE[(SELECTABLE.index(fighter) + 1) % len(SELECTABLE)]
    run_game(tmp_path, "--scene", "training", "--p1", fighter, "--p2", rival, frames=60)


def test_screenshot_tour_visits_every_screen(tmp_path):
    saved = screenshot_tour.run_tour(tmp_path / "tour", scale=1)
    names = [path.stem.split("_", 1)[1] for path in saved]
    for expected in (
        "title",
        "main_menu",
        "select_training",
        "move_list_page1",
        "training_combo",
        "training_pause",
        "vs_screen",
        "fight_pause",
        "knockout",
        "options",
    ):
        assert expected in names
    assert all(path.exists() for path in saved)
