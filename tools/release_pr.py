"""Prepare a release: one command on develop, the merge into main does the rest.

    python tools/release_pr.py 0.2.0     # bump, close the changelog, push, open the PR
    python tools/release_pr.py --check   # CI, on a PR into main: is this a new version?
    python tools/release_pr.py --version # the version the package says it is

The version lives in two places (pyproject.toml and jojo_arena/__init__.py). The
changelog keeps an empty `## Non publié` on top and gets a `## X.Y.Z - date` section
under it. Once the PR is merged, .github/workflows/release.yml builds the .exe, tags
vX.Y.Z and publishes the Release with that section as its notes.
"""

from __future__ import annotations

import datetime
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_notes import UNRELEASED, notes_for  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "jojo_arena" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"


def parse_version(text: str) -> tuple[int, int, int]:
    """`0.2.0` or `v0.2.0` as three numbers; anything else is refused."""
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", text.strip())
    if not match:
        raise ValueError(f"not a version X.Y.Z: {text!r}")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def set_version_pyproject(text: str, version: str) -> str:
    """The `version = "..."` line of [project], and nothing else."""
    out, count = re.subn(r'(?m)^version = "[^"]*"$', f'version = "{version}"', text, count=1)
    if not count:
        raise ValueError("pyproject.toml has no version line")
    return out


def set_version_init(text: str, version: str) -> str:
    out, count = re.subn(r'(?m)^__version__ = "[^"]*"$', f'__version__ = "{version}"', text)
    if not count:
        raise ValueError("jojo_arena/__init__.py has no __version__")
    return out


def _unreleased_span(changelog: str) -> tuple[int, int]:
    """Where the body of `## Non publié` starts and ends in the text."""
    heading = re.search(rf"(?m)^## {re.escape(UNRELEASED)}\s*$", changelog)
    if heading is None:
        raise ValueError(f"the changelog has no '## {UNRELEASED}' section")
    following = re.search(r"(?m)^## ", changelog[heading.end() :])
    end = heading.end() + following.start() if following else len(changelog)
    return heading.end(), end


def close_unreleased(changelog: str, version: str, date: str) -> str:
    """Give what `## Non publié` says to `## <version> - <date>`, and leave an empty
    `## Non publié` above it for what comes next."""
    start, end = _unreleased_span(changelog)
    if not changelog[start:end].strip():
        raise ValueError(f"'## {UNRELEASED}' is empty: nothing to release")
    return f"{changelog[:start]}\n\n## {version} - {date}{changelog[start:]}"


def check_release(version: str, last_tag: str | None, changelog: str) -> list[str]:
    """What stops this version from being released (nothing: an empty list)."""
    problems = []
    if last_tag is not None and parse_version(version) <= parse_version(last_tag):
        problems.append(f"version {version} is not above the last release {last_tag}")
    if not re.search(rf"(?m)^## {re.escape(version)}(\s|$)", changelog):
        problems.append(f"the changelog has no '## {version} - <date>' section")
    return problems


# The commands --------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def current_version() -> str:
    match = re.search(r'(?m)^__version__ = "([^"]*)"$', INIT.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError("jojo_arena/__init__.py has no __version__")
    return match.group(1)


def last_tag() -> str | None:
    found = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v*"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return found.stdout.strip() if found.returncode == 0 else None


def _check() -> int:
    problems = check_release(current_version(), last_tag(), CHANGELOG.read_text("utf-8"))
    for problem in problems:
        print(f"::error::{problem}")
    if not problems:
        print(f"version {current_version()} is ready to be released")
    return 1 if problems else 0


def _prepare(version: str) -> int:
    parse_version(version)
    if _git("rev-parse", "--abbrev-ref", "HEAD") != "develop":
        print("a release is prepared from develop", file=sys.stderr)
        return 1
    if _git("status", "--porcelain"):
        print("develop has uncommitted changes", file=sys.stderr)
        return 1
    _git("fetch", "-q", "origin", "develop")
    if _git("rev-parse", "HEAD") != _git("rev-parse", "origin/develop"):
        print("develop is not the same as origin/develop: pull or push first", file=sys.stderr)
        return 1
    problems = check_release(version, last_tag(), f"## {version}\n")
    if problems:
        print(problems[0], file=sys.stderr)
        return 1

    today = datetime.date.today().isoformat()
    changelog = close_unreleased(CHANGELOG.read_text("utf-8"), version, today)
    PYPROJECT.write_text(set_version_pyproject(PYPROJECT.read_text("utf-8"), version), "utf-8")
    INIT.write_text(set_version_init(INIT.read_text("utf-8"), version), "utf-8")
    CHANGELOG.write_text(changelog, "utf-8")

    title = f"chore: release {version}"
    _git("commit", "-am", title)
    _git("push", "origin", "develop")
    with tempfile.TemporaryDirectory() as temp:
        body = Path(temp) / "notes.md"
        body.write_text(notes_for(version, changelog), "utf-8")
        subprocess.run(
            ["gh", "pr", "create", "--base", "main", "--head", "develop"]
            + ["--title", title, "--body-file", str(body)],
            cwd=ROOT,
            check=True,
        )
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--check"]:
        return _check()
    if argv == ["--version"]:
        print(current_version())
        return 0
    if len(argv) == 1 and not argv[0].startswith("-"):
        return _prepare(argv[0])
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
