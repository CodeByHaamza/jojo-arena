"""A fighter's moveset and stats, read from its character data file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jojo_arena.combat.rules import per_frame
from jojo_arena.engine.data import load_toml, seconds_to_frames

# Input slots that start a move; the stance decides which move each slot maps to.
ATTACK_SLOTS = ("light", "heavy", "special")


@dataclass(frozen=True)
class ProjectileDef:
    speed: float  # px/frame
    radius: float
    damage: int
    lifetime_f: int
    hitstun_f: int
    knockback: float  # px/frame
    hitstop_f: int
    blockstun_f: int = 0  # 0 = derived from hitstun (rules)

    @classmethod
    def from_data(cls, data: dict) -> ProjectileDef:
        return cls(
            speed=per_frame(data["speed"]),
            radius=data["radius"],
            damage=data["damage"],
            lifetime_f=seconds_to_frames(data["lifetime_s"]),
            hitstun_f=data["hitstun_f"],
            knockback=per_frame(data.get("knockback", 0)),
            hitstop_f=data.get("hitstop_f", 3),
            blockstun_f=data.get("blockstun_f", 0),
        )


@dataclass(frozen=True)
class MoveDef:
    name: str
    startup_f: int
    active_f: int
    recovery_f: int
    damage: int = 0
    reach: float = 0.0  # hitbox center, in front of the body
    radius: float = 0.0  # hitbox radius (0 = no melee hitbox)
    hitstun_f: int = 0
    blockstun_f: int = 0  # 0 = derived from hitstun (rules)
    knockback: float = 0.0  # px/frame
    hitstop_f: int = 0
    wall_bounce: bool = False
    cancel_on_hit: tuple[str, ...] = ()
    anim: str = ""
    projectile: ProjectileDef | None = None

    @property
    def total_f(self) -> int:
        return self.startup_f + self.active_f + self.recovery_f

    @classmethod
    def from_data(cls, name: str, data: dict) -> MoveDef:
        projectile = data.get("projectile")
        return cls(
            name=name,
            startup_f=data["startup_f"],
            active_f=data["active_f"],
            recovery_f=data["recovery_f"],
            damage=data.get("damage", 0),
            reach=data.get("reach", 0.0),
            radius=data.get("radius", 0.0),
            hitstun_f=data.get("hitstun_f", 0),
            blockstun_f=data.get("blockstun_f", 0),
            knockback=per_frame(data.get("knockback", 0)),
            hitstop_f=data.get("hitstop_f", 0),
            wall_bounce=data.get("wall_bounce", False),
            cancel_on_hit=tuple(data.get("cancel_on_hit", ())),
            anim=data.get("anim", name),
            projectile=ProjectileDef.from_data(projectile) if projectile else None,
        )


@dataclass(frozen=True)
class Stance:
    moves: dict[str, MoveDef]
    walk_speed_mult: float = 1.0


@dataclass(frozen=True)
class Kit:
    id: str
    name: str
    max_hp: int
    walk_speed: float | None  # px/frame, None = rules default
    style: str
    stances: dict[str, Stance] = field(default_factory=dict)

    def move(self, stance: str, slot: str) -> MoveDef | None:
        return self.stances[stance].moves.get(slot)


def load_kit(path: Path) -> Kit:
    data = load_toml(path)
    stances = {
        name: Stance(
            moves={slot: MoveDef.from_data(slot, m) for slot, m in stance["moves"].items()},
            walk_speed_mult=stance.get("walk_speed_mult", 1.0),
        )
        for name, stance in data["stances"].items()
    }
    walk = data.get("walk_speed")
    return Kit(
        id=path.stem,
        name=data["name"],
        max_hp=data.get("max_hp", 1000),
        walk_speed=per_frame(walk) if walk else None,
        style=data.get("style", "none"),
        stances=stances,
    )
