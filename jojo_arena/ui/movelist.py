"""Move list: every move of a character with its input, name and a short explanation.

Built from the kit data (labels and infos in characters/<id>.toml) and from the
player's controls, so the keys shown are the ones this player really uses.
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from jojo_arena.characters import FighterDef
from jojo_arena.combat.rules import Rules
from jojo_arena.controls import PlayerControls
from jojo_arena.engine import font
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.input import InputManager
from jojo_arena.engine.sprites import shade
from jojo_arena.ui import text
from jojo_arena.ui.labels import action_label, device_label, menu_key, move_label
from jojo_arena.ui.widgets import (
    BORDER,
    DIM,
    GOLD,
    WHITE,
    draw_caps,
    draw_hints,
    draw_wrapped,
    veil,
)

STANCE_SLOTS = ("light", "heavy", "heavy_alt", "special", "special_alt")
VARIANTS = {"heavy_alt": "heavy", "special_alt": "special"}  # a direction + this button
NAME_X = 128
SCREEN = (480, 270)
TOP = 64


@dataclass(frozen=True)
class MoveEntry:
    keys: tuple[str, ...]  # key caps, pressed together (none for passive rules)
    name: str
    info: str = ""
    sequence: bool = False  # the keys are pressed one after the other (a chain)


@dataclass(frozen=True)
class MovePage:
    title: str
    entries: tuple[MoveEntry, ...]
    note: str = ""  # shown under the entries
    part: int = 1  # a page too long for the screen is cut in parts: this one...
    parts: int = 1  # ...out of so many


ENTRY_GAP = 7
BOTTOM_MARGIN = 30  # room kept for the hints at the bottom


def entry_height(entry: MoveEntry, width: int) -> int:
    lines = len(font.wrap(entry.info, width - NAME_X - 16)) if entry.info else 0
    return 11 + 10 * lines + ENTRY_GAP


def paginate(pages: list[MovePage], size: tuple[int, int]) -> list[MovePage]:
    """Cut the pages whose entries run past the bottom of the screen into parts."""
    width, height = size
    room = height - BOTTOM_MARGIN - TOP
    result: list[MovePage] = []
    for page in pages:
        chunks: list[list[MoveEntry]] = [[]]
        used = 0
        for entry in page.entries:
            needed = entry_height(entry, width)
            if chunks[-1] and used + needed > room:
                chunks.append([])
                used = 0
            chunks[-1].append(entry)
            used += needed
        for i, chunk in enumerate(chunks):
            note = page.note if i == len(chunks) - 1 else ""
            result.append(MovePage(page.title, tuple(chunk), note, i + 1, len(chunks)))
    return result


def _bars(amount: float) -> str:
    """A Heart Heat cost in bars: "1/2 BARRE", "1 BARRE", "2 BARRES"."""
    if amount < 1:
        return f"1/{round(1 / amount)} {text.BAR}"
    if amount == 1:
        return text.BARS_ONE
    return text.BARS_MANY.format(n=round(amount))


def _info(move) -> str:
    """A move's line in the list, with its Hamon cost in front when it has one."""
    tag = ""
    if move.hamon_cost:
        tag = text.HAMON_TAG.format(cost=move.hamon_cost)
    elif move.blood_cost:
        tag = text.BLOOD_TAG.format(cost=move.blood_cost)
    if tag:
        return f"{tag} - {move.info}" if move.info else tag
    return move.info


