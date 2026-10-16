"""In-fight HUD: life, guard and Heart Heat gauges, timer, rounds, announcements."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from jojo_arena.characters import FighterDef
from jojo_arena.combat.events import Event
from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.combat.rounds import Phase, Rounds
from jojo_arena.engine import font
from jojo_arena.engine.geometry import Vec2
from jojo_arena.engine.sprites import shade
from jojo_arena.ui import text

OUTLINE = (23, 18, 31)
WHITE = (255, 255, 255)
LIFE = (240, 200, 70)
LIFE_LOW = (230, 60, 60)
TRAIL = (255, 245, 220)
GUARD = (110, 170, 255)
GOLD = (255, 214, 90)
SCREEN_W = 480

LIFE_W, LIFE_H, LIFE_Y = 180, 9, 6
GUARD_W, GUARD_Y = 120, 16
HH_SEGMENT_W, HH_Y = 34, 259
GO_F = 45  # how long "COMBATTEZ !" stays after the intro


@dataclass
class Callout:
    label: str
    color: tuple[int, int, int]
    pos: Vec2
    life: int = 50


class Hud:
    def __init__(self, fighter_defs: list[FighterDef], heights: list[int]) -> None:
        self.defs = fighter_defs
        self.heights = heights  # sprite height of each fighter, to place labels overhead
        self.shown_hp: list[float | None] = [None, None]
        self.callouts: list[Callout] = []
        self.tick = 0
        self._bands: dict[int, pygame.Surface] = {}
        self.mash_keys: tuple[str, str] = ("", "")  # each player's key to mash in a clash

    def on_events(self, events: list[Event], rounds: Rounds) -> None:
        labels = {
            "stylish": (text.STYLISH, GOLD),
            "guard_break": (text.GUARD_BREAK, WHITE),
            "flash_cancel": (text.FLASH_CANCEL, WHITE),
            "resolve": (text.RESOLVE, LIFE_LOW),
        }
        for event in events:
            if event.kind in labels and event.fighter is not None:
                label, color = labels[event.kind]
                fighter = rounds.match.fighters[event.fighter]
                above = Vec2(0, -(self.heights[event.fighter] + 14))
                self.callouts.append(Callout(label, color, fighter.pos + above))
            elif event.kind == "clash_start" and event.pos is not None:
                above = Vec2(0, -(max(self.heights) + 24))
                self.callouts.append(Callout(text.CLASH, WHITE, event.pos + above, 40))
            elif event.kind == "round_start":
                self.shown_hp = [None, None]

    def update(self, rounds: Rounds) -> None:
        self.tick += 1
        for callout in self.callouts:
            callout.life -= 1
            callout.pos = callout.pos + Vec2(0, -0.3)
        self.callouts = [c for c in self.callouts if c.life > 0]
        for i, fighter in enumerate(rounds.match.fighters):
            shown = self.shown_hp[i]
            if shown is None or shown < fighter.hp:
                self.shown_hp[i] = fighter.hp
            elif shown > fighter.hp:
                self.shown_hp[i] = max(fighter.hp, shown - 4)  # damage trail drains

    # Drawing ---------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, rounds: Rounds, announcements: bool = True) -> None:
        if rounds.match.cutscene is not None:
            return  # the cutscene has the whole screen
        for fighter in rounds.match.fighters:
            self._draw_player(surface, fighter, rounds)
        self._draw_timer(surface, rounds)
        if not announcements:
            return
        for callout in self.callouts:
            x, y = callout.pos.as_ints()
            font.draw(surface, callout.label, (x, y), callout.color, align="center")
        stop = rounds.match.time_stop
        if stop is not None and rounds.match.super_freeze == 0:
            font.draw(surface, text.TIME_STOPPED, (SCREEN_W // 2, 36), GOLD, align="center")
            width = round(80 * stop.frames_left / max(1, stop.duration_f))
            surface.fill(OUTLINE, (SCREEN_W // 2 - 41, 47, 82, 4))
            surface.fill(GOLD, (SCREEN_W // 2 - 40, 48, width, 2))
        if rounds.match.clash is not None:
            self._draw_mash(surface)
        self._draw_announcement(surface, rounds)

    def _draw_mash(self, surface: pygame.Surface) -> None:
        """The clash prompt under the duel bar: MASH!, with each player's key."""
        scale = 3 if (self.tick // 6) % 2 == 0 else 2
        y = 40 if scale == 2 else 36
        font.draw(surface, text.MASH, (SCREEN_W // 2, y), GOLD, scale=scale, align="center")
        for i, key in enumerate(self.mash_keys):
            if not key:
                continue
            width = font.text_width(key) + 8
            x = SCREEN_W // 2 - 110 - width if i == 0 else SCREEN_W // 2 + 110
            pressed = (self.tick // 3) % 2 == i
            y = 65 + (1 if pressed else 0)
            surface.fill(OUTLINE, (x - 1, y - 1, width + 2, 15))
            surface.fill((90, 80, 120) if pressed else (60, 52, 84), (x, y, width, 13))
            font.draw(surface, key, (x + 4, y + 2), WHITE, outline=None)

    def _mirror(self, index: int, x: int, width: int) -> int:
        """x of a box for player 1; the same box mirrored for player 2."""
        return x if index == 0 else SCREEN_W - x - width

    def _draw_player(self, surface: pygame.Surface, fighter: Fighter, rounds: Rounds) -> None:
        i = fighter.index
        fdef = self.defs[i]
        # Placeholder portrait: a disc in the character's color.
        center = (14, 13) if i == 0 else (SCREEN_W - 14, 13)
        pygame.draw.circle(surface, OUTLINE, center, 10)
        pygame.draw.circle(surface, fdef.color, center, 9)
        pygame.draw.circle(surface, shade(fdef.color, 60), (center[0] - 3, center[1] - 3), 2)

        # Life: damage trail behind the current value; flashing red in Résolution.
        x = self._mirror(i, 26, LIFE_W)
        surface.fill(OUTLINE, (x - 1, LIFE_Y - 1, LIFE_W + 2, LIFE_H + 2))
        surface.fill((60, 40, 50), (x, LIFE_Y, LIFE_W, LIFE_H))
        shown = self.shown_hp[i] if self.shown_hp[i] is not None else fighter.hp
        for value, color in ((shown, TRAIL), (fighter.hp, self._life_color(fighter))):
            width = round(LIFE_W * value / fighter.max_hp)
            bar_x = x if i == 0 else x + LIFE_W - width
            surface.fill(color, (bar_x, LIFE_Y, width, LIFE_H))
            surface.fill(shade(color, 40), (bar_x, LIFE_Y, width, 2))

        # Guard gauge, just under the life bar.
        gx = self._mirror(i, 26, GUARD_W)
        surface.fill(OUTLINE, (gx - 1, GUARD_Y - 1, GUARD_W + 2, 5))
        broken = fighter.state == State.GUARD_BROKEN
        ratio = fighter.guard_gauge / fighter.rules.guard_gauge_max
        width = round(GUARD_W * ratio)
        color = (90, 90, 100) if broken and (self.tick // 6) % 2 else GUARD
        surface.fill(color, (gx if i == 0 else gx + GUARD_W - width, GUARD_Y, width, 3))

        align = "left" if i == 0 else "right"
        name_x = 26 if i == 0 else SCREEN_W - 26
        font.draw(surface, fdef.name, (name_x, 20), shade(fdef.color, 40), align=align)

        # Round wins, as pips beside the timer.
        for n in range(rounds.rounds_to_win):
            px = 230 - n * 7 - 5 if i == 0 else 250 + n * 7
            surface.fill(OUTLINE, (px - 1, 25, 7, 7))
            filled = n < rounds.wins[i]
            surface.fill(fdef.color if filled else (50, 46, 62), (px, 26, 5, 5))

        self._draw_heart_heat(surface, fighter)

    def _life_color(self, fighter: Fighter) -> tuple[int, int, int]:
        if fighter.in_resolve:
            return LIFE_LOW if (self.tick // 10) % 2 else shade(LIFE_LOW, 40)
        return LIFE

    def _draw_heart_heat(self, surface: pygame.Surface, fighter: Fighter) -> None:
        i = fighter.index
        aura = self.defs[i].aura
        bar = fighter.rules.hh_bar
        bars = round(fighter.rules.hh_max / bar)
        for n in range(bars):
            x = self._mirror(i, 8 + n * (HH_SEGMENT_W + 2), HH_SEGMENT_W)
            surface.fill(OUTLINE, (x - 1, HH_Y - 1, HH_SEGMENT_W + 2, 7))
            surface.fill((40, 36, 52), (x, HH_Y, HH_SEGMENT_W, 5))
            fill = max(0.0, min(1.0, (fighter.hh - n * bar) / bar))
            width = round(HH_SEGMENT_W * fill)
            color = shade(aura, 50) if fill >= 1 else shade(aura, -40)
            surface.fill(color, (x if i == 0 else x + HH_SEGMENT_W - width, HH_Y, width, 5))
        full = int(fighter.hh // bar)
        count_x = 8 + bars * (HH_SEGMENT_W + 2) + 2
        count_x = count_x if i == 0 else SCREEN_W - count_x
        font.draw(
            surface, str(full), (count_x, HH_Y - 2), WHITE, align="left" if i == 0 else "right"
        )
        label_x = 8 if i == 0 else SCREEN_W - 8
        align = "left" if i == 0 else "right"
        if fighter.aura_active:
            font.draw(surface, text.STANCE_ON, (label_x, HH_Y - 11), shade(aura, 40), align=align)
        ready = fighter.time_stop_ready()
        if ready is not None:
            # Time stoppers: is the time stop available, or still recharging?
            color = GOLD if ready else (90, 86, 104)
            stop_x = label_x + (40 if i == 0 else -40)
            font.draw(surface, text.TIME_STOP_READY, (stop_x, HH_Y - 11), color, align=align)

    def _draw_timer(self, surface: pygame.Surface, rounds: Rounds) -> None:
        seconds = rounds.timer_seconds
        label = "∞" if seconds is None else f"{seconds:02d}"
        color = LIFE_LOW if seconds is not None and seconds <= 10 else WHITE
        font.draw(surface, label, (SCREEN_W // 2, 3), color, scale=2, align="center")

    def _draw_announcement(self, surface: pygame.Surface, rounds: Rounds) -> None:
        title, subtitle, color = None, None, WHITE
        intro_f = rounds.rules.round_intro_f
        if rounds.phase == Phase.INTRO:
            if rounds.sudden_death:
                title, color = text.SUDDEN_DEATH, LIFE_LOW
            else:
                title = text.ROUND_N.format(n=rounds.round_number)
            if rounds.phase_f < intro_f // 6:
                return  # brief pause before the announcement pops
        elif rounds.phase == Phase.FIGHT and rounds.phase_f < GO_F and not rounds.training:
            title, color = text.GO, GOLD
        elif rounds.phase == Phase.ROUND_OVER and rounds.result is not None:
            result = rounds.result
            title = {"ko": text.KO, "double_ko": text.DOUBLE_KO, "time": text.TIME_UP}[
                result.reason
            ]
            color = LIFE_LOW if result.reason != "time" else WHITE
            if rounds.training:
                subtitle = None  # no score in training
            elif result.draw:
                subtitle = text.DRAW
            else:
                subtitle = text.ROUND_WINNER.format(name=self.defs[result.winners[0]].name)
        elif rounds.phase == Phase.MATCH_OVER and rounds.winner is not None:
            title, color = text.VICTORY, GOLD
            subtitle = text.WINNER.format(name=self.defs[rounds.winner].name)
        if not title:
            return
        # A dark band behind the text keeps it readable over the fighters.
        height = 54 if subtitle else 40
        if height not in self._bands:
            band = pygame.Surface((SCREEN_W, height), pygame.SRCALPHA)
            band.fill((8, 6, 18, 140))
            self._bands[height] = band
        surface.blit(self._bands[height], (0, 88))
        font.draw(surface, title, (SCREEN_W // 2, 94), color, scale=3, align="center")
        if subtitle:
            font.draw(surface, subtitle, (SCREEN_W // 2, 126), WHITE, align="center")
