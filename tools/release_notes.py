"""The notes of a GitHub Release, taken from CHANGELOG.md.

    python tools/release_notes.py v0.2.0 release-notes.md

The section of that version (`## 0.2.0`) is used; if the version has no section yet,
the `## Non publié` one is (the usual case: the tag is pushed before the changelog is
renamed). The fan game notice always comes first.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
UNRELEASED = "Non publié"
HEADER = (
    "Fan game non officiel, gratuit et sans but lucratif. "
    "Télécharge JoJoArena.exe et lance-le (Windows).\n"
)


def sections(text: str) -> dict[str, str]:
    """Every `## ` section of the changelog, by title, without its title line."""
    found: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = found.setdefault(line[3:].strip(), [])
        elif current is not None:
            current.append(line)
    return {title: "\n".join(lines).strip() for title, lines in found.items()}


def notes_for(version: str, text: str) -> str:
    version = version.removeprefix("v")
    parts = sections(text)
    body = parts.get(version) or parts.get(UNRELEASED, "")
    return f"{HEADER}\n{body}\n" if body else HEADER


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    version, out = argv
    Path(out).write_text(notes_for(version, CHANGELOG.read_text(encoding="utf-8")), "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
