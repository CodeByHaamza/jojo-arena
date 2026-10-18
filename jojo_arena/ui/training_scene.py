"""Training mode: the fight screen with no clock, refills, a dummy and a combo counter.

The pause menu holds the training settings: what the dummy does, infinite life and
Heart Heat, putting both fighters back in place. Its "dummy settings" page goes further:
the dummy repeats one chosen move, with the delay of your choice between each try, and
the frame meter shows what both sides were doing frame by frame.
"""

from __future__ import annotations

import pygame

from jojo_arena.combat.dummy import DELAYS, After, Dummy, DummyAction, DummyPlayer, dummy_actions
from jojo_arena.combat.framedata import frame_data, signed
from jojo_arena.combat.framemeter import Band, FrameMeter
from jojo_arena.combat.kit import MoveDef
from jojo_arena.combat.replay import Replay
from jojo_arena.combat.training import Training
from jojo_arena.context import GameContext
from jojo_arena.engine import font
from jojo_arena.engine.actions import InputFrame, merge_frames
from jojo_arena.stages.base import StageOptions
from jojo_arena.ui import text
from jojo_arena.ui.fight_scene import FightScene
from jojo_arena.ui.frame_meter import COLORS, FrameMeterPanel, draw_legend
from jojo_arena.ui.input_display import ACTIONS, InputDisplay
from jojo_arena.ui.labels import action_label, move_label
from jojo_arena.ui.menu import Menu, MenuItem
from jojo_arena.ui.widgets import DIM, FAINT, GOLD, WHITE

DUMMY_LABELS = {  # names in ui/text.py
    Dummy.STAND: "DUMMY_STAND",
    Dummy.GUARD: "DUMMY_GUARD",
    Dummy.PLAYER: "DUMMY_PLAYER",
    Dummy.ACTION: "DUMMY_ACTION_MODE",
    Dummy.RECORD: "DUMMY_RECORDING",
    Dummy.PLAYBACK: "DUMMY_PLAYBACK_MODE",
}
# The training panel fills the band between the input display and the bottom gauges.
LEGEND_Y = 219
DATA_X, DATA_Y = 20, 229  # frame data of the last move each side played
METER_X, METER_Y = 220, 230  # the strips, to the right of it
METER_COLUMNS = 230  # just under four seconds of fight
RECORDING_COLOR = (236, 96, 96)


def action_name(action: DummyAction) -> str:
    """A move's own name, or the name of a built-in action in the current language."""
    return action.label or getattr(text, action.text_key)


def delay_name(frames: int) -> str:
    return text.DUMMY_DELAY_NOW if frames == 0 else text.DUMMY_DELAY_VALUE.format(n=frames)


# How long stopped time lasts in the training room, as a share of the move's own
# length. A real fight always uses 100 %.
STOP_LENGTHS = (0.25, 0.5, 1.0, 1.5, 2.0)


