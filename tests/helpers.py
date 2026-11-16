"""Shared builders for combat tests: a match in an empty arena and input shortcuts."""

from __future__ import annotations

import pygame

from jojo_arena.characters import get_fighter
from jojo_arena.combat.arena import Arena, Obstacle
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Rect, RoundedRect, Vec2
from jojo_arena.engine.sprites import SheetSprites

NONE = InputFrame()
OPEN_BOUNDS = RoundedRect(Rect(0, 0, 400, 200), 20)


def press(*actions: str, move=(0.0, 0.0), hold=()) -> InputFrame:
    return InputFrame(move, frozenset(hold), {a: 1 for a in actions})


def hold(*actions: str, move=(0.0, 0.0)) -> InputFrame:
    return InputFrame(move, frozenset(actions), {})


def walk(dx: float, dy: float = 0.0) -> InputFrame:
    return InputFrame((dx, dy), frozenset(), {})


def make_match(p1=(150, 100), p2=(180, 100), obstacles=(), bounds=OPEN_BOUNDS) -> Match:
    arena = Arena(bounds, (Vec2(*p1), Vec2(*p2)), list(obstacles))
    kit = get_fighter("mannequin_red").kit
    return Match((kit, kit), load_rules(), arena)


def make_duel(p1_id: str, p2_id: str, p1=(150, 100), p2=(180, 100)) -> Match:
    """A match between two roster fighters in an empty arena."""
    arena = Arena(OPEN_BOUNDS, (Vec2(*p1), Vec2(*p2)), [])
    kits = (get_fighter(p1_id).kit, get_fighter(p2_id).kit)
    return Match(kits, load_rules(), arena)


def run_until(match: Match, condition, limit: int = 600, p1=NONE, p2=NONE) -> list:
    """Step with the given inputs held until `condition(match)` is true."""
    events = []
    for _ in range(limit):
        if condition(match):
            return events
        events += match.step((p1, p2))
    raise AssertionError("condition never met")


def crate(x, y, w=12, h=11, hp=40) -> Obstacle:
    return Obstacle("crate", Rect(x, y, w, h), hp)


def run(match: Match, frames: int, p1=NONE, p2=NONE) -> list:
    """Step `frames` times; p1/p2 apply on the first step only, then neutral input."""
    events = []
    for i in range(frames):
        events += match.step((p1, p2) if i == 0 else (NONE, NONE))
    return events


def run_held(match: Match, frames: int, p1=NONE, p2=NONE) -> list:
    """Step `frames` times with the same inputs every step (held buttons)."""
    events = []
    for _ in range(frames):
        events += match.step((p1, p2))
    return events


def kinds(events) -> list[str]:
    return [e.kind for e in events]


# Sprite sheets with colours, built on the fly ------------------------------------------------

GREY = (120, 120, 130)


def colored_sheet(tmp_path, colors: int, name: str = "sheet"):
    """A one-animation sheet of one flat tone, with `colors` colours: c0 is the sheet as it
    is, cN paints the body (N * 20, 10, 10)."""
    image = pygame.Surface((64, 192), pygame.SRCALPHA)
    image.fill((*GREY, 255), (20, 20, 24, 24))
    png, spec = tmp_path / f"{name}.png", tmp_path / f"{name}.toml"
    pygame.image.save(image, str(png))
    lines = [
        "frame_size = [64, 64]",
        "anchor = [32, 60]",
        'directions = ["down", "up", "right"]',
        "",
        "[anims.idle]",
        "row = 0",
        "frames = 1",
    ]
    if colors:
        lines += ["", "[costume]", 'label = "Tenue"', 'label_en = "Outfit"', 'source = "S"']
        lines += ["", "[recolor]", f"body = [{list(GREY)}]"]
    for n in range(colors):
        lines += ["", f"[colors.c{n}]", f'label = "C{n}"', f'label_en = "C{n} en"']
        lines += [f'source = "source {n}"', f'stand = "{"s1" if n == 1 else ""}"']
        if n:
            lines += [f"[colors.c{n}.palette]", f"body = [[{n * 20}, 10, 10]]"]
    spec.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return png, spec


def body(sheet: SheetSprites):
    return tuple(sheet.frame("idle", "down", False, 0).get_at((30, 30)))[:3]