def build_pages(
    fdef: FighterDef, player: PlayerControls, rules: Rules, inputs: InputManager | None = None
) -> list[MovePage]:
    kit = fdef.kit

    def key(action: str) -> str:
        return action_label(player, action, inputs)

    pages: list[MovePage] = []
    for stance_name, stance in kit.stances.items():
        entries = []
        for slot in STANCE_SLOTS:
            move = stance.moves.get(slot)
            if move is None:
                continue
            keys = (text.DIRECTION, key(VARIANTS[slot])) if slot in VARIANTS else (key(slot),)
            entries.append(MoveEntry(keys, move.label or slot.upper(), _info(move)))
            if move.counter and move.counter in stance.moves:
                # The answer of a counter comes out on its own, when struck.
                answer = stance.moves[move.counter]
                entries.append(
                    MoveEntry((text.WHEN_STRUCK,), answer.label or answer.name, _info(answer), True)
                )
            # A chain: the same button again, once the previous blow connects.
            depth = 1
            while move.chain and move.chain in stance.moves and depth < 6:
                move = stance.moves[move.chain]
                depth += 1
                presses = (key(slot),) * depth
                entries.append(MoveEntry(presses, move.label or move.name, _info(move), True))
        if entries:
            title = kit.stance_labels.get(stance_name, stance_name.upper())
            pages.append(MovePage(title, tuple(entries)))

    supers = []
    for slot, cost in (("hha", rules.hha_cost), ("gha", rules.gha_cost)):
        move = kit.shared_moves.get(slot)
        if move is not None:
            info = f"{_bars(cost / rules.hh_bar)} - {move.info}" if move.info else ""
            keys = (text.DIRECTION, key("heart_heat")) if slot == "gha" else (key("heart_heat"),)
            supers.append(MoveEntry(keys, move.label or slot.upper(), info))
    if supers:
        note = text.SYS_SUPER_INFO if len(supers) == 2 else ""
        pages.append(MovePage(text.PAGE_SUPER, tuple(supers), note))

    prop_info = text.SYS_PROP_INFO if fdef.stand_sprite else text.SYS_PROP_INFO_HANDS
    stand_info = text.SYS_STYLE_INFO
    if fdef.stand_name:
        stand_info = text.SYS_STAND_INFO.format(stand=fdef.stand_name)
    basics = [
        MoveEntry((move_label(player),), text.SYS_MOVE, text.SYS_MOVE_INFO),
        MoveEntry((key("guard"),), text.SYS_GUARD, text.SYS_GUARD_INFO),
        MoveEntry((key("dash"),), text.SYS_DASH, text.SYS_DASH_INFO),
        MoveEntry((key("pose"),), text.SYS_POSE, text.SYS_POSE_INFO),
        MoveEntry((key("pose"),), text.SYS_PROP, prop_info),
    ]
    if kit.pose_counter:
        # Posing calls the opponent's next move: right, it is answered at once.
        answer = kit.move(kit.base_stance_name, kit.pose_counter)
        entry = MoveEntry((key("pose"),), answer.label or answer.name, _info(answer))
        basics.insert(4, entry)
    if kit.style == "hamon":
        basics.insert(1, MoveEntry((key("stand"),), text.SYS_BREATH, text.SYS_BREATH_INFO))
    if kit.style == "vampire":
        basics.insert(1, MoveEntry((key("stand"),), text.SYS_FREEZE, text.SYS_FREEZE_INFO))
        basics.insert(2, MoveEntry((), text.SYS_BLOOD, text.SYS_BLOOD_INFO))
    elif len(kit.stances) > 1:
        basics.insert(1, MoveEntry((key("stand"),), text.SYS_STAND, stand_info))
    if kit.style_params.get("remote"):
        secs = f"{rules.remote_hold_f / 60:.1f}".replace(".", ",")
        stand = fdef.stand_name or text.SYS_STAND
        remote_info = text.SYS_REMOTE_INFO.format(secs=secs, stand=stand)
        basics.insert(2, MoveEntry((key("stand"),), text.SYS_REMOTE, remote_info))
    pages.append(MovePage(text.PAGE_BASICS, tuple(basics)))

    flash = text.SYS_FLASH_INFO.format(cost=_bars(rules.flash_cancel_cost / rules.hh_bar))
    resolve = text.SYS_RESOLVE_INFO.format(
        threshold=round(rules.resolve_threshold * 100),
        bonus=round(rules.resolve_damage_bonus * 100),
    )
    technique = [
        MoveEntry((key("guard"),), text.SYS_FLASH, flash),
        MoveEntry((text.SYS_CLASH_KEYS,), text.SYS_CLASH, text.SYS_CLASH_INFO),
        MoveEntry((), text.SYS_GUARD_BREAK, text.SYS_GUARD_BREAK_INFO),
        MoveEntry((), text.SYS_RESOLVE, resolve),
    ]
    pages.append(MovePage(text.PAGE_TECH, tuple(technique)))
    return pages


class MoveListPanel:
    """Full-screen move list over whatever is behind. Left/right turns the pages."""

    def __init__(
        self,
        fdef: FighterDef,
        player: PlayerControls,
        rules: Rules,
        player_name: str = "",
        inputs: InputManager | None = None,
    ) -> None:
        self.fdef = fdef
        self.pages = paginate(build_pages(fdef, player, rules, inputs), SCREEN)
        self.page = 0
        self.owner = f"{player_name or text.P1} - {device_label(player)}"
        self.hints = [
            ("←→", text.HINT_PAGE),
            (menu_key("back", inputs), text.HINT_CLOSE),
        ]

    def handle(self, frame: InputFrame) -> bool:
        """Read one step of menu input. Returns False once the panel is closed."""
        step = int(frame.was_pressed("right")) - int(frame.was_pressed("left"))
        if step:
            self.page = (self.page + step) % len(self.pages)
        closing = ("back", "info", "pause", "confirm")
        return not any(frame.was_pressed(action) for action in closing)

    def draw(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        surface.blit(veil((width, height), (8, 6, 18, 242)), (0, 0))
        fdef = self.fdef
        name_scale = 2 if font.text_width(fdef.name, 2) < 280 else 1
        font.draw(surface, fdef.name, (16, 8), shade(fdef.color, 50), scale=name_scale)
        if fdef.stand_name:
            font.draw(surface, f"{text.STAND_LABEL} : {fdef.stand_name}", (16, 29), fdef.aura)
        font.draw(surface, text.MOVE_LIST, (width - 16, 8), GOLD, align="right")
        font.draw(surface, self.owner, (width - 16, 20), DIM, align="right")

        # Tabs: one per page; the parts of a long page share their tab.
        x = 16
        shown = self.pages[self.page]
        for page in self.pages:
            if page.part > 1:
                continue
            current = page.title == shown.title
            color = GOLD if current else DIM
            label = page.title
            if current and shown.parts > 1:
                label = f"{page.title} {shown.part}/{shown.parts}"
            rect = font.draw(surface, label, (x, 44), color)
            if current:
                surface.fill(GOLD, (rect.x, rect.bottom + 1, rect.width, 2))
            x = rect.right + 12
        surface.fill(BORDER, (16, 58, width - 32, 1))

        y = TOP
        for entry in self.pages[self.page].entries:
            draw_caps(surface, entry.keys, (16, y - 1), ">" if entry.sequence else "+")
            font.draw(surface, entry.name, (NAME_X, y), WHITE)
            y += 11
            if entry.info:
                y = draw_wrapped(surface, entry.info, (NAME_X, y), width - NAME_X - 16)
            y += ENTRY_GAP
        note = self.pages[self.page].note
        if note:
            draw_wrapped(surface, note, (16, y + 2), width - 32, GOLD)
        draw_hints(surface, self.hints, (width // 2, height - 16))
