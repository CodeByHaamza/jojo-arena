"""Global fight rules, loaded from rules.toml and converted to per-frame units."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from jojo_arena.engine.data import load_toml, seconds_to_frames

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
    guard_damage_reduction: float
    guard_gauge_max: float
    guard_gauge_per_damage: float
    guard_regen_delay_f: int
    guard_regen_per_f: float
    guard_break_stun_f: int
    blockstun_ratio: float
    block_pushback_ratio: float
    guard_arc_cos: float  # cosine of half the guarded arc
    dash_duration_f: int
    dash_speed: float  # px/frame
    dash_invincible_f: int
    dash_recovery_f: int
    stylish_window_f: int
    stylish_slowmo_f: int
    hh_bar: float
    hh_max: float
    hh_per_damage_dealt: float
    hh_per_damage_taken: float
    hh_block_ratio: float
    hh_stylish_gain: float
    hh_pose_per_f: float
    hha_cost: float
    super_freeze_f: int
    flash_cancel_cost: float
    flash_cancel_freeze_f: int
    resolve_threshold: float
    resolve_damage_bonus: float
    stance_switch_f: int
    clash_window_f: int
    clash_duration_f: int
    clash_loser_damage: int
    clash_loser_knockback: float  # px/frame
    clash_loser_hitstun_f: int
    clash_tie_knockback: float  # px/frame

    @classmethod
    def from_data(cls, data: dict) -> Rules:
        body, knock, wall = data["body"], data["knockback"], data["wall_bounce"]
        guard, dash, hh, clash = data["guard"], data["dash"], data["heart_heat"], data["clash"]
        return cls(
            clash_window_f=clash["window_f"],
            clash_duration_f=seconds_to_frames(clash["duration_s"]),
            clash_loser_damage=clash["loser_damage"],
            clash_loser_knockback=per_frame(clash["loser_knockback"]),
            clash_loser_hitstun_f=clash["loser_hitstun_f"],
            clash_tie_knockback=per_frame(clash["tie_knockback"]),
            hh_bar=hh["bar_size"],
            hh_max=hh["bar_size"] * hh["bars"],
            hh_per_damage_dealt=hh["gain_per_damage_dealt"],
            hh_per_damage_taken=hh["gain_per_damage_taken"],
            hh_block_ratio=hh["block_gain_ratio"],
            hh_stylish_gain=hh["stylish_gain"],
            hh_pose_per_f=hh["pose_gain_per_s"] / HZ,
            hha_cost=hh["hha_cost"],
            super_freeze_f=seconds_to_frames(hh["super_freeze_s"]),
            flash_cancel_cost=hh["flash_cancel_cost"],
            flash_cancel_freeze_f=hh["flash_cancel_freeze_f"],
            resolve_threshold=data["resolve"]["threshold"],
            resolve_damage_bonus=data["resolve"]["damage_bonus"],
            stance_switch_f=data["stance"]["switch_f"],
            body_radius=body["radius"],
            hurt_radius=body["hurt_radius"],
            walk_speed=per_frame(body["walk_speed"]),
            knockback_friction=per_frame_sq(knock["friction"]),
            obstacle_damage_per_speed=knock["obstacle_damage_per_speed"],
            wall_bounce_min_speed=per_frame(wall["min_speed"]),
            wall_bounce_keep=wall["keep"],
            wall_bounce_stun_f=wall["stun_f"],
            wall_bounce_damage=wall["damage"],
            guard_damage_reduction=guard["damage_reduction"],
            guard_gauge_max=guard["gauge_max"],
            guard_gauge_per_damage=guard["gauge_per_damage"],
            guard_regen_delay_f=seconds_to_frames(guard["regen_delay_s"]),
            guard_regen_per_f=guard["regen_per_s"] / HZ,
            guard_break_stun_f=seconds_to_frames(guard["break_stun_s"]),
            blockstun_ratio=guard["blockstun_ratio"],
            block_pushback_ratio=guard["pushback_ratio"],
            guard_arc_cos=math.cos(math.radians(guard["arc_deg"] / 2)),
            dash_duration_f=dash["duration_f"],
            dash_speed=per_frame(dash["speed"]),
            dash_invincible_f=dash["invincible_f"],
            dash_recovery_f=dash["recovery_f"],
            stylish_window_f=dash["stylish_window_f"],
            stylish_slowmo_f=seconds_to_frames(dash["stylish_slowmo_s"]),
        )


def load_rules(path: Path = RULES_PATH) -> Rules:
    return Rules.from_data(load_toml(path))
