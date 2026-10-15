"""Scenes (title screen, fight, results...) and the manager that switches between them."""

from __future__ import annotations

import pygame


class Scene:
    """One screen of the game. `update` runs once per fixed logic step."""

    def __init__(self) -> None:
        self.manager: SceneManager | None = None

    def on_enter(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


class SceneManager:
    def __init__(self) -> None:
        self.current: Scene | None = None
        self._pending: Scene | None = None
        self.quit_requested = False

    def switch(self, scene: Scene) -> None:
        """Change scene at the end of the current step, never in the middle of one."""
        self._pending = scene

    def quit(self) -> None:
        self.quit_requested = True

    def apply_pending(self) -> None:
        if self._pending is not None:
            self.current = self._pending
            self._pending = None
            self.current.manager = self
            self.current.on_enter()
