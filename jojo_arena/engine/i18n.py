"""The language texts are shown in: one current language for the whole game.

Data files give a text in the original language under its plain key (`label`) and its
translations under suffixed keys (`label_en`). `localized` picks the one to show.
"""

from __future__ import annotations

import locale
from collections.abc import Mapping

LANGUAGES = ("fr", "en")
DEFAULT = "fr"

_current = DEFAULT


def language() -> str:
    return _current


def set_language(code: str) -> None:
    global _current
    if code not in LANGUAGES:
        raise ValueError(f"unknown language '{code}' (one of {', '.join(LANGUAGES)})")
    _current = code


def localized(data: Mapping, key: str, default: str = "") -> str:
    """data["<key>_<language>"] when the data has it, otherwise data["<key>"]."""
    return data.get(f"{key}_{_current}", data.get(key, default))


def system_language() -> str:
    """The language of the computer when the game knows it, otherwise the default."""
    try:
        name = locale.getlocale()[0] or ""
    except ValueError:
        name = ""
    code = name[:2].lower()
    if code in LANGUAGES:
        return code
    # Windows may name the locale in full ("French_France").
    for known, word in (("fr", "french"), ("en", "english")):
        if name.lower().startswith(word):
            return known
    return DEFAULT
