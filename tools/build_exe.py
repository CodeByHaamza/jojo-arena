"""Build the single-file Windows executable with PyInstaller.

    python tools/build_exe.py

Output: dist/JoJoArena.exe. Every data file of the package (TOML, sprites...) is
bundled inside, so the .exe runs on its own.
"""

from __future__ import annotations

from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    PyInstaller.__main__.run(
        [
            str(ROOT / "jojo_arena" / "__main__.py"),
            "--name",
            "JoJoArena",
            "--onefile",
            "--windowed",
            "--noconfirm",
            "--clean",
            "--paths",
            str(ROOT),
            "--collect-data",
            "jojo_arena",
            "--distpath",
            str(ROOT / "dist"),
            "--workpath",
            str(ROOT / "build"),
            "--specpath",
            str(ROOT / "build"),
        ]
    )


if __name__ == "__main__":
    main()