class TrainingScene(FightScene):
    mode = "training"

    def __init__(
        self,
        ctx: GameContext,
        fighter_ids: tuple[str, str] = ("jotaro_p3", "dio_p3"),
        stage_id: str = "cairo_night",
        stage_options: StageOptions | None = None,
    ) -> None:
        super().__init__(
            ctx,
            rounds_to_win=0,
            fighter_ids=fighter_ids,
            stage_id=stage_id,
            stage_options=stage_options,
        )
        player = ctx.controls.active_preset.players[0]
        self.pause_key = action_label(player, "pause", ctx.inputs)
        self.hint = text.TRAINING_HINT.format(key=self.pause_key)
        self.inputs_shown = True
        self.frames_shown = True
        self.meter_shown = True
        self.pause_page = "main"
        self.last_moves: list[MoveDef | None] = [None, None]  # for the frame data panel
        self._serials = [-1, -1]
        # One display per player: while recording, the dummy is played by the second
        # one, so the keys shown are that player's own, named for that player's device.
        self.input_displays = [
            InputDisplay({a: action_label(who, a, ctx.inputs) for a in ACTIONS})
            for who in ctx.controls.active_preset.players
        ]
        self.meter_panel = FrameMeterPanel((text.P1, text.P2), METER_COLUMNS)
        self.dummy.load_json(ctx.settings.training)  # the setup from last time
        # Watching a move frame by frame: F6 speed, F7 freeze, F8 one step.
        self.speed_div = 1
        self.frozen = False
        self.single_step = False
        self.slow_f = 0

    @property
    def training(self) -> Training:
        return self.rounds

    @property
    def watched(self) -> int:
        """The player whose keys are shown: whoever is playing the dummy right now."""
        return 1 if self.dummy.recording_now else 0

    def action_keys(self, action: DummyAction) -> str:
        """The buttons player 2 would press for this action, named for their device.

        A move that lives in the other stance needs the style button first, and a
        variant needs a direction held: both are spelled out with the real keys.
        """
        if not action.press:
            return ""
        who = self.ctx.controls.active_preset.players[1]
        inputs = self.ctx.inputs
        press = action_label(who, action.press, inputs)
        if action.direction:
            press = f"{move_label(who)} + {press}"
        if action.stance and action.stance != self.fighter_defs[1].kit.base_stance_name:
            stand = action_label(who, "stand", inputs)
            return f"{stand} {text.DUMMY_THEN} {press}"
        return press

    @property
    def pause_title(self) -> str:
        return text.DUMMY_SETTINGS if self.pause_page == "dummy" else text.PAUSE

    @property
    def pause_width(self) -> int:
        return 330 if self.pause_page == "dummy" else 230

    def _new_rounds(self) -> None:
        kits = (self.fighter_defs[0].kit, self.fighter_defs[1].kit)
        self.rounds = Training(kits, self.rules, self.build_arena)
        self.pause_menu = None
        self.result_menu = None
        self.pause_page = "main"
        self.replay = Replay(self.replay_meta())
        self.meter = FrameMeter()
        actions = dummy_actions(kits[1])
        if hasattr(self, "dummy"):
            self.dummy.retarget(actions)  # same settings, the other character's moves
        else:
            self.dummy = DummyPlayer(actions)

    # Update -----------------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_F6:
            self.speed_div = {1: 2, 2: 4, 4: 1}[self.speed_div]
        elif event.key == pygame.K_F7:
            self.frozen = not self.frozen
        elif event.key == pygame.K_F8:
            self.frozen, self.single_step = True, True

    def update(self) -> None:
        if self.dummy.recording_now and self.pause_menu is None and self.move_list is None:
            # While recording, the pause key ends the recording instead of pausing.
            menu = self.ctx.read_menu()
            if menu.was_pressed("pause") or menu.was_pressed("back"):
                self.dummy.stop_recording()
                return
        if self.pause_menu is not None or self.move_list is not None:
            super().update()
            return
        if self.frozen and not self.single_step:
            # The world holds still; the pause key still answers.
            if self.ctx.read_menu().was_pressed("pause"):
                self.pause_menu = Menu(self._pause_items())
            return
        self.slow_f += 1
        if not self.single_step and self.slow_f % self.speed_div:
            return  # slow motion: this frame is drawn, but the world does not move
        self.single_step = False
        super().update()

    def on_step(self, events: list) -> None:
        self.meter.update(self.rounds.match, events)

    def _read_frames(self) -> list[InputFrame]:
        frames = super()._read_frames()
        if self.playback is not None:
            return frames  # recorded as they were played, dummy included
        match = self.rounds.match
        dummy = self.dummy.think(match.fighters[1], match.fighters[0])
        if dummy is not None:
            # Alone at training: player 1 can use any device, keyboard or pad.
            frames = [merge_frames(*frames), dummy]
        elif self.dummy.recording_now:
            self.dummy.record(frames[1])
        self.input_displays[self.watched].update(frames[self.watched])
        for index, fighter in enumerate(match.fighters):
            attack = fighter.attack
            if attack is not None and attack.serial != self._serials[index]:
                self._serials[index] = attack.serial
                self.last_moves[index] = attack.move
        return frames

    def _go_to_menu(self) -> None:
        """Leaving the room: the dummy's setup is kept for next time."""
        self.ctx.settings.training = self.dummy.to_json()
        self.ctx.save_settings()
        super()._go_to_menu()

    def apply_command(self, command: dict) -> None:
        if "time_stop" in command:
            self.training.time_stop_mult = command["time_stop"]
        if "life" in command:
            self.training.infinite_life = command["life"]
        if "hh" in command:
            self.training.infinite_hh = command["hh"]
        if command.get("reset"):
            self._reset_positions()
        self.training.apply_options()

    def _reset_positions(self) -> None:
        self.training.reset()
        self.dummy.reset()
        self.meter.reset()

    # The pause menu ---------------------------------------------------------------------

    def _dummy_modes(self) -> list[Dummy]:
        modes = [Dummy.STAND, Dummy.GUARD, Dummy.PLAYER, Dummy.ACTION]
        if self.dummy.recorded:
            modes.append(Dummy.PLAYBACK)
        return modes

    def _pause_items(self) -> list[MenuItem]:
        modes = self._dummy_modes()
        mode = self.dummy.plan.mode
        switch = [text.INFINITE, text.NORMAL]
        show = [text.SHOWN, text.HIDDEN]
        return [
            MenuItem("resume", text.RESUME),
            MenuItem("moves", text.MOVE_LIST),
            MenuItem(
                "dummy",
                text.DUMMY_MODE,
                [getattr(text, DUMMY_LABELS[m]) for m in modes],
                modes.index(mode) if mode in modes else 0,
            ),
            MenuItem("dummy_setup", text.DUMMY_SETTINGS),
            MenuItem("life", text.LIFE, switch, 0 if self.training.infinite_life else 1),
            MenuItem("hh", text.HH_GAUGE, switch, 0 if self.training.infinite_hh else 1),
            MenuItem(
                "time_stop",
                text.TIME_STOP_LENGTH,
                [f"{int(m * 100)} %" for m in STOP_LENGTHS],
                STOP_LENGTHS.index(self.training.time_stop_mult)
                if self.training.time_stop_mult in STOP_LENGTHS
                else STOP_LENGTHS.index(1.0),
            ),
            MenuItem("inputs", text.INPUTS, show, 0 if self.inputs_shown else 1),
            MenuItem("frames", text.FRAMES, show, 0 if self.frames_shown else 1),
            MenuItem("reset", text.RESET_POSITIONS),
            MenuItem("change", text.CHANGE_FIGHTERS),
            MenuItem("menu", text.MAIN_MENU),
        ]

    def _dummy_items(self) -> list[MenuItem]:
        plan = self.dummy.plan
        yes_no = [text.YES, text.NO]
        after = list(After)
        return [
            MenuItem(
                "action",
                text.DUMMY_ACTION,
                [action_name(a) for a in self.dummy.actions],
                plan.action,
            ),
            MenuItem("delay", text.DUMMY_DELAY, [delay_name(d) for d in DELAYS], self._delay_index),
            MenuItem("chain", text.DUMMY_CHAIN, yes_no, 0 if plan.chain else 1),
            MenuItem("approach", text.DUMMY_APPROACH, yes_no, 0 if plan.approach else 1),
            MenuItem(
                "after",
                text.DUMMY_AFTER,
                [text.DUMMY_AFTER_IDLE, text.DUMMY_AFTER_GUARD],
                after.index(plan.after),
            ),
            MenuItem("record", text.DUMMY_RECORD),
            MenuItem("meter", text.METER, [text.SHOWN, text.HIDDEN], 0 if self.meter_shown else 1),
            MenuItem("back", text.BACK),
        ]

    @property
    def _delay_index(self) -> int:
        delay = self.dummy.plan.delay_f
        return DELAYS.index(delay) if delay in DELAYS else 0

    def _update_pause(self) -> None:
        if self.pause_page != "dummy":
            super()._update_pause()
            return
        frame = self.ctx.read_menu()
        action = self.pause_menu.handle(frame)
        if action in (("confirm", "back"), ("back", "")) or frame.was_pressed("pause"):
            # One step back: the settings page is a page of the pause menu, not a mode.
            self.pause_page = "main"
            self.pause_menu = Menu(self._pause_items())
            self.pause_menu.select("dummy_setup")
            return
        if action is not None:
            self._dummy_setting(*action)

    def _pause_action(self, kind: str, key: str) -> None:
        menu = self.pause_menu
        if kind == "change":
            index = menu.item(key).index
            if key == "dummy":
                self.dummy.plan.mode = self._dummy_modes()[index]
            elif key == "life":
                self.training.infinite_life = index == 0
                self.replay.command({"life": index == 0})
            elif key == "hh":
                self.training.infinite_hh = index == 0
                self.replay.command({"hh": index == 0})
            elif key == "inputs":
                self.inputs_shown = index == 0
            elif key == "frames":
                self.frames_shown = index == 0
            elif key == "time_stop":
                # How many frames ZA WARUDO gives you, for working a combo inside it.
                self.training.time_stop_mult = STOP_LENGTHS[index]
                self.replay.command({"time_stop": STOP_LENGTHS[index]})
            self.training.apply_options()
        elif (kind, key) == ("confirm", "dummy_setup"):
            self.pause_page = "dummy"
            self.pause_menu = Menu(self._dummy_items())
        elif (kind, key) == ("confirm", "reset"):
            self._reset_positions()
            self.replay.command({"reset": True})
            self.pause_menu = None
        else:
            super()._pause_action(kind, key)

    def _dummy_setting(self, kind: str, key: str) -> None:
        plan = self.dummy.plan
        if kind == "change":
            index = self.pause_menu.item(key).index
            if key == "action":
                plan.action = index
                # Choosing a move is asking for it: the dummy switches to playing it.
                if self.dummy.action.press and plan.mode != Dummy.ACTION:
                    plan.mode = Dummy.ACTION
            elif key == "delay":
                plan.delay_f = DELAYS[index]
            elif key == "chain":
                plan.chain = index == 0
            elif key == "approach":
                plan.approach = index == 0
            elif key == "after":
                plan.after = list(After)[index]
            elif key == "meter":
                self.meter_shown = index == 0
            self.dummy.reset()
        elif (kind, key) == ("confirm", "record"):
            self.dummy.start_recording()
            self.pause_menu, self.pause_page = None, "main"

    # Draw -------------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        if self.pause_menu is not None and self.pause_page == "dummy":
            self._draw_action_data(surface)

    def _draw_action_data(self, surface: pygame.Surface) -> None:
        """Under the settings box: the frames of the action the dummy is set to play."""
        move = self.dummy.action.move
        center = surface.get_width() // 2
        if move is None:
            font.draw(surface, text.DUMMY_NEEDS_ACTION, (center, 226), FAINT, align="center")
            return
        data = frame_data(move, self.rules)
        line = text.FRAME_DATA.format(
            name=move.label or move.name.upper(),
            startup=data.startup,
            active=data.active,
            recovery=data.recovery,
            hit=signed(data.on_hit),
            block=signed(data.on_block),
        )
        font.draw(surface, line, (center, 226), DIM, align="center")
        keys = self.action_keys(self.dummy.action)
        if keys:
            # What the second player would press to do it by hand, on their own device.
            line = text.DUMMY_KEYS.format(player=text.P2, keys=keys)
            font.draw(surface, line, (center, 236), FAINT, align="center")

    def draw_overlay(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        font.draw(surface, text.TRAINING, (width // 2, 22), GOLD, align="center")
        self._draw_dummy_line(surface, width)
        for attacker, combo in enumerate(self.training.combos):
            if not combo.visible:
                continue
            x, align = (26, "left") if attacker == 0 else (width - 26, "right")
            color = GOLD if combo.live else DIM
            hits = text.COMBO_HITS.format(n=combo.hits)
            font.draw(surface, hits, (x, 44), color, scale=2, align=align)
            damage = text.COMBO_DAMAGE.format(n=combo.damage)
            font.draw(surface, damage, (x, 64), WHITE if combo.live else DIM, align=align)
        if self.frozen or self.speed_div > 1:
            # Under the title, in the middle: the combo counters sit at the edges.
            label = (
                text.TRAIN_FROZEN
                if self.frozen
                else text.TRAIN_SPEED.format(pct=100 // self.speed_div)
            )
            font.draw(surface, label, (width // 2, 46), GOLD, align="center")
        font.draw(surface, self.hint, (width // 2, height - 12), FAINT, align="center")
        if self.inputs_shown:
            tag = (text.P1, text.P2)[self.watched]
            left = font.draw(surface, tag, (20, 205), GOLD if self.watched else DIM).right
            self.input_displays[self.watched].draw(surface, left + 4, 204)
        if self.frames_shown:
            draw_legend(surface, DATA_X, LEGEND_Y)
            self._draw_frame_data(surface)
        if self.meter_shown:
            self.meter_panel.draw(surface, self.meter, METER_X, METER_Y)
            right = METER_X + METER_COLUMNS
            self.meter_panel.draw_advantage(surface, self.meter, right, LEGEND_Y)

    def _draw_dummy_line(self, surface: pygame.Surface, width: int) -> None:
        """Top right: what the dummy is set to do, and the action it repeats."""
        plan = self.dummy.plan
        if self.dummy.recording_now:
            font.draw(
                surface, text.DUMMY_RECORDING, (width // 2, 36), RECORDING_COLOR, align="center"
            )
            hint = text.DUMMY_RECORD_HINT.format(key=self.pause_key)
            font.draw(surface, hint, (width // 2, 46), DIM, align="center")
            return
        mode = f"{text.DUMMY_MODE} : {getattr(text, DUMMY_LABELS[plan.mode])}"
        font.draw(surface, mode, (width - 26, 31), DIM, align="right")
        if plan.mode == Dummy.ACTION:
            name = action_name(self.dummy.action)
            line = f"{name}   {delay_name(plan.delay_f)}"
            font.draw(surface, line, (width - 26, 41), GOLD, align="right")

    def _draw_frame_data(self, surface: pygame.Surface) -> None:
        """The last move each side played, as players write it: name, 4/3/10, +6/-2."""
        for index, move in enumerate(self.last_moves):
            if move is None:
                continue
            data = frame_data(move, self.rules)
            y = DATA_Y + index * 10
            name = f"{(text.P1, text.P2)[index]}  {move.label or move.name.upper()}"
            cursor = font.draw(surface, name, (DATA_X, y), WHITE if index == 0 else DIM).right + 6
            phases = ((data.startup, Band.STARTUP), (data.active, Band.ACTIVE))
            for value, band in (*phases, (data.recovery, Band.RECOVERY)):
                cursor = font.draw(surface, str(value), (cursor, y), COLORS[band]).right
                if band != Band.RECOVERY:
                    cursor = font.draw(surface, "/", (cursor, y), FAINT).right
            cursor += 6
            cursor = font.draw(surface, signed(data.on_hit), (cursor, y), DIM).right
            cursor = font.draw(surface, "/", (cursor, y), FAINT).right
            font.draw(surface, signed(data.on_block), (cursor, y), DIM)
