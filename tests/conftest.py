"""What every test starts from.

A few things in the game are global on purpose (the language, the sound and music
players). A test that starts the whole game sets them and leaves them behind, and the
tests run in a different order on every worker: each test starts from the same place.
"""

import pytest

from jojo_arena.engine import audio, i18n, music


@pytest.fixture(autouse=True)
def clean_globals():
    """In French (the default one follows the machine: an English Windows runner says
    "CPU" where the game says "IA"), with no sound or music player left by a game that
    has already quit its mixer."""
    i18n.set_language("fr")
    audio.set_player(None)
    music.set_player(None)
    yield
    i18n.set_language("fr")
    audio.set_player(None)
    music.set_player(None)
