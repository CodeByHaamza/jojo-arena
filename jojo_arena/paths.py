"""Where game files live (works from source and from the PyInstaller build)."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PACKAGE_DIR / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
