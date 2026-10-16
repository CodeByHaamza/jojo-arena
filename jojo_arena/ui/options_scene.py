"""Options: control preset, fullscreen, and a table of the keys of both players."""

from __future__ import annotations

import pygame

from jojo_arena.context import GameContext
from jojo_arena.engine import audio, font, i18n, music
from jojo_arena.engine.input import LAYOUTS, detected_layout, set_layout
from jojo_arena.engine.scene import Scene
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.labels import (
    PAD_STYLES,
    action_label,
    device_label,
    menu_key,
    move_label,
    pad_family,
    pad_name,
    preset_label,
    set_pad_style,
)
from jojo_arena.ui.menu import Menu, MenuItem
from jojo_arena.ui.widgets import DIM, GOLD, P1_COLOR, P2_COLOR, WHITE, draw_box, draw_hints

WARNING = (240, 90, 90)
TABLE = pygame.Rect(70, 108, 340, 132)
COLUMNS = (TABLE.x + 10, TABLE.x + 190, TABLE.x + 282)  # action, J1, J2 (centers for J1/J2)


def naming_labels(choices: tuple[str, ...], auto: str, names: dict, found: str) -> list[str]:
    """Menu values for a naming choice: "AUTO (AZERTY)", then the forced ones."""
    detected = names.get(found, found.upper())
    return [auto.format(name=detected) if c == "auto" else names[c] for c in choices]


