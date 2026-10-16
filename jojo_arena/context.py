"""Shared services handed to every scene."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jojo_arena.controls import ControlsConfig, menu_sources, save_controls
from jojo_arena.engine.actions import InputFrame, merge_frames
from jojo_arena.engine.display import Display
from jojo_arena.engine.input import GamepadSource, InputManager, KeyboardSource
from jojo_arena.engine.scene import SceneManager
from jojo_arena.settings import Settings, save_settings, settings_path


@dataclass
class GameContext:
    display: Display
    inputs: InputManager
    scenes: SceneManager
    controls: ControlsConfig
    controls_path: Path
    settings: Settings = field(default_factory=Settings)
    _menu_sources: list[KeyboardSource | GamepadSource] = field(default_factory=menu_sources)

    def read_menu(self) -> InputFrame:
        """Menus listen to any keyboard and any pad. Call once per logic step."""
        return merge_frames(*(source.read(self.inputs) for source in self._menu_sources))

    def save_controls(self) -> None:
        save_controls(self.controls, self.controls_path)

    def save_settings(self) -> None:
        save_settings(self.settings, settings_path(self.controls_path))
