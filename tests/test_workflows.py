"""The guards written in the workflows themselves: who gets a write token, and which
branch a release can come from. Plain text checks (the project has no YAML parser):
each one fails if the guard is taken out."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")


def _job(name: str) -> str:
    """The text of one job of release.yml, up to the next job."""
    start = RELEASE.index(f"\n  {name}:\n")
    rest = RELEASE[start + 1 :]
    following = [rest.find(f"\n  {other}:\n") for other in ("linux", "windows") if other != name]
    ends = [i for i in following if i > 0]
    return rest[: min(ends)] if ends else rest


def test_the_release_workflow_reads_by_default():
    # The linux job runs on the home server: it must not hold a token that can push,
    # tag or publish.
    head = RELEASE[: RELEASE.index("\njobs:")]
    assert "permissions:\n  contents: read" in head
    assert "contents: write" not in _job("linux")


def test_only_the_windows_job_can_publish():
    assert "permissions:\n      contents: write" in _job("windows")


def test_a_release_only_ever_comes_from_main():
    # Run by hand from develop (the default branch), it would tag develop's head.
    for job in ("linux", "windows"):
        assert "if: github.ref == 'refs/heads/main'" in _job(job), job


def test_ruff_leaves_markdown_alone():
    # The CI skips documentation-only pull requests, so a Python block in a Markdown
    # file must never be what turns the next pull request red.
    ruff = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["ruff"]
    assert "*.md" in ruff.get("extend-exclude", [])


def test_ruff_is_one_known_version():
    # A new ruff release must not turn every pull request red overnight.
    dev = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert any(dep.startswith("ruff==") for dep in dev["optional-dependencies"]["dev"])
