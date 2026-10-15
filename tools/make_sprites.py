"""Generate character sprite sheets from look files (data, no drawing by hand).

    python tools/make_sprites.py              # every look
    python tools/make_sprites.py jotaro_p3    # only these looks

Looks: tools/spritegen/mannequin.toml and jojo_arena/characters/looks/*.toml.
Sheets go to jojo_arena/assets/sprites/<id>/; enlarged previews to build/sprite_previews/.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from spritegen.look import load_look  # noqa: E402
from spritegen.sheet import portrait, preview, write_sheet  # noqa: E402

LOOK_FILES = [
    ROOT / "tools" / "spritegen" / "mannequin.toml",
    *sorted((ROOT / "jojo_arena" / "characters" / "looks").glob("*.toml")),
]
SPRITES_DIR = ROOT / "jojo_arena" / "assets" / "sprites"
PREVIEW_DIR = ROOT / "build" / "sprite_previews"


def main(argv: list[str]) -> None:
    pygame.init()
    wanted = set(argv)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for path in LOOK_FILES:
        if wanted and path.stem not in wanted:
            continue
        look = load_look(path)
        sheet = write_sheet(look, SPRITES_DIR)
        pygame.image.save(preview(look, sheet), str(PREVIEW_DIR / f"{look.id}_sheet.png"))
        pygame.image.save(portrait(look), str(PREVIEW_DIR / f"{look.id}.png"))
        print(
            f"{look.id}: sheet {sheet.get_width()}x{sheet.get_height()}, preview in {PREVIEW_DIR}"
        )


if __name__ == "__main__":
    main(sys.argv[1:])
