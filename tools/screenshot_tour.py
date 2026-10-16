"""Screenshot tour: play through every screen with scripted keys and save a picture of each.

Handy to check the menus at a glance after a change, without playing by hand:

    python tools/screenshot_tour.py              # pictures in screenshots/tour/
    python tools/screenshot_tour.py out --scale 1

Runs in a hidden window. The controls file used is a temporary one, never the player's.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

from jojo_arena import controls  # noqa: E402
from jojo_arena.context import GameContext  # noqa: E402
from jojo_arena.engine.display import Display  # noqa: E402
from jojo_arena.engine.geometry import Vec2  # noqa: E402
from jojo_arena.engine.input import KEY_SCANCODES, InputManager  # noqa: E402
from jojo_arena.engine.scene import SceneManager  # noqa: E402

DEFAULT_OUT = Path("screenshots") / "tour"


class Tour:
    def __init__(self, out_dir: Path, scale: int, controls_file: Path) -> None:
        self.out_dir = out_dir
        self.scale = scale
        self.saved: list[Path] = []
        config, _ = controls.parse_controls(None)
        self.ctx = GameContext(
            Display("tour", (480, 270)), InputManager(), SceneManager(), config, controls_file
        )

    @property
    def scene(self):
        return self.ctx.scenes.current

    def start(self, scene) -> None:
        self.ctx.scenes.switch(scene)
        self.ctx.scenes.apply_pending()
        self.wait(1)

    def wait(self, steps: int) -> None:
        for _ in range(steps):
            self.ctx.inputs.begin_step()
            self.scene.update()
            self.ctx.scenes.apply_pending()
            self.scene.draw(self.ctx.display.surface)

    def _key(self, name: str, down: bool) -> None:
        kind = pygame.KEYDOWN if down else pygame.KEYUP
        event = pygame.event.Event(kind, scancode=KEY_SCANCODES[name], key=0, mod=0)
        self.ctx.inputs.handle_event(event)

    def keys(self, *names: str, wait: int = 2) -> None:
        """Tap keys one after the other (key names as in controls.json)."""
        for name in names:
            self._key(name, True)
            self._key(name, False)
            self.wait(wait)

    def choose(self, menu, key: str, wait: int = 2) -> None:
        """Move down a menu until `key` is highlighted, then confirm it."""
        for _ in range(len(menu.items)):
            if menu.selected.key == key:
                break
            self.keys("Down", wait=1)
        self.keys("Return", wait=wait)

    def shot(self, name: str) -> None:
        image = self.ctx.display.surface
        if self.scale != 1:
            image = pygame.transform.scale_by(image, self.scale)
        path = self.out_dir / f"{len(self.saved) + 1:02d}_{name}.png"
        pygame.image.save(image, str(path))
        self.saved.append(path)


def run_tour(out_dir: Path = DEFAULT_OUT, scale: int = 2) -> list[Path]:
    """Play the tour and return the pictures saved, in order."""
    from jojo_arena.ui.title_scene import TitleScene

    out_dir.mkdir(parents=True, exist_ok=True)
    pygame.init()
    try:
        with tempfile.TemporaryDirectory() as temp:
            tour = Tour(out_dir, scale, Path(temp) / "controls.json")
            _play(tour, TitleScene(tour.ctx))
    finally:
        pygame.quit()
    return tour.saved


def _play(tour: Tour, title) -> None:
    tour.start(title)
    tour.wait(40)
    tour.shot("title")
    tour.keys("Return", wait=30)
    tour.shot("main_menu")
    tour.choose(tour.scene.menu, "arcade", wait=10)  # a mode still to come
    tour.shot("main_menu_soon")
    tour.wait(90)

    # Training: character select, move list, the dummy.
    tour.choose(tour.scene.menu, "training", wait=20)
    tour.shot("select_training")
    tour.keys("Tab", wait=3)
    for page in range(len(tour.scene.move_list.pages)):
        tour.shot(f"move_list_page{page + 1}")
        tour.keys("Right")
    tour.keys("Escape")
    tour.keys("Return")  # player 1
    tour.keys("Right", wait=20)
    tour.shot("select_dummy")
    tour.keys("Down", "Return", wait=5)  # a slot still to come
    tour.shot("select_soon")
    tour.keys("E", wait=5)  # the next part's tab
    tour.shot("select_next_part")
    tour.keys("Q", wait=5)
    tour.keys("Up", "Return", wait=30)
    training = tour.scene
    attacker, dummy = training.rounds.match.fighters
    attacker.pos = dummy.pos - Vec2(24, 0)
    for _ in range(4):
        tour.keys("J", wait=10)
    tour.shot("training_combo")
    tour.keys("Escape", wait=3)
    tour.shot("training_pause")
    tour.choose(training.pause_menu, "moves", wait=3)
    tour.shot("training_move_list")
    tour.keys("Escape", wait=3)
    tour.choose(training.pause_menu, "menu", wait=10)

    # Local fight: select, VS screen, fight, pause, result.
    tour.choose(tour.scene.menu, "versus", wait=10)
    tour.keys("Return", "Right", "Return", wait=20)
    tour.shot("vs_screen")
    tour.keys("Return", wait=60)
    tour.shot("fight_intro")
    tour.wait(120)
    tour.shot("fight")
    tour.keys("Escape", wait=3)
    tour.shot("fight_pause")
    tour.keys("Escape", wait=3)
    fight = tour.scene
    fight.rounds.match.fighters[1].hurt(fight.rounds.match.fighters[1].hp)
    tour.wait(60)
    tour.shot("knockout")

    # Options.
    from jojo_arena.ui.options_scene import OptionsScene

    tour.start(OptionsScene(tour.ctx))
    tour.wait(10)
    tour.shot("options")

    # Glossary: a term of part 1, then a character and a Stand of part 3.
    from jojo_arena.ui.glossary_scene import GlossaryScene

    tour.start(GlossaryScene(tour.ctx))
    tour.wait(10)
    tour.shot("glossary_term")
    tour.keys("E", "E", "Right", wait=5)
    tour.shot("glossary_character")
    tour.keys("Right", wait=5)
    tour.shot("glossary_stand")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", nargs="?", type=Path, default=DEFAULT_OUT, help="output folder")
    parser.add_argument("--scale", type=int, default=2, help="enlarge the pictures (default 2)")
    args = parser.parse_args()
    saved = run_tour(args.out, args.scale)
    print(f"{len(saved)} screenshots in {args.out}")


if __name__ == "__main__":
    main()
