"""Claude Code hook: format and auto-fix a Python file right after it is written.

Registered as a PostToolUse hook in `.claude/settings.json`. It reads the hook payload
on stdin, and when the tool touched a .py file of this repository it runs ruff on that
one file. The point is that `make check` never fails on formatting alone.

It stays silent and always exits 0: a hook must never stand between the writer and
their work. Run it by hand to see what it would do:

    echo '{"tool_input": {"file_path": "jojo_arena/app.py"}}' | python tools/hooks/format_python.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON = (
    ROOT / ".venv" / "Scripts" / "python.exe",  # Windows
    ROOT / ".venv" / "bin" / "python",  # everywhere else
)


def python_executable() -> str:
    """The project's own interpreter when there is one, else the current one."""
    for candidate in VENV_PYTHON:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def touched_file(payload: object) -> Path | None:
    """The .py file inside this repository the tool just wrote, if any."""
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input")
    raw = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(raw, str) or not raw.endswith(".py"):
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    try:
        path.relative_to(ROOT)
    except ValueError:
        return None  # somewhere else on the disk: not ours to format
    return path if path.exists() else None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    path = touched_file(payload)
    if path is None:
        return 0
    python = python_executable()
    for arguments in (["format", str(path)], ["check", "--fix", "--quiet", str(path)]):
        try:
            subprocess.run(
                [python, "-m", "ruff", *arguments],
                cwd=ROOT,
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return 0  # no ruff, no venv, no matter: never block the write
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
