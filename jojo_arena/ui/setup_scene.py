"""VS screen before a local fight: both fighters face off in the poses they picked and say
what the games give that pair to say; rounds to win and controls."""

from __future__ import annotations

import pygame

from jojo_arena.characters import get_fighter
from jojo_arena.characters.lines import exchange_for
from jojo_arena.combat.rounds import ROUNDS_TO_WIN_CHOICES
from jojo_arena.context import GameContext
from jojo_arena.engine import font, music
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import shade
from jojo_arena.stages import load_stage, stage_for_part
from jojo_arena.stages.base import StageOptions
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.labels import menu_key, preset_label
from jojo_arena.ui.loadout import resolve_loadout
from jojo_arena.ui.menu import Menu, MenuItem
from jojo_arena.ui.portraits import FighterLook
from jojo_arena.ui.widgets import DIM, GOLD, P1_COLOR, P2_COLOR, draw_box, draw_hints

WARNING = (240, 90, 90)
DEFAULT_ROUNDS_TO_WIN = 3
DEFAULT_FIGHTERS = ("jotaro_p3", "kakyoin")
FEET_Y = 178
FEET_X = (78, 402)
# The exchange: each line is typed out on its speaker's side, stays, then the next one.
LINES_Y = 208
LINE_W = 300  # px a line may take before it wraps (two rows at most)
LINE_F = 170  # frames one line stays up
LINE_PAUSE_F = 30  # a breath between two lines
LOOP_PAUSE_F = 150  # ...and a longer one before the pair starts over
TYPE_PER_F = 2  # letters typed each frame


