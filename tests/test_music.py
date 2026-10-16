"""Music: every loop renders to the right length, every arena has its track, the player
loops the wanted track once it is ready, and stays silent without audio."""

import time

import pygame

from jojo_arena.engine.audio import RATE
from jojo_arena.engine.music import MusicPlayer, Track, degree_note, render
from jojo_arena.settings import Settings
from jojo_arena.stages import STAGE_IDS
from jojo_arena.ui.music import TRACKS, track_for_stage


def test_every_track_renders_a_whole_loop():
    for name, track in TRACKS.items():
        samples = render(track)
        step = int(RATE * 60 / track.tempo / 4)
        bars = len(track.progression) * track.repeats
        assert len(samples) == step * 16 * bars, name
        assert max(abs(s) for s in samples) > 10000, name  # music, not silence


def test_scale_degrees_climb_octaves():
    track = Track(tempo=120, root=60, scale=(0, 2, 4, 5, 7, 9, 11), progression=(0,))
    assert degree_note(track, 0) == 60
    assert degree_note(track, 7) == 72
    assert degree_note(track, 2, octave=-1) == 52


def test_every_arena_has_its_music():
    for stage_id in STAGE_IDS:
        assert track_for_stage(stage_id) in TRACKS
    assert track_for_stage("an arena still to come") == "menu"


def test_the_player_is_silent_without_audio(monkeypatch):
    pygame.mixer.quit()
    player = MusicPlayer({"menu": TRACKS["menu"]})
    player.request("menu")
    player.tick()  # nothing to play on: no error


def test_the_player_loops_the_wanted_track_once_rendered(monkeypatch):
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.quit()
    try:
        pygame.mixer.init(RATE, -16, 1, 512)
    except pygame.error:
        return  # no audio at all on this machine
    short = Track(tempo=240, root=57, scale=(0, 2, 3, 5, 7, 8, 10), progression=(0,), repeats=1)
    player = MusicPlayer({"short": short})
    player.request("short")
    deadline = time.time() + 10
    while player._playing != "short" and time.time() < deadline:
        player.tick()
        time.sleep(0.02)
    assert player._playing == "short"
    player.request(None)
    player.tick()
    assert player._playing is None
    pygame.mixer.quit()


def test_the_music_volume_has_its_own_setting():
    assert Settings().music_volume == 5
