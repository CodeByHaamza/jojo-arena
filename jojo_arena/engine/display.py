"""Low-resolution render target scaled to the window with nearest-neighbour filtering.

Everything is drawn on a small internal surface, then blown up by the largest
integer factor that fits the window, centered with black bars.
"""

from __future__ import annotations

import pygame

BLACK = (0, 0, 0)


def compute_viewport(
    window_size: tuple[int, int], internal_size: tuple[int, int]
) -> tuple[int, pygame.Rect]:
    """Return (scale, destination rect) for the internal surface inside the window."""
    win_w, win_h = window_size
    int_w, int_h = internal_size
    scale = max(1, min(win_w // int_w, win_h // int_h))
    width, height = int_w * scale, int_h * scale
    return scale, pygame.Rect((win_w - width) // 2, (win_h - height) // 2, width, height)


def best_window_scale(
    desktop_size: tuple[int, int], internal_size: tuple[int, int], margin: tuple[int, int]
) -> int:
    """Largest integer scale whose window still fits the desktop minus a margin."""
    usable_w = desktop_size[0] - margin[0]
    usable_h = desktop_size[1] - margin[1]
    return max(1, min(usable_w // internal_size[0], usable_h // internal_size[1]))


class Display:
    # Room left for the title bar and taskbar when picking the windowed size.
    WINDOW_MARGIN = (0, 120)

    def __init__(
        self, title: str, internal_size: tuple[int, int], fullscreen: bool = False
    ) -> None:
        self.internal_size = internal_size
        self.surface = pygame.Surface(internal_size)
        pygame.display.set_caption(title)
        desktop = pygame.display.get_desktop_sizes()[0]
        scale = best_window_scale(desktop, internal_size, self.WINDOW_MARGIN)
        self.windowed_size = (internal_size[0] * scale, internal_size[1] * scale)
        self.fullscreen = fullscreen
        self._scaled: pygame.Surface | None = None
        self._apply_mode()

    def _apply_mode(self) -> None:
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self._apply_mode()

    def present(self) -> None:
        window = pygame.display.get_surface()
        _, dest = compute_viewport(window.get_size(), self.internal_size)
        if self._scaled is None or self._scaled.get_size() != dest.size:
            self._scaled = pygame.Surface(dest.size)
        pygame.transform.scale(self.surface, dest.size, self._scaled)
        window.fill(BLACK)
        window.blit(self._scaled, dest)
        pygame.display.flip()

    def window_to_internal(self, pos: tuple[int, int]) -> tuple[int, int]:
        window = pygame.display.get_surface()
        scale, dest = compute_viewport(window.get_size(), self.internal_size)
        return (pos[0] - dest.x) // scale, (pos[1] - dest.y) // scale