class SetupScene(Scene):
    def __init__(
        self,
        ctx: GameContext,
        fighter_ids: tuple[str, str] = DEFAULT_FIGHTERS,
        rounds_to_win: int = DEFAULT_ROUNDS_TO_WIN,
        cpu: bool = False,
        stage_id: str | None = None,
        stage_options: StageOptions | None = None,
    ) -> None:
        super().__init__()
        music.request("menu")
        self.ctx = ctx
        self.fighter_ids = fighter_ids
        self.cpu = cpu
        self.defs = [get_fighter(i) for i in fighter_ids]
        self.looks = [FighterLook(f) for f in self.defs]
        # The poses picked on the select screen (a sheet's first ones for the computer).
        self.loadouts = [
            resolve_loadout(look.sprites, loadout)
            for look, loadout in zip(self.looks, ctx.loadouts, strict=False)
        ]
        # What the games give these two to say to each other (None: nothing).
        self.exchange = exchange_for(*fighter_ids)
        self.backdrop = MenuBackdrop()
        self.preset_keys = list(ctx.controls.presets)
        rounds = [str(n) for n in ROUNDS_TO_WIN_CHOICES]
        labels = [preset_label(ctx.controls.presets[k]) for k in self.preset_keys]
        # The arena was picked on the screen before; this one only says which it is.
        self.stage_id = stage_id or stage_for_part(self.defs[0].part)
        self.stage = load_stage(self.stage_id)
        self.stage_options = stage_options or StageOptions()
        self.menu = Menu(
            [
                MenuItem("rounds", text.ROUNDS_TO_WIN, rounds, rounds.index(str(rounds_to_win))),
                *(
                    [MenuItem("level", text.DIFFICULTY, text.LEVEL_NAMES, ctx.settings.cpu_level)]
                    if cpu
                    else []
                ),
                MenuItem(
                    "controls", text.CONTROLS, labels, self.preset_keys.index(ctx.controls.active)
                ),
                MenuItem("fight", text.FIGHT),
                MenuItem("back", text.BACK),
            ]
        )
        self.menu.select("fight")
        self.tick = 0
        self.hints = [
            (menu_key("confirm", ctx.inputs), text.HINT_CONFIRM),
            (menu_key("back", ctx.inputs), text.HINT_BACK),
        ]

    @property
    def rounds_to_win(self) -> int:
        return int(self.menu.item("rounds").value)

    def pose_of(self, side: int) -> tuple[str, bool, tuple[float, float] | None]:
        """(animation, Stand shown, where the Stand stands) for this side: the pose picked
        with the Stand when there is one, else the pose picked alone, else standing."""
        look, loadout = self.looks[side], self.loadouts[side]
        if loadout.stand_pose and look.stand is not None:
            info = look.sprites.poses.get(loadout.stand_pose)
            return f"pose_{loadout.stand_pose}", True, info.stand_offset if info else None
        if loadout.pose:
            return f"pose_{loadout.pose}", False, None
        return "idle", True, None

    def spoken(self) -> tuple[int, str, int] | None:
        """(the side speaking, its line, how many letters are typed so far), by the clock;
        None between two lines, or when this pair has nothing to say."""
        intro = self.exchange.intro if self.exchange is not None else ()
        if not intro:
            return None
        slot = LINE_F + LINE_PAUSE_F
        index, at = divmod(self.tick % (slot * len(intro) + LOOP_PAUSE_F), slot)
        if index >= len(intro) or at >= LINE_F:
            return None
        who, line = intro[index]
        return self.fighter_ids.index(who), line, min(len(line), (at + 1) * TYPE_PER_F)

    def update(self) -> None:
        self.tick += 1
        action = self.menu.handle(self.ctx.read_menu())
        if action is None:
            return
        kind, key = action
        if kind == "change" and key == "level":
            self.ctx.settings.cpu_level = self.menu.item("level").index
            self.ctx.save_settings()
        if kind == "change" and key == "controls":
            self.ctx.controls.active = self.preset_keys[self.menu.item("controls").index]
            self.ctx.save_controls()
        elif kind == "confirm" and key == "fight":
            from jojo_arena.ui.fight_scene import FightScene

            self.ctx.scenes.switch(
                FightScene(
                    self.ctx,
                    rounds_to_win=self.rounds_to_win,
                    fighter_ids=self.fighter_ids,
                    stage_id=self.stage_id,
                    bots=(False, self.cpu),
                    cpu_level=self.ctx.settings.cpu_level,
                    stage_options=self.stage_options,
                )
            )
        elif (kind == "confirm" and key == "back") or kind == "back":
            # Back one step: the arena select, with this arena still under the cursor.
            from jojo_arena.ui.stage_scene import StageSelectScene

            mode = "vs_cpu" if self.cpu else "versus"
            self.ctx.scenes.switch(
                StageSelectScene(
                    self.ctx,
                    mode,
                    self.fighter_ids,
                    cursor=self.stage_id,
                    options=self.stage_options,
                )
            )

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        center = width // 2
        title = text.MENU_VS_CPU if self.cpu else text.SETUP_TITLE
        font.draw(surface, title, (center, 8), GOLD, scale=2, align="center")
        for side, (look, fdef) in enumerate(zip(self.looks, self.defs, strict=True)):
            x = FEET_X[side]
            anim, with_stand, offset = self.pose_of(side)
            look.draw(
                surface,
                (x, FEET_Y),
                self.tick,
                scale=2,
                flip=side == 1,
                stand=with_stand,
                anim=anim,
                stand_offset=offset,
            )
            color = P1_COLOR if side == 0 else P2_COLOR
            tag = text.CPU if self.cpu and side == 1 else text.PLAYER_N.format(n=side + 1)
            font.draw(surface, tag, (x, 40), color, scale=2, align="center")
            font.draw(surface, fdef.name, (x, FEET_Y + 8), shade(fdef.color, 60), align="center")
            if fdef.stand_name:
                font.draw(surface, fdef.stand_name, (x, FEET_Y + 19), fdef.aura, align="center")
        font.draw(surface, text.VS, (center, 50), GOLD, scale=4, align="center")
        box = pygame.Rect(0, 0, 262, 69 + (15 if self.cpu else 0))
        box.midtop = (center, 104)
        draw_box(surface, box)
        self.menu.draw(surface, center, box.y + 9, spacing=15)
        arena = f"{text.STAGE} : {self.stage.name.upper()}"
        font.draw(surface, arena, (center, box.bottom + 6), GOLD, align="center")
        self._draw_line(surface)
        preset = self.ctx.controls.active_preset
        if preset.pads_needed() > len(self.ctx.inputs.pads):
            font.draw(surface, text.PADS_MISSING, (center, 229), WARNING, align="center")
        font.draw(surface, text.CONTROLS_FILE_HINT, (center, 240), DIM, align="center")
        draw_hints(surface, self.hints, (center, height - 14))

    def _draw_line(self, surface: pygame.Surface) -> None:
        """The line being said, on its speaker's side and in its speaker's color."""
        said = self.spoken()
        if said is None:
            return
        side, line, typed = said
        color = shade(self.defs[side].color, 70)
        x = 14 if side == 0 else surface.get_width() - 14
        # Wrapped as the whole line will be, so the words do not jump while it is typed.
        for row, words in enumerate(font.wrap(line, LINE_W)):
            if typed <= 0:
                break
            align = "left" if side == 0 else "right"
            font.draw(surface, words[:typed], (x, LINES_Y + row * 10), color, align=align)
            typed -= len(words) + 1  # the space the wrap ate
