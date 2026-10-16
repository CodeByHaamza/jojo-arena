"""The fight screen: reads both players, steps the rounds, draws them; pause and results."""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

import pygame

from jojo_arena import __version__
from jojo_arena.characters import get_fighter
from jojo_arena.combat.ai import CpuPlayer
from jojo_arena.combat.replay import Replay, save_replay
from jojo_arena.combat.rounds import Phase, Rounds
from jojo_arena.combat.rules import load_rules
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.actions import NEUTRAL, InputFrame
from jojo_arena.engine.scene import Scene
from jojo_arena.stages import load_stage
from jojo_arena.ui import text
from jojo_arena.ui.fight_view import FightView
from jojo_arena.ui.hud import Hud
from jojo_arena.ui.labels import action_label
from jojo_arena.ui.menu import Menu, MenuItem
from jojo_arena.ui.movelist import MoveListPanel
from jojo_arena.ui.widgets import GOLD, draw_box, draw_toast, veil

RESULT_MENU_AFTER_F = 120  # let the victory sink in before offering a rematch
TOAST_F = 90
MOUSE_AIM_F = 60  # the mouse aims for a keyboard player if it moved in the last second


class FightScene(Scene):
    mode = "versus"  # which character select and menu entry this fight comes from

    def __init__(
        self,
        ctx: GameContext,
        rounds_to_win: int = 3,
        fighter_ids: tuple[str, str] = ("mannequin_red", "mannequin_blue"),
        stage_id: str = "cairo_night",
        bots: tuple[bool, bool] = (False, False),
        cpu_level: int = 2,
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.fighter_ids = fighter_ids
        self.fighter_defs = [get_fighter(i) for i in fighter_ids]
        self.stage = load_stage(stage_id)
        self.rules = load_rules()
        self.rounds_to_win = rounds_to_win
        self.sources = ctx.controls.active_preset.build_sources()
        self.cpu_level = cpu_level
        self.bots = [
            CpuPlayer(cpu_level, seed=i + 1) if bot else None for i, bot in enumerate(bots)
        ]
        self.demo = all(bots)
        if any(bots) and not self.demo:
            self.mode = "vs_cpu"
        self.view = FightView(self.stage, self.fighter_defs)
        self.hud = Hud(self.fighter_defs, [view.height for view in self.view.fighter_views])
        players = ctx.controls.active_preset.players
        self.hud.mash_keys = tuple(action_label(p, "light", ctx.inputs) for p in players)
        self.view.pose_keys = tuple(action_label(p, "pose", ctx.inputs) for p in players)
        self.pause_menu: Menu | None = None
        self.result_menu: Menu | None = None
        self.move_list: MoveListPanel | None = None
        self.paused_by = 0  # the player who paused: the move list shows their character
        self.stage_id = stage_id
        # Replays: every fight is recorded; a replay given here is played back instead.
        self.playback: Replay | None = None
        self.playback_step = 0
        self.toast_f = 0
        self._new_rounds()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            self.view.debug = not self.view.debug  # show hit and hurt circles
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F9 and self.playback is None:
            stamp = time.strftime("%Y%m%d-%H%M%S")
            self.save_replay(f"replay-{stamp}")
            self.toast_f = TOAST_F

    # Replays ----------------------------------------------------------------------------

    def replay_meta(self) -> dict:
        return {
            "game": __version__,
            "mode": self.mode,
            "fighters": list(self.fighter_ids),
            "stage": self.stage_id,
            "rounds_to_win": self.rounds_to_win,
        }

    def replays_dir(self) -> Path:
        return self.ctx.controls_path.parent / "replays"

    def save_replay(self, name: str = "derniere_partie") -> Path | None:
        """Keep the fight so far (not in demos, and not when watching a replay)."""
        if self.demo or self.playback is not None or not self.replay.frames:
            return None
        path = self.replays_dir() / f"{name}.json"
        try:
            save_replay(path, self.replay)
        except OSError:
            return None
        return path

    def apply_command(self, command: dict) -> None:
        """A pause-menu command found in a replay (fight variants handle theirs)."""

    def _new_rounds(self) -> None:
        kits = (self.fighter_defs[0].kit, self.fighter_defs[1].kit)
        self.rounds = Rounds(kits, self.rules, self.stage.build_arena, self.rounds_to_win)
        self.pause_menu = None
        self.result_menu = None
        self.replay = Replay(self.replay_meta())

    # Update -----------------------------------------------------------------------------

    def update(self) -> None:
        if self.move_list is not None:
            if not self.move_list.handle(self.ctx.read_menu()):
                self.move_list = None
            return
        if self.pause_menu is not None:
            self._update_pause()
            return
        if self.result_menu is not None:
            self._update_result()
            return
        self.toast_f = max(0, self.toast_f - 1)
        if self.playback is not None:
            menu = self.ctx.read_menu()
            if menu.was_pressed("pause") or menu.was_pressed("back"):
                self._go_to_menu()
                return
        frames = self._read_frames()
        pauser = next((i for i, f in enumerate(frames) if f.was_pressed("pause")), None)
        if not self.demo and pauser is not None:
            self.paused_by = pauser
            self.pause_menu = Menu(self._pause_items())
            return
        if self.playback is None:
            self.replay.record((frames[0], frames[1]))
        events = self.rounds.step((frames[0], frames[1]))
        self.view.on_events(events, self.rounds.match)
        self.hud.on_events(events, self.rounds)
        self.view.update(self.rounds.match)
        self.hud.update(self.rounds)
        if self.rounds.phase == Phase.MATCH_OVER and self.rounds.phase_f >= RESULT_MENU_AFTER_F:
            if self.demo or self.playback is not None:
                if self.demo:
                    self._new_rounds()
            else:
                self.save_replay()
                self.result_menu = Menu(self._result_items())

    def _read_frames(self) -> list[InputFrame]:
        if self.playback is not None:
            # Watching a replay: the recorded inputs, and the recorded menu commands.
            step = self.playback_step
            for command in self.playback.commands.get(step, []):
                self.apply_command(command)
            if step >= len(self.playback.frames):
                return [NEUTRAL, NEUTRAL]
            self.playback_step += 1
            return list(self.playback.frames[step])
        match = self.rounds.match
        frames = []
        mouse = self._mouse_cursor()
        players = self.ctx.controls.active_preset.players
        mouse_player = next((i for i, p in enumerate(players) if p.device == "keyboard"), 0)
        for i, source in enumerate(self.sources):
            frame = source.read(self.ctx.inputs)
            if i == mouse_player and mouse is not None:
                frame = replace(frame, cursor=mouse)
            bot = self.bots[i]
            if bot is not None:
                me = match.fighters[i]
                frame = bot.think(me, match.opponent(me))
            frames.append(frame)
        return frames

    def _mouse_cursor(self) -> tuple[float, float] | None:
        """Where the mouse points on the arena, if it is being used."""
        inputs = self.ctx.inputs
        if inputs.mouse_idle_f > MOUSE_AIM_F or pygame.display.get_surface() is None:
            return None
        x, y = self.ctx.display.window_to_internal(inputs.mouse_pos)
        width, height = self.ctx.display.internal_size
        if not (0 <= x < width and 0 <= y < height):
            return None  # outside the picture (black bars, another screen)
        return float(x), float(y)

    def _pause_items(self) -> list[MenuItem]:
        return [
            MenuItem("resume", text.RESUME),
            MenuItem("moves", text.MOVE_LIST),
            MenuItem("restart", text.RESTART),
            MenuItem("change", text.CHANGE_FIGHTERS),
            MenuItem("menu", text.MAIN_MENU),
        ]

    def _update_pause(self) -> None:
        frame = self.ctx.read_menu()
        action = self.pause_menu.handle(frame)
        if action in (("confirm", "resume"), ("back", "")) or frame.was_pressed("pause"):
            self.pause_menu = None
        elif action is not None:
            self._pause_action(*action)

    def _pause_action(self, kind: str, key: str) -> None:
        if kind != "confirm":
            return
        if key == "moves":
            self._open_move_list(self.paused_by)
        elif key == "restart":
            self._new_rounds()
        elif key == "change":
            self._change_fighters()
        elif key == "menu":
            self._go_to_menu()

    def _result_items(self) -> list[MenuItem]:
        """The menu after the last round (variants of the fight change it)."""
        return [
            MenuItem("rematch", text.REMATCH),
            MenuItem("change", text.CHANGE_FIGHTERS),
            MenuItem("menu", text.MAIN_MENU),
        ]

    def _update_result(self) -> None:
        action = self.result_menu.handle(self.ctx.read_menu())
        if action == ("confirm", "rematch"):
            self._new_rounds()
        elif action == ("confirm", "change"):
            self._change_fighters()
        elif action == ("confirm", "menu"):
            self._go_to_menu()

    def _open_move_list(self, index: int) -> None:
        player = self.ctx.controls.active_preset.players[index]
        self.move_list = MoveListPanel(
            self.fighter_defs[index],
            player,
            self.rules,
            text.PLAYER_N.format(n=index + 1),
            self.ctx.inputs,
        )

    def _change_fighters(self) -> None:
        from jojo_arena.ui.select_scene import CharacterSelectScene

        self.save_replay()
        self.ctx.scenes.switch(
            CharacterSelectScene(self.ctx, self.mode, cursor=self.fighter_ids[0])
        )

    def _go_to_menu(self) -> None:
        from jojo_arena.ui.main_menu import MainMenuScene

        self.save_replay()
        self.ctx.scenes.switch(MainMenuScene(self.ctx, cursor=self.mode))

    # Draw -------------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        self.view.draw(surface, self.rounds.match)
        menus_open = self.pause_menu is not None or self.move_list is not None
        self.hud.draw(surface, self.rounds, announcements=not menus_open)
        if not menus_open and self.rounds.match.cutscene is None:
            self.draw_overlay(surface)
            if self.playback is not None:
                over = self.playback_step >= len(self.playback.frames)
                label = text.REPLAY_OVER if over else text.REPLAY
                font.draw(surface, label, (surface.get_width() // 2, 38), GOLD, align="center")
        draw_toast(surface, text.REPLAY_SAVED, self.toast_f, y=60)
        center = surface.get_width() // 2
        if self.pause_menu is not None:
            surface.blit(veil(surface.get_size(), (10, 8, 24, 160)), (0, 0))
            items = len(self.pause_menu.items)
            box = pygame.Rect(0, 0, 230, 46 + items * 15)
            box.center = (center, surface.get_height() // 2)
            draw_box(surface, box)
            font.draw(surface, text.PAUSE, (center, box.y + 8), GOLD, scale=2, align="center")
            self.pause_menu.draw(surface, center, box.y + 36, spacing=15)
        elif self.result_menu is not None:
            box = pygame.Rect(0, 0, 200, 56)
            box.midtop = (center, 160)
            draw_box(surface, box)
            self.result_menu.draw(surface, center, box.y + 9, spacing=15)
        if self.move_list is not None:
            self.move_list.draw(surface)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        """Extra layer over the HUD, for fight variants (training)."""
