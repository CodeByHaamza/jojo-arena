"""Arena select: after the fighters are picked, where the fight happens.

One arena at a time, shown at half size so the pixels stay honest - the preview is the
real stage, drawn by its own renderer, not a picture of it. Left and right walk through
them, and the last entry draws one at random. Down reaches the arena's options: whether
the sun comes up, and whether its events (a chandelier, spikes) are on.
"""

from __future__ import annotations

import random

import pygame

from jojo_arena.characters import get_fighter, load_parts
from jojo_arena.context import GameContext
from jojo_arena.engine import audio, font, music
from jojo_arena.engine.scene import Scene
from jojo_arena.engine.sprites import shade
from jojo_arena.stages import STAGE_IDS, load_stage, stage_for_part, stage_renderer
from jojo_arena.stages.base import SUN_MODES, StageOptions
from jojo_arena.ui import text
from jojo_arena.ui.backdrop import MenuBackdrop
from jojo_arena.ui.icons import draw_icon
from jojo_arena.ui.labels import menu_key
from jojo_arena.ui.widgets import DIM, FAINT, GOLD, WHITE, draw_hints

PREVIEW = (240, 135)  # exactly half the game's resolution: no blurry rescale
PREVIEW_POS = (120, 32)
RANDOM = "random"  # the extra entry after the real arenas
MODES = ("training", "versus", "vs_cpu")
ROWS = ("arena", "sun", "events")  # what up and down move between
OPTIONS_Y = 222


def stage_thumbnail(stage_id: str, size: tuple[int, int] = PREVIEW) -> pygame.Surface:
    """The arena as it really looks, empty, scaled down with no smoothing."""
    stage = load_stage(stage_id)
    renderer = stage_renderer(stage)
    full = pygame.Surface((480, 270))
    arena = stage.build_arena()
    renderer.draw_background(full)
    renderer.draw_floor_details(full, arena)
    for obstacle in sorted(arena.obstacles, key=renderer.stage_index):
        renderer.draw_obstacle(full, obstacle)
    renderer.draw_lights(full, 0)
    return pygame.transform.scale(full, size)