class OptionsScene(Scene):
    def __init__(self, ctx: GameContext) -> None:
        super().__init__()
        music.request("menu")
        self.ctx = ctx
        self.backdrop = MenuBackdrop()
        self.preset_keys = list(ctx.controls.presets)
        labels = [preset_label(ctx.controls.presets[k]) for k in self.preset_keys]
        self.menu = Menu(
            [
                MenuItem(
                    "controls", text.CONTROLS, labels, self.preset_keys.index(ctx.controls.active)
                ),
                MenuItem("keys", text.REBIND),
                MenuItem(
                    "layout",
                    text.LAYOUT,
                    naming_labels(LAYOUTS, text.LAYOUT_AUTO, text.LAYOUT_NAMES, detected_layout()),
                    LAYOUTS.index(ctx.settings.layout),
                ),
                MenuItem(
                    "pad_style",
                    text.PAD_STYLE,
                    naming_labels(
                        PAD_STYLES,
                        text.PAD_STYLE_AUTO,
                        text.PAD_STYLE_NAMES,
                        pad_family(ctx.inputs, 0),
                    ),
                    PAD_STYLES.index(ctx.settings.pad_style),
                ),
                MenuItem("fullscreen", text.FULLSCREEN, [text.NO, text.YES]),
                MenuItem(
                    "language",
                    text.LANGUAGE,
                    [text.LANGUAGE_NAMES[code] for code in i18n.LANGUAGES],
                    i18n.LANGUAGES.index(i18n.language()),
                ),
                MenuItem("volume", text.VOLUME, [str(n) for n in range(11)], ctx.settings.volume),
                MenuItem(
                    "music", text.MUSIC, [str(n) for n in range(11)], ctx.settings.music_volume
                ),
                MenuItem("rumble", text.RUMBLE, [str(n) for n in range(11)], ctx.settings.rumble),
                MenuItem("back", text.BACK),
            ]
        )
        self.tick = 0
        self.hints = [(menu_key("back", ctx.inputs), text.HINT_BACK)]

    def update(self) -> None:
        self.tick += 1
        # F11 may have changed the window since the last step.
        self.menu.item("fullscreen").index = int(self.ctx.display.fullscreen)
        action = self.menu.handle(self.ctx.read_menu())
        if action is None:
            return
        kind, key = action
        if kind == "change" and key == "controls":
            self.ctx.controls.active = self.preset_keys[self.menu.item("controls").index]
            self.ctx.save_controls()
        elif kind == "change" and key == "fullscreen":
            if bool(self.menu.item("fullscreen").index) != self.ctx.display.fullscreen:
                self.ctx.display.toggle_fullscreen()
        elif kind == "change" and key == "volume":
            self.ctx.settings.volume = self.menu.item("volume").index
            self.ctx.save_settings()
            if audio._player is not None:
                audio._player.volume = self.ctx.settings.volume / 10
            audio.play("menu_ok")
        elif kind == "change" and key == "music":
            self.ctx.settings.music_volume = self.menu.item("music").index
            self.ctx.save_settings()
            music.set_volume(self.ctx.settings.music_volume / 10)
        elif kind == "change" and key in ("layout", "pad_style"):
            # Only the names shown change: the bindings are physical key positions.
            if key == "layout":
                self.ctx.settings.layout = LAYOUTS[self.menu.item("layout").index]
                set_layout(self.ctx.settings.layout)
            else:
                self.ctx.settings.pad_style = PAD_STYLES[self.menu.item("pad_style").index]
                set_pad_style(self.ctx.settings.pad_style)
            self.ctx.save_settings()
            scene = OptionsScene(self.ctx)
            scene.menu.select(key)
            self.ctx.scenes.switch(scene)
        elif kind == "change" and key == "rumble":
            self.ctx.settings.rumble = self.menu.item("rumble").index
            self.ctx.save_settings()
            audio.play("menu_ok")
        elif kind == "change" and key == "language":
            code = i18n.LANGUAGES[self.menu.item("language").index]
            i18n.set_language(code)
            self.ctx.settings.language = code
            self.ctx.save_settings()
            # Rebuild the screen so every label is in the new language.
            scene = OptionsScene(self.ctx)
            scene.menu.select("language")
            self.ctx.scenes.switch(scene)
        elif kind == "confirm" and key == "keys":
            from jojo_arena.ui.bindings_scene import BindingsScene

            self.ctx.scenes.switch(BindingsScene(self.ctx))
        elif kind == "back" or (kind == "confirm" and key == "back"):
            from jojo_arena.ui.main_menu import MainMenuScene

            self.ctx.scenes.switch(MainMenuScene(self.ctx, cursor="options"))

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        font.draw(surface, text.OPTIONS_TITLE, (width // 2, 0), GOLD, scale=3, align="center")
        self.menu.draw(surface, width // 2, 27, spacing=9)

        preset = self.ctx.controls.active_preset
        draw_box(surface, TABLE)
        y = TABLE.y + 6
        font.draw(surface, text.BINDINGS_ACTION, (COLUMNS[0], y), GOLD)
        for i, (player, color) in enumerate(zip(preset.players, (P1_COLOR, P2_COLOR), strict=True)):
            label = f"{text.PLAYER_N.format(n=i + 1)} {device_label(player)}"
            font.draw(surface, label, (COLUMNS[1 + i], y), color, align="center")
        y += 13
        for action, name in text.ACTION_NAMES.items():
            font.draw(surface, name, (COLUMNS[0], y), DIM)
            for i, player in enumerate(preset.players):
                if action == "move":
                    key = move_label(player)
                else:
                    key = action_label(player, action, self.ctx.inputs)
                font.draw(surface, key, (COLUMNS[1 + i], y), WHITE, align="center")
            y += 11

        if preset.pads_needed() > len(self.ctx.inputs.pads):
            font.draw(
                surface, text.PADS_MISSING, (width // 2, TABLE.bottom + 2), WARNING, align="center"
            )
        else:
            font.draw(
                surface, self.pads_line(), (width // 2, TABLE.bottom + 2), DIM, align="center"
            )
        draw_hints(surface, self.hints, (width // 2, height - 14))

    def pads_line(self) -> str:
        """Which pads the game actually sees, by their own name."""
        pads = self.ctx.inputs.pads
        if not pads:
            return text.PAD_NONE
        return "   ".join(
            text.PAD_DETECTED.format(n=i + 1, name=pad_name(self.ctx.inputs, i))
            for i in range(len(pads))
        )
