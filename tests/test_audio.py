"""Sound: every effect is synthesized, the fight's events make sounds, the volume is kept."""

from array import array

import pygame
import pytest

from jojo_arena.combat.events import Event
from jojo_arena.engine import audio
from jojo_arena.engine.audio import RATE, AudioPlayer
from jojo_arena.settings import Settings, load_settings, save_settings, settings_path
from jojo_arena.ui import sounds


class Recorder:
    """Stands in for the audio player: keeps what was added and played."""

    def __init__(self) -> None:
        self.added: dict[str, array] = {}
        self.played: list[str] = []

    def add(self, name: str, samples: array) -> None:
        self.added[name] = samples

    def play(self, name: str, volume: float = 1.0) -> None:
        self.played.append(name)


@pytest.fixture
def recorder():
    player = Recorder()
    sounds.build_sounds(player)
    audio.set_player(player)
    yield player
    audio.set_player(None)


def test_every_sound_is_short_loud_enough_and_in_range(recorder):
    assert len(recorder.added) >= 15
    for name, samples in recorder.added.items():
        assert samples.typecode == "h" and 0 < len(samples) <= RATE, name
        assert max(abs(s) for s in samples) > 2000, name  # not silent


def test_every_event_sound_exists(recorder):
    for kind, choose in sounds.EVENT_SOUNDS.items():
        assert choose(Event(kind, None, 0, 100)) in recorder.added, kind


def test_every_move_effect_has_a_sound_that_exists(recorder):
    for fx, name in sounds.FX_SOUNDS.items():
        assert name in recorder.added, fx


def test_every_effect_a_kit_uses_has_a_voice(recorder):
    """A move drawn with an effect of its own should be heard, not only seen."""
    from jojo_arena.characters import load_roster

    silent = set()
    for entry in load_roster():
        for move in entry.kit.all_moves():
            if move.fx and move.fx not in sounds.FX_SOUNDS:
                silent.add(move.fx)
    assert silent == set(), f"these effects make no sound: {sorted(silent)}"


def test_events_make_their_sounds_once_per_step(recorder):
    events = [Event("hit", None, 1, 30), Event("hit", None, 1, 30), Event("hit", None, 0, 120)]
    sounds.play_events(events + [Event("walk", None, 0)])
    assert recorder.played == ["hit", "hit_heavy"]


def test_the_player_plays_or_stays_silent(monkeypatch):
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.quit()
    player = AudioPlayer()
    player.add("tone", array("h", [0, 12000, 0, -12000] * 200))
    player.play("tone")
    player.play("no such sound")  # nothing happens
    if player.ok:
        assert "tone" in player.sounds
    pygame.mixer.quit()


def test_the_volume_is_saved(tmp_path):
    path = settings_path(tmp_path / "controls.json")
    save_settings(Settings(language="fr", volume=3), path)
    assert load_settings(path).volume == 3
    assert Settings().volume == 7