class StageSelectScene(Scene):
    def __init__(
        self,
        ctx: GameContext,
        mode: str = "versus",
        fighter_ids: tuple[str, str] = ("jotaro_p3", "kakyoin"),
        cursor: str | None = None,
        options: StageOptions | None = None,
    ) -> None:
        super().__init__()
        music.request("menu")
        options = options or StageOptions()
        self.sun = options.sun
        self.events = options.events
        self.row = 0
        if mode not in MODES:
            raise ValueError(f"unknown mode '{mode}'")
        self.ctx = ctx
        self.mode = mode
        self.fighter_ids = fighter_ids
        self.defs = [get_fighter(i) for i in fighter_ids]
        self.parts = {p.number: p for p in load_parts()}
        self.choices: list[str] = [*STAGE_IDS, RANDOM]
        self.stages = {s: load_stage(s) for s in STAGE_IDS}
        self.thumbs = {s: stage_thumbnail(s) for s in STAGE_IDS}
        # Start on the arena of player 1's part: their home ground.
        home = cursor if cursor in self.choices else stage_for_part(self.defs[0].part)
        self.index = self.choices.index(home)
        self.backdrop = MenuBackdrop(part=self.defs[0].part)
        self.tick = 0
        self.hints = [
            (menu_key("confirm", ctx.inputs), text.HINT_CONFIRM),
            (f"{menu_key('up', ctx.inputs)} {menu_key('down', ctx.inputs)}", text.HINT_OPTION),
            (menu_key("back", ctx.inputs), text.HINT_BACK),
        ]

    @property
    def options(self) -> StageOptions:
        return StageOptions(sun=self.sun, events=self.events)

    @property
    def choice(self) -> str:
        return self.choices[self.index]

    @property
    def stage_id(self) -> str:
        """The arena picked, or one drawn at random when that entry is chosen."""
        return random.choice(STAGE_IDS) if self.choice == RANDOM else self.choice

    # Update -----------------------------------------------------------------------------

    def update(self) -> None:
        self.tick += 1
        frame = self.ctx.read_menu()
        rows = frame.presses("down") - frame.presses("up")
        if rows:
            self.row = (self.row + rows) % len(ROWS)
            audio.play("menu_move")
        step = frame.presses("right") - frame.presses("left")
        if step and ROWS[self.row] == "arena":
            self.index = (self.index + step) % len(self.choices)
            audio.play("menu_move")
            stage = self.stages.get(self.choice)
            self.backdrop.part = stage.part if stage else self.defs[0].part
        elif step and ROWS[self.row] == "sun":
            self.sun = SUN_MODES[(SUN_MODES.index(self.sun) + step) % len(SUN_MODES)]
            audio.play("menu_move")
        elif step and ROWS[self.row] == "events":
            self.events = not self.events
            audio.play("menu_move")
        if frame.was_pressed("confirm"):
            audio.play("menu_ok")
            self._go()
        elif frame.was_pressed("back"):
            from jojo_arena.ui.select_scene import CharacterSelectScene

            p1 = self.fighter_ids[0]
            self.ctx.scenes.switch(
                CharacterSelectScene(self.ctx, self.mode, picks=(p1,), cursor=self.fighter_ids[1])
            )

    def _go(self) -> None:
        stage_id = self.stage_id
        if self.mode == "training":
            from jojo_arena.ui.training_scene import TrainingScene

            scene = TrainingScene(
                self.ctx,
                fighter_ids=self.fighter_ids,
                stage_id=stage_id,
                stage_options=self.options,
            )
        else:
            from jojo_arena.ui.setup_scene import SetupScene

            scene = SetupScene(
                self.ctx,
                fighter_ids=self.fighter_ids,
                stage_id=stage_id,
                cpu=self.mode == "vs_cpu",
                stage_options=self.options,
            )
        self.ctx.scenes.switch(scene)

    # Draw -------------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface, self.tick)
        width, height = surface.get_size()
        center = width // 2
        font.draw(surface, text.PICK_STAGE, (center, 8), GOLD, scale=2, align="center")
        self._draw_preview(surface)
        self._draw_arrows(surface, center)
        self._draw_name(surface, center)
        self._draw_dots(surface, center)
        self._draw_options(surface, center)
        draw_hints(surface, self.hints, (center, height - 14))

    def _draw_preview(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(PREVIEW_POS, PREVIEW)
        pygame.draw.rect(surface, (14, 11, 26), rect.inflate(6, 6))
        if self.choice == RANDOM:
            # Every arena in turn, so you can see what you are gambling on.
            turning = STAGE_IDS[(self.tick // 45) % len(STAGE_IDS)]
            surface.blit(self.thumbs[turning], rect)
            veil = pygame.Surface(PREVIEW, pygame.SRCALPHA)
            veil.fill((10, 8, 24, 170))
            surface.blit(veil, rect)
            font.draw(surface, "?", rect.center, GOLD, scale=4, align="center")
        else:
            surface.blit(self.thumbs[self.choice], rect)
        pygame.draw.rect(surface, GOLD, rect.inflate(2, 2), 1)

    def _draw_arrows(self, surface: pygame.Surface, center: int) -> None:
        blink = (self.tick // 15) % 2 == 0
        color = GOLD if blink else DIM
        y = PREVIEW_POS[1] + PREVIEW[1] // 2 - 4
        font.draw(surface, "<", (PREVIEW_POS[0] - 14, y), color, scale=2, align="center")
        font.draw(
            surface, ">", (PREVIEW_POS[0] + PREVIEW[0] + 14, y), color, scale=2, align="center"
        )

    def _draw_name(self, surface: pygame.Surface, center: int) -> None:
        y = PREVIEW_POS[1] + PREVIEW[1] + 10
        if self.choice == RANDOM:
            font.draw(surface, text.STAGE_RANDOM, (center, y), WHITE, scale=2, align="center")
            font.draw(surface, text.STAGE_RANDOM_INFO, (center, y + 20), FAINT, align="center")
            return
        stage = self.stages[self.choice]
        font.draw(surface, stage.name.upper(), (center, y), WHITE, scale=2, align="center")
        part = self.parts.get(stage.part)
        if part is None:
            return
        line = f"{text.PART_SHORT.format(n=part.number)} - {part.title}"
        rect = font.draw(
            surface, line, (center + 6, y + 20), shade(part.colors[0], 60), align="center"
        )
        draw_icon(surface, part.emblem, (rect.x - 13, rect.y - 2))

    def _draw_options(self, surface: pygame.Surface, center: int) -> None:
        """The two settings of the arena under it, the one being changed highlighted.
        An arena without sun or without events says so instead of offering a choice
        that would change nothing."""
        stage = self.stages.get(self.choice)
        has_sun = stage is None or stage.has_sun
        has_events = stage is None or stage.has_events
        lines = (
            (
                "sun",
                text.STAGE_SUN,
                text.SUN_MODES[SUN_MODES.index(self.sun)],
                has_sun,
                text.STAGE_NO_SUN,
            ),
            (
                "events",
                text.STAGE_EVENTS,
                text.YES if self.events else text.NO,
                has_events,
                text.STAGE_NO_EVENTS,
            ),
        )
        for i, (row, label, value, available, missing) in enumerate(lines):
            y = OPTIONS_Y + i * 11
            here = ROWS[self.row] == row
            if not available:
                font.draw(surface, f"{label} : {missing}", (center, y), FAINT, align="center")
                continue
            color = GOLD if here else WHITE
            line = f"< {label} : {value} >" if here else f"{label} : {value}"
            font.draw(surface, line, (center, y), color, align="center")

    def _draw_dots(self, surface: pygame.Surface, center: int) -> None:
        """One mark per arena, so the number of them is readable at a glance."""
        y = PREVIEW_POS[1] + PREVIEW[1] + 44
        span = len(self.choices) * 8 - 3
        x = center - span // 2
        for i in range(len(self.choices)):
            here = i == self.index
            surface.fill(GOLD if here else (70, 64, 92), (x + i * 8, y, 5, 5 if here else 3))
