"""A fighter's moveset and stats, read from its character data file."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from jojo_arena.combat.rules import HZ, per_frame
from jojo_arena.engine.data import load_toml, seconds_to_frames

# Input slots that start a move; the stance decides which move each slot maps to.
# "special" pressed while a direction is held uses the "special_alt" move if there is one.
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
    count: int = 1  # several projectiles at once...
    spread_deg: float = 0.0  # ...fanned out over this angle
    origin: str = "self"  # "self", or "ring": around the target, flying inward
    ring_radius: float = 0.0
    homing: float = 0.0  # radians per frame it turns toward the target (0 = straight)
    waves: int = 1  # volleys thrown one after the other...
    wave_every_f: int = 4  # ...this many frames apart (each volley offset a little)
    look: str = "orb"  # how the view draws it: "orb", "knife", "gem", "blade"

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
            count=data.get("count", 1),
            spread_deg=data.get("spread_deg", 0.0),
            origin=data.get("origin", "self"),
            ring_radius=data.get("ring_radius", 0.0),
            homing=math.radians(data.get("homing_deg_s", 0.0)) / HZ,
            waves=data.get("waves", 1),
            wave_every_f=data.get("wave_every_f", 4),
            look=data.get("look", "orb"),
        )


@dataclass(frozen=True)
class TrapDef:
    """Something laid on the ground that fires on its own when the opponent comes close."""

    distance: float  # laid this far in front of the user
    radius: float  # trigger radius
    lifetime_f: int
    max_count: int  # the oldest disappears when one more is laid
    projectile: ProjectileDef  # what it fires at the opponent when triggered

    @classmethod
    def from_data(cls, data: dict) -> TrapDef:
        return cls(
            distance=data.get("distance", 20),
            radius=data["radius"],
            lifetime_f=seconds_to_frames(data["lifetime_s"]),
            max_count=data.get("max_count", 3),
            projectile=ProjectileDef.from_data(data["projectile"]),
        )


@dataclass(frozen=True)
class BuffDef:
    """A temporary state started by a move (e.g. dropping armor for speed)."""

    duration_f: int
    speed_mult: float = 1.0
    damage_dealt_mult: float = 1.0
    damage_taken_mult: float = 1.0
    afterimages: bool = False

    @classmethod
    def from_data(cls, data: dict) -> BuffDef:
        return cls(
            duration_f=seconds_to_frames(data["duration_s"]),
            speed_mult=data.get("speed_mult", 1.0),
            damage_dealt_mult=data.get("damage_dealt_mult", 1.0),
            damage_taken_mult=data.get("damage_taken_mult", 1.0),
            afterimages=data.get("afterimages", False),
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
    shape: str = "circle"  # "circle" at `reach`, or "line": from the body out to `reach`
    hitstun_f: int = 0
    blockstun_f: int = 0  # 0 = derived from hitstun (rules)
    knockback: float = 0.0  # px/frame
    hitstop_f: int = 0
    wall_bounce: bool = False
    cancel_on_hit: tuple[str, ...] = ()
    anim: str = ""
    projectile: ProjectileDef | None = None
    invincible_f: int = 0  # first frames of the move that cannot be hit
    clashable: bool = True  # can start a clash against another clashable attack
    hits: int = 1  # rush: the hitbox can hit this many times...
    hit_every_f: int = 0  # ...once every this many frames
    last_knockback: float | None = None  # px/frame, for the last hit of a rush
    last_damage: int | None = None  # damage of the last hit of a rush (the finisher)
    last_wall_bounce: bool = False
    lunge: float = 0.0  # px/frame forward during startup and active frames
    at_target: bool = False  # the hitbox lands where the opponent stood at the start
    unblockable: bool = False  # grabs
    drain: float = 0.0  # share of the damage dealt that heals the attacker
    cooldown_f: int = 0  # cannot be used again for this long
    time_stop_f: int = 0  # stops time for this long...
    time_stop_at: str = "active"  # ...from the first "active" frame, or from the "start"
    trap: TrapDef | None = None
    disarm_f: int = 0  # the Stand's own moves are unavailable this long afterwards
    buff: str = ""  # name of a buff (kit [buffs]) started by this move
    chain: str = ""  # the same button, once this connects, continues into this move
    counter: str = ""  # struck in melee while active: answer at once with this move
    leap: float = 0.0  # px: during startup, travel up to this far...
    leap_to: str = "target"  # ...toward the opponent ("target") or the aimed point ("cursor")
    leap_height: float = 0.0  # px: height of the jump arc, for the view (0 = slide)
    armor: int = 0  # hits taken without flinching during startup and active frames
    guard_damage: float = 1.0  # multiplies the guard gauge damage when blocked
    stand_flash: bool = False  # the Stand appears for this move even when called back
    fx: str = ""  # drawn while active: "limb", "tentacle" or "blade" out to `reach`
    shout: str = ""  # written on screen when used (each hit of a rush: "ORA", "MUDA")
    label: str = ""  # display name in the move list
    info: str = ""  # one-line description in the move list

    @property
    def total_f(self) -> int:
        return self.startup_f + self.active_f + self.recovery_f

    @classmethod
    def from_data(cls, name: str, data: dict) -> MoveDef:
        projectile = data.get("projectile")
        trap = data.get("trap")
        last_knockback = data.get("last_knockback")
        return cls(
            name=name,
            startup_f=data["startup_f"],
            active_f=data["active_f"],
            recovery_f=data["recovery_f"],
            damage=data.get("damage", 0),
            reach=data.get("reach", 0.0),
            radius=data.get("radius", 0.0),
            shape=data.get("shape", "circle"),
            hitstun_f=data.get("hitstun_f", 0),
            blockstun_f=data.get("blockstun_f", 0),
            knockback=per_frame(data.get("knockback", 0)),
            hitstop_f=data.get("hitstop_f", 0),
            wall_bounce=data.get("wall_bounce", False),
            cancel_on_hit=tuple(data.get("cancel_on_hit", ())),
            anim=data.get("anim", name),
            projectile=ProjectileDef.from_data(projectile) if projectile else None,
            invincible_f=data.get("invincible_f", 0),
            clashable=data.get("clashable", data.get("radius", 0) > 0),
            hits=data.get("hits", 1),
            hit_every_f=data.get("hit_every_f", 0),
            last_knockback=per_frame(last_knockback) if last_knockback is not None else None,
            last_wall_bounce=data.get("last_wall_bounce", False),
            last_damage=data.get("last_damage"),
            lunge=per_frame(data.get("lunge", 0)),
            at_target=data.get("at_target", False),
            unblockable=data.get("unblockable", False),
            drain=data.get("drain", 0.0),
            cooldown_f=seconds_to_frames(data.get("cooldown_s", 0)),
            time_stop_f=seconds_to_frames(data.get("time_stop_s", 0)),
            time_stop_at=data.get("time_stop_at", "active"),
            trap=TrapDef.from_data(trap) if trap else None,
            disarm_f=seconds_to_frames(data.get("disarm_s", 0)),
            buff=data.get("buff", ""),
            chain=data.get("chain", ""),
            counter=data.get("counter", ""),
            leap=data.get("leap", 0.0),
            leap_to=data.get("leap_to", "target"),
            leap_height=data.get("leap_height", 0.0),
            armor=data.get("armor", 0),
            guard_damage=data.get("guard_damage", 1.0),
            stand_flash=data.get("stand_flash", False),
            fx=data.get("fx", ""),
            shout=data.get("shout", ""),
            label=data.get("label", ""),
            info=data.get("info", ""),
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
    style_params: dict = field(default_factory=dict)
    stances: dict[str, Stance] = field(default_factory=dict)
    shared_moves: dict[str, MoveDef] = field(default_factory=dict)  # same in every stance
    buffs: dict[str, BuffDef] = field(default_factory=dict)
    stance_labels: dict[str, str] = field(default_factory=dict)  # move list headings

    def move(self, stance: str, slot: str) -> MoveDef | None:
        return self.stances[stance].moves.get(slot) or self.shared_moves.get(slot)

    def all_moves(self) -> list[MoveDef]:
        moves = list(self.shared_moves.values())
        for stance in self.stances.values():
            moves += stance.moves.values()
        return moves

    @property
    def time_stopper(self) -> bool:
        """Can stop time (matters when caught in another time stopper's stopped time)."""
        return any(move.time_stop_f > 0 for move in self.all_moves())


def load_kit(path: Path) -> Kit:
    return parse_kit(load_toml(path), path.stem, path.name)


def parse_kit(data: dict, kit_id: str, source: str = "kit") -> Kit:
    """Build a kit from its data (the content of a kit file); `source` names it in errors."""
    stances = {
        name: Stance(
            moves={slot: MoveDef.from_data(slot, m) for slot, m in stance["moves"].items()},
            walk_speed_mult=stance.get("walk_speed_mult", 1.0),
        )
        for name, stance in data["stances"].items()
    }
    shared = {slot: MoveDef.from_data(slot, m) for slot, m in data.get("moves", {}).items()}
    buffs = {name: BuffDef.from_data(b) for name, b in data.get("buffs", {}).items()}
    for stance_name, stance in stances.items():
        for move in [*stance.moves.values(), *shared.values()]:
            for link in (move.chain, move.counter):
                if link and link not in stance.moves and link not in shared:
                    raise ValueError(
                        f"{source}: move '{move.name}' leads to unknown move '{link}' "
                        f"in stance '{stance_name}'"
                    )
    for move in [*shared.values(), *(m for s in stances.values() for m in s.moves.values())]:
        if move.buff and move.buff not in buffs:
            raise ValueError(f"{source}: move '{move.name}' uses unknown buff '{move.buff}'")
        if move.leap_to not in ("target", "cursor"):
            raise ValueError(f"{source}: move '{move.name}' has unknown leap_to")
    walk = data.get("walk_speed")
    style = data.get("style", "none")
    style_name, style_params = (style, {}) if isinstance(style, str) else (style["type"], style)
    return Kit(
        id=kit_id,
        name=data["name"],
        max_hp=data.get("max_hp", 1000),
        walk_speed=per_frame(walk) if walk else None,
        style=style_name,
        style_params=style_params,
        stances=stances,
        shared_moves=shared,
        buffs=buffs,
        stance_labels={
            name: stance.get("label", name.upper()) for name, stance in data["stances"].items()
        },
    )
