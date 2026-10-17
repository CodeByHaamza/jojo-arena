"""The game's sound effects, synthesized in code (no sound files): impacts, whooshes,
the guard, clashes, stopped time, Hamon, ice, chains... and the menus.

Every sound is a short list of samples built from noise, tones and sweeps under an
envelope. The fight view plays them from the simulation's events.
"""

from __future__ import annotations

import math
import random
from array import array
from collections.abc import Callable

from jojo_arena.combat.events import Event
from jojo_arena.engine import audio
from jojo_arena.engine.audio import RATE, AudioPlayer

PEAK = 30000


def _render(duration: float, voice: Callable, seed: int = 1) -> array:
    """Samples of `voice(t, progress, rng)` over `duration` seconds, clipped to 16 bits."""
    rng = random.Random(seed)
    count = int(duration * RATE)
    out = array("h")
    for i in range(count):
        t = i / RATE
        value = voice(t, i / count, rng)
        out.append(max(-32767, min(32767, int(value * PEAK))))
    return out


def _decay(progress: float, power: float = 3.0) -> float:
    return (1 - progress) ** power


def _sweep(t: float, f0: float, f1: float, duration: float) -> float:
    """Phase of a tone gliding from f0 to f1 over `duration`."""
    k = (f1 - f0) / duration
    return 2 * math.pi * (f0 * t + 0.5 * k * t * t)


def _hit(heavy: bool) -> array:
    duration = 0.22 if heavy else 0.1
    base = 70 if heavy else 130

    def voice(t, p, rng):
        thump = math.sin(_sweep(t, base * 1.6, base * 0.6, duration)) * _decay(p, 2.5)
        crack = rng.uniform(-1, 1) * _decay(min(1.0, p * (3 if heavy else 4)), 2)
        return 0.7 * thump + 0.45 * crack

    return _render(duration, voice, seed=3 if heavy else 2)


def _whoosh() -> array:
    state = {"low": 0.0}

    def voice(t, p, rng):
        state["low"] += (rng.uniform(-1, 1) - state["low"]) * 0.25  # soft, airy noise
        return state["low"] * math.sin(math.pi * p) * 0.8

    return _render(0.16, voice, seed=5)


def _ping(freqs: tuple[float, ...], duration: float, power: float = 2.5) -> array:
    def voice(t, p, _rng):
        tone = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        return tone * _decay(p, power) * 0.7

    return _render(duration, voice)


def _blip(f0: float, f1: float, duration: float) -> array:
    def voice(t, p, _rng):
        square = 1.0 if math.sin(_sweep(t, f0, f1, duration)) >= 0 else -1.0
        return square * 0.25 * _decay(p, 1.5)

    return _render(duration, voice)


def _guard_break() -> array:
    def voice(t, p, rng):
        glass = math.sin(_sweep(t, 1600, 300, 0.32)) * _decay(p, 2)
        return 0.5 * glass + 0.35 * rng.uniform(-1, 1) * _decay(p, 4)

    return _render(0.32, voice, seed=7)


def _clash() -> array:
    def voice(t, p, rng):
        ring = sum(math.sin(2 * math.pi * f * t) for f in (620, 950, 1340)) / 3
        return 0.6 * ring * _decay(p, 2) + 0.35 * rng.uniform(-1, 1) * _decay(p, 6)

    return _render(0.45, voice, seed=9)


def _time_stop() -> array:
    """A rising rush of noise, then a deep boom with a ringing tone."""

    def voice(t, p, rng):
        if p < 0.55:
            q = p / 0.55
            return rng.uniform(-1, 1) * q * q * 0.7
        q = (p - 0.55) / 0.45
        boom = math.sin(2 * math.pi * 55 * t) * _decay(q, 2)
        bell = math.sin(2 * math.pi * 880 * t) * _decay(q, 3) * 0.4
        return 0.8 * boom + bell

    return _render(0.9, voice, seed=11)


def _time_resume() -> array:
    def voice(t, p, _rng):
        return math.sin(_sweep(t, 900, 120, 0.45)) * _decay(p, 1.5) * 0.6

    return _render(0.45, voice)


