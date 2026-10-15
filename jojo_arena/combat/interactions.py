"""Special interactions between powers (GDD "Interactions spéciales").

These rules take precedence over the normal fight rules. For now: stopped time.

- Everything freezes except the one who stopped time. Hits on a frozen fighter deal
  their damage at once, but the impact (knockback, hitstun) lands when time resumes.
- Projectiles thrown in stopped time fly a short way, then hang in the air until time
  resumes.
- A time stopper caught in the other's stopped time can still move for a moment (1 s
  the first time, a bit longer each time it happens again in the match). If they stop
  time themselves meanwhile, both move freely.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from jojo_arena.combat.events import Event

if TYPE_CHECKING:
    from jojo_arena.combat.fighter import Fighter
    from jojo_arena.combat.match import Match


@dataclass
class TimeStop:
    casters: set[int]  # fighters moving freely in stopped time
    frames_left: int
    duration_f: int
    allowance: dict[int, int] = field(default_factory=dict)  # caught time stoppers
    fresh: bool = True  # started this very step: the count starts on the next one

    def frozen(self, index: int) -> bool:
        return index not in self.casters and self.allowance.get(index, 0) <= 0


def start_time_stop(match: Match, caster: Fighter, duration_f: int) -> list[Event]:
    rules = match.rules
    stop = match.time_stop
    if stop is None:
        stop = TimeStop({caster.index}, duration_f, duration_f)
        match.time_stop = stop
        other = match.opponent(caster)
        if other.kit.time_stopper:
            caught = match.time_stops_endured[other.index]
            stop.allowance[other.index] = (
                rules.time_stop_resist_first_f + rules.time_stop_resist_growth_f * caught
            )
            match.time_stops_endured[other.index] += 1
    else:
        # Time is already stopped and this one can move in it: now both move freely.
        stop.casters.add(caster.index)
        stop.frames_left = max(stop.frames_left, duration_f)
        stop.duration_f = max(stop.duration_f, stop.frames_left)
        stop.fresh = True
    match.super_freeze = max(match.super_freeze, rules.time_stop_flash_f)
    match.super_user = caster.index
    update_frozen(match)
    return [Event("time_stop", caster.pos, caster.index, duration_f)]


def update_frozen(match: Match) -> None:
    stop = match.time_stop
    for fighter in match.fighters:
        fighter.frozen = stop is not None and stop.frozen(fighter.index)


def tick_time_stop(match: Match) -> list[Event]:
    """Count stopped time down; when it ends, every delayed impact lands at once."""
    stop = match.time_stop
    if stop is None:
        return []
    if stop.fresh:
        stop.fresh = False
        return []
    stop.frames_left -= 1
    for index, left in stop.allowance.items():
        if left > 0:
            stop.allowance[index] = left - 1
    if stop.frames_left > 0:
        update_frozen(match)
        return []
    match.time_stop = None
    update_frozen(match)
    for projectile in match.projectiles:
        projectile.stop_after = None
    events = [Event("time_resume")]
    for fighter in match.fighters:
        if fighter.release_pending_hits():
            events.append(Event("delayed_hits", fighter.pos, fighter.index))
            match.hitstop = max(match.hitstop, 10)
    return events
