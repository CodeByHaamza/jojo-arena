"""Global fight rules, loaded from rules.toml and converted to per-frame units."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jojo_arena.engine.data import load_toml

RULES_PATH = Path(__file__).with_name("rules.toml")
HZ = 60


def per_frame(px_per_s: float) -> float:
    return px_per_s / HZ


def per_frame_sq(px_per_s2: float) -> float:
    return px_per_s2 / (HZ * HZ)


@dataclass(frozen=True)
class Rules:
    body_radius: float
    hurt_radius: float
    walk_speed: float  # px/frame
    knockback_friction: float  # px/frame²
    obstacle_damage_per_speed: float  # per px/s
    wall_bounce_min_speed: float  # px/frame
    wall_bounce_keep: float
    wall_bounce_stun_f: int
    wall_bounce_damage: int

    @classmethod
    def from_data(cls, data: dict) -> Rules:
        body, knock, wall = data["body"], data["knockback"], data["wall_bounce"]
        return cls(
            body_radius=body["radius"],
            hurt_radius=body["hurt_radius"],
            walk_speed=per_frame(body["walk_speed"]),
            knockback_friction=per_frame_sq(knock["friction"]),
            obstacle_damage_per_speed=knock["obstacle_damage_per_speed"],
            wall_bounce_min_speed=per_frame(wall["min_speed"]),
            wall_bounce_keep=wall["keep"],
            wall_bounce_stun_f=wall["stun_f"],
            wall_bounce_damage=wall["damage"],
        )


def load_rules(path: Path = RULES_PATH) -> Rules:
    return Rules.from_data(load_toml(path))
