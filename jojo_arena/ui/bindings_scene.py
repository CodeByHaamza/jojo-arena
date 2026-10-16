"""Key bindings, changed in the game: pick an action and a player, then press the new key
(or pad button). A key already used by another action of that player swaps with it.
Saved to controls.json at once."""

from __future__ import annotations

from dataclasses import replace

import pygame

from jojo_arena.context import GameContext
from jojo_arena.controls import DEFAULT_PRESETS, PlayerControls
from jojo_arena.engine import audio, font, music
from jojo_arena.engine.input import KEY_SCANCODES, PAD_BUTTON_NAMES
from jojo_arena.engine.scene import Scene
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.labels import action_label, device_label, menu_key, preset_label
from jojo_arena.ui.widgets import DIM, FAINT, GOLD, P1_COLOR, P2_COLOR, WHITE, draw_box, draw_hints

ACTIONS = (
    "up",
    "down",
    "left",
    "right",
    "light",
    "heavy",
    "special",
    "stand",
    "dash",
    "guard",
    "heart_heat",
    "pose",
    "pause",
)
EXTRA_ROWS = ("reset", "back")
SCANCODE_NAMES = {code: name for name, code in reversed(list(KEY_SCANCODES.items()))}
TABLE = pygame.Rect(60, 40, 360, 186)
COLUMNS = (TABLE.x + 10, TABLE.x + 200, TABLE.x + 296)
ROW_H = 12


def rebind(player: PlayerControls, action: str, name: str) -> PlayerControls:
    """The player's bindings with `name` first for `action`; an action that had it first
    gets the action's old key instead (a swap). Other keys of the action stay."""
    bindings = {key: list(names) for key, names in player.bindings.items()}
    old = bindings.get(action, [])
    previous = old[0] if old else None
    for other in ACTIONS:
        names = bindings.get(other, [])
        if other != action and names and names[0] == name and previous is not None:
            names[0] = previous
    bindings[action] = [name] + [n for n in old[1:] if n != name]
    return replace(player, bindings=bindings)


class BindingsScene(Scene):
    def __init__(self, ctx: GameContext) -> None:
        super().__init__()
        music.request("menu")
        self.ctx = ctx
        self.backdrop = MenuBackdrop()
        self.row = 0
        self.column = 0
        self.waiting = False  # waiting for the new key
        self.tick = 0

    @property
    def rows(self) -> int:
        return len(ACTIONS) + len(EXTRA_ROWS)

    @property
    def preset(self):
        return self.ctx.controls.active_preset

    def update(self) -> None:
        self.tick += 1
        if self.waiting:
            self._listen()
            return
        frame = self.ctx.read_menu()
        if frame.was_pressed("up"):
            self.row = (self.row - 1) % self.rows
            audio.play("menu_move")
        if frame.was_pressed("down"):
            self.row = (self.row + 1) % self.rows
            audio.play("menu_move")
        if frame.was_pressed("left") or frame.was_pressed("right"):
            self.column = 1 - self.column
            audio.play("menu_move")
        if frame.was_pressed("confirm"):
            audio.play("menu_ok")
            if self.row < len(ACTIONS):
                self.waiting = True
            elif EXTRA_ROWS[self.row - len(ACTIONS)] == "reset":
                self._reset()
            else:
                self._leave()
        elif frame.was_pressed("back"):
            audio.play("menu_back")
            self._leave()

    def _listen(self) -> None:
        """The next key (keyboard player) or button (pad player) becomes the binding."""
        player = self.preset.players[self.column]
        inputs = self.ctx.inputs
        name = None
        if player.device == "keyboard":
            for code in inputs.key_presses:
                if code == KEY_SCANCODES["Escape"]:
                    self.waiting = False  # cancelled
                    audio.play("menu_back")
                    return
                name = SCANCODE_NAMES.get(code) or name
        else:
            pads = inputs.pads
            pad = pads[player.slot] if player.slot < len(pads) else (pads[0] if pads else None)
            if pad is not None:
                name = next((n for n in pad.presses if n in PAD_BUTTON_NAMES), None)
            if any(code == KEY_SCANCODES["Escape"] for code in inputs.key_presses):
                self.waiting = False
                return
        if name is None:
            return
        self._set(self.column, rebind(player, ACTIONS[self.row], name))
        self.waiting = False
        audio.play("menu_ok")

    def _set(self, index: int, player: PlayerControls) -> None:
        preset = self.preset
        players = list(preset.players)
        players[index] = player
        self.ctx.controls.presets[preset.key] = replace(preset, players=(players[0], players[1]))
        self.ctx.save_controls()

    def _reset(self) -> None:
        default = DEFAULT_PRESETS.get(self.preset.key)
        if default is None:
            return
        for index, raw in enumerate(default["players"]):
            bindings = {action: list(names) for action, names in raw["bindings"].items()}
            self._set(index, replace(self.preset.players[index], bindings=bindings))

    def _leave(self) -> None:
        from jojo_arena.ui.options_scene import OptionsScene

        scene = OptionsScene(self.ctx)
        scene.menu.select("keys")
        self.ctx.scenes.switch(scene)

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        font.draw(surface, text.KEYS_TITLE, (width // 2, 6), GOLD, scale=2, align="center")
        font.draw(surface, preset_label(self.preset), (width // 2, 26), DIM, align="center")
        draw_box(surface, TABLE)
        y = TABLE.y + 6
        players = self.preset.players
        font.draw(surface, text.BINDINGS_ACTION, (COLUMNS[0], y), GOLD)
        for i, (player, color) in enumerate(zip(players, (P1_COLOR, P2_COLOR), strict=True)):
            label = f"{text.PLAYER_N.format(n=i + 1)} {device_label(player)}"
            font.draw(surface, label, (COLUMNS[1 + i], y), color, align="center")
        y += 14
        names = {**text.ACTION_NAMES, **text.DIRECTION_NAMES}
        for row, action in enumerate(ACTIONS):
            selected_row = row == self.row
            font.draw(
                surface,
                names.get(action, action.upper()),
                (COLUMNS[0], y),
                WHITE if selected_row else DIM,
            )
            for i, player in enumerate(players):
                key = action_label(player, action, self.ctx.inputs)
                selected = selected_row and i == self.column
                if selected:
                    cell = pygame.Rect(0, 0, 80, ROW_H)
                    cell.center = (COLUMNS[1 + i], y + 4)
                    surface.fill((60, 48, 96), cell)
                    if self.waiting and (self.tick // 15) % 2 == 0:
                        key = "..."
                font.draw(
                    surface, key, (COLUMNS[1 + i], y), GOLD if selected else WHITE, align="center"
                )
            y += ROW_H
        for k, extra in enumerate(EXTRA_ROWS):
            label = text.RESET_KEYS if extra == "reset" else text.BACK
            color = GOLD if self.row == len(ACTIONS) + k else WHITE
            font.draw(
                surface, label, (width // 2, TABLE.bottom + 4 + k * 11), color, align="center"
            )
        if self.waiting:
            player = players[self.column]
            ask = text.PRESS_KEY if player.device == "keyboard" else text.PRESS_BUTTON
            font.draw(surface, ask, (width // 2, height - 26), GOLD, align="center")
            font.draw(surface, text.CANCEL_HINT, (width // 2, height - 14), FAINT, align="center")
        else:
            hints = [
                (menu_key("confirm", self.ctx.inputs), text.HINT_CONFIRM),
                ("←→", text.HINT_PLAYER),
                (menu_key("back", self.ctx.inputs), text.HINT_BACK),
            ]
            draw_hints(surface, hints, (width // 2, height - 12))