def _ko() -> array:
    def voice(t, p, rng):
        boom = math.sin(_sweep(t, 90, 35, 0.8)) * _decay(p, 1.8)
        return 0.8 * boom + 0.4 * rng.uniform(-1, 1) * _decay(p, 5)

    return _render(0.8, voice, seed=13)


def _super() -> array:
    def voice(t, p, _rng):
        chord = sum(math.sin(_sweep(t, f, f * 2, 0.45)) for f in (220, 277, 330)) / 3
        return chord * math.sin(math.pi * p) * 0.7

    return _render(0.45, voice)


def _crackle() -> array:
    """Hamon: a buzzing hum with sharp electric clicks."""

    def voice(t, p, rng):
        buzz = math.sin(2 * math.pi * 1900 * t) * 0.25
        click = rng.choice((0.0, 0.0, 0.0, 0.0, rng.uniform(-1, 1)))
        return (buzz + 0.7 * click) * _decay(p, 1.5)

    return _render(0.22, voice, seed=17)


def _freeze() -> array:
    def voice(t, p, _rng):
        shimmer = math.sin(2 * math.pi * 2100 * t) + math.sin(2 * math.pi * 2650 * t)
        tremolo = 0.5 + 0.5 * math.sin(2 * math.pi * 24 * t)
        return shimmer * 0.3 * tremolo * _decay(p, 1.5)

    return _render(0.32, voice)


def _sizzle() -> array:
    state = {"high": 0.0, "last": 0.0}

    def voice(t, p, rng):
        noise = rng.uniform(-1, 1)
        state["high"] = noise - state["last"]  # thin, hissing noise
        state["last"] = noise
        return state["high"] * 0.25 * math.sin(math.pi * p)

    return _render(0.28, voice, seed=19)


def _chain() -> array:
    clinks = (0.0, 0.07, 0.13)

    def voice(t, p, _rng):
        value = 0.0
        for start in clinks:
            if t >= start:
                q = min(1.0, (t - start) / 0.06)
                value += math.sin(2 * math.pi * 1500 * t) * (1 - q) ** 3
        return 0.4 * value

    return _render(0.22, voice)


def _beam() -> array:
    def voice(t, p, _rng):
        phase = _sweep(t, 900, 1600, 0.28) / (2 * math.pi)
        saw = 2 * (phase - math.floor(phase + 0.5))
        return saw * 0.3 * _decay(p, 1.2)

    return _render(0.28, voice)


def _boom() -> array:
    """An explosion: a deep falling thump under a long rumble of noise."""
    state = {"low": 0.0}

    def voice(t, p, rng):
        state["low"] += (rng.uniform(-1, 1) - state["low"]) * 0.08
        thump = math.sin(_sweep(t, 90, 30, 0.5)) * _decay(min(1.0, p * 2), 2)
        return 0.6 * thump + 1.6 * state["low"] * _decay(p, 1.6)

    return _render(0.5, voice, seed=11)


def _pop() -> array:
    def voice(t, p, rng):
        return math.sin(_sweep(t, 1400, 500, 0.06)) * _decay(p, 2) * 0.5

    return _render(0.06, voice)


def _wind() -> array:
    """A tornado: a band of noise rising, with the air beating round it."""
    state = {"low": 0.0, "band": 0.0}

    def voice(t, p, rng):
        noise = rng.uniform(-1, 1)
        state["low"] += (noise - state["low"]) * 0.12
        state["band"] += (state["low"] - state["band"]) * (0.05 + 0.25 * p)
        beat = 0.75 + 0.25 * math.sin(2 * math.pi * 11 * t)
        return 1.5 * state["band"] * beat * math.sin(math.pi * p) ** 0.6

    return _render(0.45, voice, seed=23)


def _splat() -> array:
    """Boiling blood pumped out: a wet burst, thick and low."""
    state = {"low": 0.0}

    def voice(t, p, rng):
        state["low"] += (rng.uniform(-1, 1) - state["low"]) * 0.2
        gulp = math.sin(_sweep(t, 420, 120, 0.3)) * _decay(p, 2.2)
        return 0.45 * gulp + 0.9 * state["low"] * _decay(p, 3.0)

    return _render(0.3, voice, seed=29)


