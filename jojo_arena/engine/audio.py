"""Sound effects played through pygame's mixer; silent when there is no audio device.

Sounds are given as mono 16-bit samples (array("h")) at RATE, and converted to the
mixer's own format, or read from sound files in a folder (a sound pack). One module-level
player (set_player) lets any part of the program play a sound by name without knowing who
set the audio up.
"""

from __future__ import annotations

from array import array
from pathlib import Path

import pygame

RATE = 22050
SOUND_FILES = (".ogg", ".wav")  # what a folder of sounds may hold


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

    def load_folder(self, folder: Path, prefix: str = "") -> list[str]:
        """Read every sound file under `folder`, subfolders included. Each one is known by
        its path without the extension, with `prefix` in front ("voices/someone/shout");
        a sound already known by that name is replaced. Returns the names read, sorted; a
        file that cannot be read is left out, and a folder that is not there is no sound."""
        if not self.ok or not folder.is_dir():
            return []
        loaded = []
        for path in sorted(folder.rglob("*")):
            if path.suffix.lower() not in SOUND_FILES or not path.is_file():
                continue
            name = prefix + path.relative_to(folder).with_suffix("").as_posix()
            try:
                self.sounds[name] = pygame.mixer.Sound(str(path))
            except pygame.error:
                continue
            loaded.append(name)
        return loaded

    def has(self, name: str) -> bool:
        return name in self.sounds

    def play(self, name: str, volume: float = 1.0) -> bool:
        """Play the sound of that name. False when there is none (or the sound is off)."""
        sound = self.sounds.get(name)
        if sound is None or self.volume <= 0:
            return False
        sound.set_volume(max(0.0, min(1.0, volume * self.volume)))
        sound.play()
        return True


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


def play(name: str, volume: float = 1.0) -> bool:
    """Play a sound by name, if audio is set up (tests and tools run without it). False
    when nothing was played."""
    return _player is not None and _player.play(name, volume)


def has(name: str) -> bool:
    return _player is not None and _player.has(name)


def load_folder(folder: Path, prefix: str = "") -> list[str]:
    """Read a folder of sound files into the player that is set up (see AudioPlayer)."""
    return _player.load_folder(folder, prefix) if _player is not None else []
