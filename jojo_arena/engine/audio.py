"""Sound effects played through pygame's mixer; silent when there is no audio device.

Sounds are given as mono 16-bit samples (array("h")) at RATE, and converted to the
mixer's own format. One module-level player (set_player) lets any part of the program
play a sound by name without knowing who set the audio up.
"""

from __future__ import annotations

from array import array

import pygame

RATE = 22050


class AudioPlayer:
    def __init__(self) -> None:
        self.ok = pygame.mixer.get_init() is not None
        if not self.ok:
            try:
                pygame.mixer.init(RATE, -16, 1, 512)
                self.ok = True
            except pygame.error:
                self.ok = False  # no audio device: everything stays silent
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.volume = 1.0

    def add(self, name: str, samples: array) -> None:
        if not self.ok:
            return
        freq, _, channels = pygame.mixer.get_init()
        data = _resample(samples, RATE, freq)
        if channels > 1:
            data = array("h", (s for s in data for _ in range(channels)))
        self.sounds[name] = pygame.mixer.Sound(buffer=data.tobytes())

    def play(self, name: str, volume: float = 1.0) -> None:
        sound = self.sounds.get(name)
        if sound is None or self.volume <= 0:
            return
        sound.set_volume(max(0.0, min(1.0, volume * self.volume)))
        sound.play()


def _resample(samples: array, rate: int, target: int) -> array:
    """Nearest-sample resampling: enough for short effects."""
    if rate == target:
        return samples
    count = len(samples) * target // rate
    return array("h", (samples[i * rate // target] for i in range(count)))


_player: AudioPlayer | None = None


def set_player(player: AudioPlayer | None) -> None:
    global _player
    _player = player


def play(name: str, volume: float = 1.0) -> None:
    """Play a sound by name, if audio is set up (tests and tools run without it)."""
    if _player is not None:
        _player.play(name, volume)