def _blade() -> array:
    """Steel coming out: a short bright ring sliding up."""

    def voice(t, p, _rng):
        return math.sin(_sweep(t, 2200, 3200, 0.12)) * _decay(p, 2.6) * 0.35

    return _render(0.12, voice)


def _gunshot() -> array:
    """A submachine gun: a crack, then the shots rattling on."""

    def voice(t, p, rng):
        crack = rng.uniform(-1, 1) * _decay(min(1.0, p * 6), 2.0)
        rattle = rng.uniform(-1, 1) if (t * 16) % 1 < 0.35 else 0.0
        return 0.8 * crack + 0.35 * rattle * _decay(p, 1.4)

    return _render(0.35, voice, seed=31)


def build_sounds(player: AudioPlayer) -> None:
    """Make every sound once, at start-up."""
    library = {
        "hit": _hit(False),
        "hit_heavy": _hit(True),
        "whoosh": _whoosh(),
        "block": _ping((780, 1180), 0.08, 4),
        "guard_break": _guard_break(),
        "clash": _clash(),
        "time_stop": _time_stop(),
        "time_resume": _time_resume(),
        "ko": _ko(),
        "super": _super(),
        "hamon": _crackle(),
        "freeze": _freeze(),
        "sizzle": _sizzle(),
        "chain": _chain(),
        "beam": _beam(),
        "boom": _boom(),
        "pop": _pop(),
        "wind": _wind(),
        "splat": _splat(),
        "blade": _blade(),
        "gunshot": _gunshot(),
        "stylish": _ping((1320, 1760), 0.25, 2),
        "menu_move": _blip(660, 660, 0.035),
        "menu_ok": _blip(660, 990, 0.08),
        "menu_back": _blip(440, 300, 0.08),
        "menu_locked": _blip(200, 180, 0.1),
    }
    for name, samples in library.items():
        player.add(name, samples)


# What a move with an effect of its own sounds like, played the frame it goes active.
FX_SOUNDS: dict[str, str] = {
    "vortex": "wind",
    "wind_beam": "wind",
    "gun": "gunshot",
    "blood_jet": "splat",
    "tentacle": "splat",
    "cables": "chain",
    "blade": "blade",
    "blade_fan": "blade",
    "blade_hair": "blade",
    "beam": "beam",
    "lenses": "beam",
    "bubbles": "pop",
    "scarf": "whoosh",
    "scarf_spear": "whoosh",
    "hair": "whoosh",
    "limb": "whoosh",
    "chain": "chain",
}


# Which sound each event of the fight makes (a name, or a function of the event).
EVENT_SOUNDS: dict[str, Callable[[Event], str]] = {
    "hit": lambda e: "hit_heavy" if (e.value or 0) >= 80 else "hit",
    "block": lambda e: "block",
    "guard_break": lambda e: "guard_break",
    "clash_start": lambda e: "clash",
    "clash_win": lambda e: "hit_heavy",
    "time_stop": lambda e: "time_stop",
    "time_resume": lambda e: "time_resume",
    "ko": lambda e: "ko",
    "hha": lambda e: "super",
    "gha": lambda e: "super",
    "hamon": lambda e: "hamon",
    "freeze": lambda e: "freeze",
    "sunburn": lambda e: "sizzle",
    "cage": lambda e: "chain",
    "cage_end": lambda e: "chain",
    "stylish": lambda e: "stylish",
    "throw": lambda e: "whoosh",
    "prop_swing": lambda e: "whoosh",
    "pickup": lambda e: "chain",
    "prop_break": lambda e: "hit",
    "explosion": lambda e: "boom",
    "burst": lambda e: "pop",
    "reflect": lambda e: "hamon",
    "foreseen": lambda e: "stylish",
}


def play_events(events: list[Event]) -> None:
    """The sounds of a step of the fight (each sound at most once per step)."""
    played: set[str] = set()
    for event in events:
        chooser = EVENT_SOUNDS.get(event.kind)
        if chooser is None:
            continue
        name = chooser(event)
        if name not in played:
            played.add(name)
            audio.play(name)
