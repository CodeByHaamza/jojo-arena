"""Background music: small chiptune loops rendered from a description (no music files),
and a player that keeps one of them looping on its own mixer channel.

A track is a key, a scale, a chord progression (one chord per bar) and a short lead
motif; the renderer adds a bass line, arpeggios and drums. Tracks render in a
background thread at start-up; one asked for before it is ready starts when it is.
"""

from __future__ import annotations

import math
import random
import threading
from array import array
from dataclasses import dataclass, field

import pygame

from jojo_arena.engine.audio import RATE

PEAK = 22000


@dataclass(frozen=True)
class Track:
    tempo: int  # beats per minute
    root: int  # MIDI note of the key
    scale: tuple[int, ...]  # semitones above the root
    progression: tuple[int, ...]  # one chord per bar: a scale degree
    motif: tuple[tuple[int, int, int], ...] = ()  # (16th step in bar, degree, 16ths long)
    lead_wave: str = "square"  # "square" or "organ"
    drums: bool = True
    repeats: int = 2  # the progression played this many times per loop


def note_hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def degree_note(track: Track, degree: int, octave: int = 0) -> int:
    """The MIDI note of a scale degree (degrees past the scale climb octaves)."""
    count = len(track.scale)
    return track.root + 12 * (octave + degree // count) + track.scale[degree % count]


def render(track: Track, seed: int = 1) -> array:
    """The whole loop, mono 16-bit samples at RATE."""
    rng = random.Random(seed)
    step_len = int(RATE * 60 / track.tempo / 4)  # a 16th note
    bars = len(track.progression) * track.repeats
    total = step_len * 16 * bars
    mix = [0.0] * total

    def add_tone(start: int, length: int, hz: float, volume: float, wave: str) -> None:
        period = RATE / hz
        attack = min(200, length // 4)
        for i in range(min(length, total - start)):
            phase = (i % period) / period
            if wave == "square":
                value = 1.0 if phase < 0.5 else -1.0
            elif wave == "pulse":
                value = 1.0 if phase < 0.25 else -1.0
            elif wave == "triangle":
                value = 4 * abs(phase - 0.5) - 1
            else:  # organ: a square and its octave, softened
                value = (1.0 if phase < 0.5 else -1.0) * 0.6 + math.sin(4 * math.pi * phase) * 0.4
            envelope = min(1.0, i / max(1, attack)) * (1 - i / length) ** 0.5
            mix[start + i] += value * volume * envelope

    def add_drum(start: int, kind: str) -> None:
        length = int(RATE * (0.14 if kind == "kick" else 0.09 if kind == "snare" else 0.03))
        for i in range(min(length, total - start)):
            p = i / length
            if kind == "kick":
                hz = 120 - 80 * p
                value = math.sin(2 * math.pi * hz * i / RATE) * (1 - p) ** 2 * 0.9
            elif kind == "snare":
                value = rng.uniform(-1, 1) * (1 - p) ** 2 * 0.45
            else:
                value = rng.uniform(-1, 1) * (1 - p) ** 3 * 0.18
            mix[start + i] += value

    for bar in range(bars):
        chord = track.progression[bar % len(track.progression)]
        bar_start = bar * 16 * step_len
        # Bass: eighth notes on the chord root, jumping an octave on the off-beats.
        for step in range(0, 16, 2):
            octave = -2 if step % 4 == 0 else -1
            hz = note_hz(degree_note(track, chord, octave))
            add_tone(bar_start + step * step_len, step_len * 2, hz, 0.22, "triangle")
        # Arpeggio: the chord's notes in 16ths.
        tones = (0, 2, 4, 7)
        for step in range(16):
            degree = chord + tones[step % len(tones)]
            hz = note_hz(degree_note(track, degree, 0))
            add_tone(bar_start + step * step_len, step_len, hz, 0.07, "pulse")
        # Lead: the motif, carried onto each chord.
        for step, degree, length in track.motif:
            hz = note_hz(degree_note(track, chord + degree, 1))
            add_tone(bar_start + step * step_len, length * step_len, hz, 0.11, track.lead_wave)
        if track.drums:
            for step in range(16):
                start = bar_start + step * step_len
                if step in (0, 8) or (step == 10 and bar % 2):
                    add_drum(start, "kick")
                if step in (4, 12):
                    add_drum(start, "snare")
                if step % 2 == 0:
                    add_drum(start, "hat")
    peak = max(1e-6, max(abs(v) for v in mix))
    scale = PEAK / max(peak, 1.0)
    return array("h", (int(v * scale) for v in mix))


@dataclass
class MusicPlayer:
    """Keeps one track looping; renders tracks in the background."""

    tracks: dict[str, Track]
    volume: float = 0.5
    _sounds: dict[str, pygame.mixer.Sound] = field(default_factory=dict)
    _wanted: str | None = None
    _playing: str | None = None
    _channel: pygame.mixer.Channel | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        if pygame.mixer.get_init() is None:
            return  # no audio: silent
        pygame.mixer.set_reserved(1)
        self._channel = pygame.mixer.Channel(0)
        threading.Thread(target=self._render_all, daemon=True).start()

    def _render_all(self) -> None:
        for name, track in self.tracks.items():
            samples = render(track)
            mixer = pygame.mixer.get_init()
            if mixer is None:
                return  # the audio was shut down meanwhile (quitting, tests)
            freq, _, channels = mixer
            if freq != RATE:
                count = len(samples) * freq // RATE
                samples = array("h", (samples[i * RATE // freq] for i in range(count)))
            if channels > 1:
                samples = array("h", (s for s in samples for _ in range(channels)))
            try:
                sound = pygame.mixer.Sound(buffer=samples.tobytes())
            except pygame.error:
                return
            with self._lock:
                self._sounds[name] = sound

    def request(self, name: str | None) -> None:
        """Ask for a track (None: silence); it starts as soon as it is rendered."""
        self._wanted = name

    def tick(self) -> None:
        """Once per frame: switch to the wanted track when it is ready."""
        if self._channel is None or self._wanted == self._playing:
            if self._channel is not None:
                self._channel.set_volume(self.volume)
            return
        if self._wanted is None:
            self._channel.fadeout(400)
            self._playing = None
            return
        with self._lock:
            sound = self._sounds.get(self._wanted)
        if sound is None:
            return  # still rendering
        self._channel.set_volume(self.volume)
        self._channel.play(sound, loops=-1, fade_ms=600)
        self._playing = self._wanted


_player: MusicPlayer | None = None


def set_player(player: MusicPlayer | None) -> None:
    global _player
    _player = player


def request(name: str | None) -> None:
    if _player is not None:
        _player.request(name)


def tick() -> None:
    if _player is not None:
        _player.tick()


def set_volume(volume: float) -> None:
    if _player is not None:
        _player.volume = volume
