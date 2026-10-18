"""The notes of a Release come out of CHANGELOG.md."""

from release_notes import HEADER, notes_for

CHANGELOG = """# Journal

## Non publié

### Ajouté

- Santana refait.

## 0.1.0

- Premier combat.
"""


def test_a_tagged_version_gets_its_own_section():
    notes = notes_for("v0.1.0", CHANGELOG)
    assert notes.startswith(HEADER) and "Premier combat" in notes and "Santana" not in notes


def test_a_version_not_written_yet_gets_the_unreleased_section():
    notes = notes_for("v0.2.0", CHANGELOG)
    assert "Santana refait" in notes and "Premier combat" not in notes


def test_with_nothing_to_say_it_is_still_a_valid_release():
    assert notes_for("v9.9.9", "# Journal\n") == HEADER
