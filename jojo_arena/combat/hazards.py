"""Arena hazards: what the place itself does to whoever fights in it.

Three kinds, each described by a stage's data file and blind to who is fighting:

- a **drop**: something heavy falls from above, again and again, on a spot of the floor
  that is marked a moment before (a shadow growing on the floor);
- a **trap zone**: a patch of floor that springs when somebody is knocked into it;
- a **surface**: a floor that does not grip, where a body keeps sliding the way it was
  going (and gets carried further by a blow);
- an **exit**: a stretch of wall that gives way when somebody is slammed into it, and
  the fight goes on in another arena (named by the stage, built by the stage layer).

A kit style can be spared by a trap or a surface (`spare_style`): what that style
means is the stage's business, the engine only compares names.

Everything here is a pure function of the match state and the step counter: the spot
a drop falls on is chosen from the fighters' positions, never at random.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from jojo_arena.combat.rules import HZ
from jojo_arena.engine.data import seconds_to_frames
from jojo_arena.engine.geometry import Rect, Vec2


@dataclass(frozen=True)
class DropDef:
    """Something that falls on the floor, over and over (a chandelier, a rock)."""

    spots: tuple[Vec2, ...]  # where it can come down
    first_f: int  # it falls for the first time this far into the round...
    every_f: int  # ...then again this often
    warning_f: int  # its shadow is on the floor this long before it lands
    radius: float
    damage: int
    hitstun_f: int
    knockback: float  # px/frame, away from where it lands
    wreck_f: int = 0  # how long the wreck lies there afterwards (for the view)
    look: str = ""  # what the view draws

    @classmethod
    def from_data(cls, data: dict) -> DropDef:
        return cls(
            spots=tuple(Vec2(*spot) for spot in data["spots"]),
            first_f=seconds_to_frames(data["first_s"]),
            every_f=seconds_to_frames(data["every_s"]),
            warning_f=seconds_to_frames(data["warning_s"]),
            radius=data["radius"],
            damage=data["damage"],
            hitstun_f=data["hitstun_f"],
            knockback=data.get("knockback", 0) / HZ,
            wreck_f=seconds_to_frames(data.get("wreck_s", 0)),
            look=data.get("look", ""),
        )


@dataclass(frozen=True)
class TrapZoneDef:
    """A patch of floor that springs on whoever is knocked into it (spikes)."""

    rect: Rect
    damage: int
    hitstun_f: int
    knockback: float  # px/frame, thrown back out of the zone
    min_speed: float  # px/frame: a body knocked in at least this fast sets it off
    rearm_f: int  # it cannot spring again before this long
    spare_style: str = ""  # bodies of this kit style are not hurt
    look: str = ""

    @classmethod
    def from_data(cls, data: dict) -> TrapZoneDef:
        return cls(
            rect=Rect(*data["rect"]),
            damage=data["damage"],
            hitstun_f=data["hitstun_f"],
            knockback=data.get("knockback", 0) / HZ,
            min_speed=data.get("min_speed", 120) / HZ,
            rearm_f=seconds_to_frames(data.get("rearm_s", 1.0)),
            spare_style=data.get("spare_style", ""),
            look=data.get("look", ""),
        )


@dataclass(frozen=True)
class SurfaceDef:
    """A floor that does not grip: oil, ice, packed snow."""

    rect: Rect | None  # None: the whole arena
    grip: float  # share of the wanted walking speed taken each step (1 = normal floor)
    slide: float  # multiplies the friction on a knocked-back body (below 1: slides further)
    spare_style: str = ""  # bodies of this kit style walk on it as on a normal floor
    look: str = ""

    @classmethod
    def from_data(cls, data: dict) -> SurfaceDef:
        rect = data.get("rect")
        return cls(
            rect=Rect(*rect) if rect is not None else None,
            grip=data["grip"],
            slide=data.get("slide", 1.0),
            spare_style=data.get("spare_style", ""),
            look=data.get("look", ""),
        )


@dataclass(frozen=True)
class ExitDef:
    """A stretch of wall a body can be slammed through, into another arena."""

    rect: Rect  # a wall bounce inside this zone breaks through
    to: str  # the arena the fight goes on in

    @classmethod
    def from_data(cls, data: dict) -> ExitDef:
        return cls(rect=Rect(*data["rect"]), to=data["to"])


@dataclass
class Drop:
    """A drop in play: when it falls next, and where its last wreck lies."""

    defn: DropDef
    countdown: int = 0  # steps until it lands
    spot: Vec2 | None = None  # marked while its shadow is on the floor
    turn: int = 0  # whose position it aims for next (it takes turns)
    wreck_at: Vec2 | None = None
    wreck_left: int = 0

    def __post_init__(self) -> None:
        self.countdown = self.defn.first_f

    @property
    def warning(self) -> float:
        """0 when nothing is coming, rising to 1 the moment it lands (for the view)."""
        if self.spot is None or self.defn.warning_f <= 0:
            return 0.0
        return 1.0 - self.countdown / self.defn.warning_f


@dataclass
class TrapZone:
    defn: TrapZoneDef
    rearm_left: int = 0
    sprung_left: int = 0  # frames the spikes stay up, for the view


@dataclass
class Hazards:
    """Everything the arena does on its own, for one round."""

    drops: list[Drop] = field(default_factory=list)
    zones: list[TrapZone] = field(default_factory=list)
    surfaces: tuple[SurfaceDef, ...] = ()
    exits: tuple[ExitDef, ...] = ()

    @classmethod
    def build(
        cls,
        drops: tuple[DropDef, ...] = (),
        zones: tuple[TrapZoneDef, ...] = (),
        surfaces: tuple[SurfaceDef, ...] = (),
        exits: tuple[ExitDef, ...] = (),
    ) -> Hazards:
        return cls([Drop(d) for d in drops], [TrapZone(z) for z in zones], surfaces, exits)

    def grip_at(self, pos: Vec2, style: str) -> tuple[float, float]:
        """(grip, slide) of the floor under `pos` for a body of this kit style."""
        for surface in self.surfaces:
            if surface.spare_style and surface.spare_style == style:
                continue
            if surface.rect is None or surface.rect.contains(pos):
                return surface.grip, surface.slide
        return 1.0, 1.0


def parse_hazards(data: dict) -> tuple[tuple[DropDef, ...], tuple[TrapZoneDef, ...]]:
    """The `[[drops]]` and `[[trap_zones]]` tables of a stage file."""
    drops = tuple(DropDef.from_data(d) for d in data.get("drops", []))
    zones = tuple(TrapZoneDef.from_data(z) for z in data.get("trap_zones", []))
    for drop in drops:
        if not drop.spots or drop.every_f <= drop.warning_f:
            raise ValueError("a drop needs spots, and to fall less often than it warns")
    return drops, zones


def parse_exits(data: dict) -> tuple[ExitDef, ...]:
    return tuple(ExitDef.from_data(e) for e in data.get("exits", []))


def parse_surfaces(data: dict) -> tuple[SurfaceDef, ...]:
    surfaces = tuple(SurfaceDef.from_data(s) for s in data.get("surfaces", []))
    for surface in surfaces:
        if not 0 < surface.grip <= 1:
            raise ValueError("a surface's grip is a share: above 0, at most 1")
    return surfaces
