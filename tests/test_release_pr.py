"""Preparing a release: the version written in both places, the changelog closed, and
the check the CI runs on a pull request into main."""

import pytest
from release_pr import (
    check_release,
    close_unreleased,
    highest_tag,
    parse_version,
    set_version_init,
    set_version_pyproject,
)


def test_parse_version_reads_three_numbers():
    assert parse_version("0.12.3") == (0, 12, 3)
    assert parse_version("v1.0.0") == (1, 0, 0)


def test_parse_version_refuses_two_parts():
    with pytest.raises(ValueError):
        parse_version("0.2")


def test_parse_version_refuses_words():
    with pytest.raises(ValueError):
        parse_version("0.2.beta")


def test_set_version_touches_only_the_project_version():
    text = '[project]\nversion = "0.1.0"\n[tool.ruff]\ntarget-version = "py312"\n'
    out = set_version_pyproject(text, "0.2.0")
    assert 'version = "0.2.0"' in out and 'target-version = "py312"' in out
    assert '"0.1.0"' not in out


def test_set_version_in_the_package():
    text = '"""JoJo Arena."""\n\n__version__ = "0.1.0"\n'
    assert '__version__ = "0.2.0"' in set_version_init(text, "0.2.0")


def test_close_unreleased_keeps_an_empty_section_on_top():
    log = "# Journal\n\n## Non publié\n\n### Ajouté\n\n- Avdol.\n"
    out = close_unreleased(log, "0.2.0", "2026-11-14")
    assert out.index("## Non publié") < out.index("## 0.2.0 - 2026-11-14") < out.index("- Avdol.")


def test_close_unreleased_refuses_an_empty_section():
    with pytest.raises(ValueError):
        close_unreleased(
            "# Journal\n\n## Non publié\n\n## 0.1.0 - 2026-01-01\n", "0.2.0", "2026-11-14"
        )


def test_close_unreleased_refuses_a_changelog_without_the_section():
    with pytest.raises(ValueError):
        close_unreleased("# Journal\n\n## 0.1.0 - 2026-01-01\n\n- x\n", "0.2.0", "2026-11-14")


def test_check_refuses_a_version_not_above_the_tag():
    log = "## Non publié\n\n## 0.2.0 - 2026-11-14\n\n- x\n"
    assert check_release("0.2.0", "v0.2.0", log)
    assert check_release("0.1.9", "v0.2.0", log)
    assert check_release("0.2.0", "v0.1.0", log) == []


def test_the_last_release_is_the_highest_tag_not_the_latest_written():
    # The tag sits on main's merge commit, which develop does not contain: the check
    # cannot ask git for the tag "before" the commit it tests.
    assert highest_tag(["v0.2.0", "v0.10.0", "v0.9.1", "not-a-release"]) == "v0.10.0"
    assert highest_tag([]) is None


def test_check_accepts_the_first_release_and_wants_its_section():
    assert check_release("0.1.0", None, "## Non publié\n\n## 0.1.0 - 2026-11-14\n\n- x\n") == []
    assert check_release("0.1.0", None, "## Non publié\n\n- x\n")  # no section of its own


def test_check_refuses_a_malformed_version_even_without_a_tag():
    # No release exists yet: a hand-edited "0.2" must not slip through and become the
    # tag every later check compares against.
    assert check_release("0.2", None, "## Non publié\n\n## 0.2 - 2026-11-15\n\n- x\n")
