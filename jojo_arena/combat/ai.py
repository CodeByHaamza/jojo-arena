"""The computer opponent of the "Versus the computer" and Arcade modes.

It reads the fight a few frames late (its reaction time), keeps the distance its kit
likes, guards or dodges what it sees coming, punishes moves that miss, follows its
chains when they land, and spends its gauges. Like a player, it only produces
InputFrames: it can never do what a pad could not.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.combat.kit import MoveDef
from jojo_arena.engine.actions import InputFrame, quantize_8
from jojo_arena.engine.geometry import Vec2


@dataclass(frozen=True)
class Level:
    """How well the computer plays."""

    reaction_f: int  # frames before it sees what the opponent does
    defend: float  # chance to guard or dodge an attack it sees coming
    punish: float  # chance to strike back at a move that missed
    combo: float  # chance to press again when a chain blow lands
    aggression: float  # chance per frame to attack when in range
    mash: float  # chance per frame to press a button in a rush duel
    supers: bool  # spends Heart Heat on supers


LEVELS = (
    Level(
        reaction_f=20, defend=0.15, punish=0.2, combo=0.3, aggression=0.05, mash=0.30, supers=False
    ),
    Level(
        reaction_f=12, defend=0.40, punish=0.5, combo=0.6, aggression=0.09, mash=0.45, supers=True
    ),
    Level(
        reaction_f=7, defend=0.65, punish=0.8, combo=0.85, aggression=0.13, mash=0.60, supers=True
    ),
    Level(
        reaction_f=4, defend=0.85, punish=0.95, combo=1.0, aggression=0.18, mash=0.75, supers=True
    ),
)

SLOTS = ("light", "heavy", "special")


@dataclass
class Seen:
    """What the computer saw of its opponent, some frames ago."""

    pos: Vec2
    attacking: bool
    active: bool
    recovering: bool
    vulnerable: bool
    reach: float


def move_reach(move: MoveDef) -> float:
    """How far a move threatens, in px from the user's body."""
    if move.projectile is not None or move.trap is not None or move.at_target:
        return 260.0
    if move.leap:
        return move.leap + move.radius
    if move.time_stop_f or move.buff or (move.radius == 0 and move.reach == 0):
        return 0.0  # not a blow: time stop, buff...
    return move.reach + move.radius + move.lunge * max(1, move.startup_f) * 0.5


class CpuPlayer:
    def __init__(self, level: int, seed: int = 1) -> None:
        self.level = LEVELS[max(0, min(level, len(LEVELS) - 1))]
        self.rng = random.Random(seed)
        self.memory: deque[Seen] = deque(maxlen=self.level.reaction_f + 1)
        self.guard_f = 0
        self.breath_f = 0
        self.strafe = 0.0

    # Seeing --------------------------------------------------------------------------

    def _see(self, foe: Fighter) -> Seen:
        attack = foe.attack
        attacking = foe.state == State.ATTACK and attack is not None
        reach = move_reach(attack.move) if attacking else 0.0
        return Seen(
            pos=foe.pos.copy(),
            attacking=attacking,
            active=attacking and attack.phase <= 1,
            recovering=attacking and attack.phase == 2 and not attack.connected,
            vulnerable=foe.state in (State.POSE, State.BREATHE, State.GUARD_BROKEN) or foe.remote,
            reach=reach,
        )

    def _seen(self) -> Seen:
        return self.memory[0]  # the oldest memory: what it has had time to react to

    # Choosing ------------------------------------------------------------------------

    def _best_slot(self, me: Fighter, distance: float, ranged: bool) -> tuple[str, bool] | None:
        """A button (and whether to hold a direction for the variant) whose move reaches."""
        options = []
        for slot in SLOTS:
            for variant in (False, True):
                move = self._move(me, slot, variant)
                if move is None:
                    continue
                reach = move_reach(move)
                if reach <= 0 or move.counter:
                    continue
                long = reach > 60
                if reach + 6 >= distance and (long == ranged or not ranged):
                    options.append((slot, variant, reach))
        if not options:
            return None
        slot, variant, _ = self.rng.choice(options)
        return slot, variant

    def _move(self, me: Fighter, slot: str, variant: bool) -> MoveDef | None:
        stance = me.kit.stances.get(me.stance)
        if stance is None:
            return None
        move = stance.moves.get(f"{slot}_alt") if variant else stance.moves.get(slot)
        if move is None or me.cooldowns.get(move, 0) > 0 or move.blood_cost > me.blood:
            return None
        return move

    def _likes_range(self, me: Fighter) -> float:
        """The distance the kit prefers: far for zoners, close for brawlers."""
        reaches = []
        for slot in SLOTS:
            move = self._move(me, slot, False)
            if move is not None:
                reaches.append(move_reach(move))
        far = sum(1 for r in reaches if r > 60)
        return 110.0 if far >= 2 else 26.0

    # Playing -------------------------------------------------------------------------

    def think(self, me: Fighter, foe: Fighter) -> InputFrame:
        rng, level = self.rng, self.level
        self.memory.append(self._see(foe))
        if me.state == State.CLASH:
            return InputFrame(press_counts={"light": 1} if rng.random() < level.mash else {})
        seen = self._seen()
        offset = seen.pos - me.pos
        distance = offset.length()
        toward = offset.normalized() if distance > 0 else me.facing
        presses: dict[str, int] = {}
        held: set[str] = set()
        move = (0.0, 0.0)

        # Defense: an attack coming that will reach.
        threat = seen.active and distance < seen.reach + 10
        if self.guard_f:
            self.guard_f -= 1
            return InputFrame((0.0, 0.0), frozenset({"guard"}), {})
        if threat and me.can_act() and rng.random() < level.defend:
            if rng.random() < 0.35:
                presses["dash"] = 1
                side = Vec2(-toward.y, toward.x) * rng.choice((-1, 1))
                return InputFrame(quantize_8(side.x, side.y, 0.1), frozenset(), presses)
            self.guard_f = rng.randint(14, 30)
            return InputFrame((0.0, 0.0), frozenset({"guard"}), {})

        # Chains: press again while the blow lands.
        attack = me.attack
        if attack is not None and attack.connected and attack.move.chain:
            if rng.random() < level.combo:
                presses[attack.slot or "light"] = 1
            return InputFrame((0.0, 0.0), frozenset(), presses)
        if not me.can_act() and me.state != State.BREATHE:
            return InputFrame()

        # Style: the Stand out, Hamon to breathe, blood to freeze.
        style = me.kit.style
        if self.breath_f:
            self.breath_f -= 1
            if distance > 90 and self.breath_f:
                return InputFrame((0.0, 0.0), frozenset({"stand"}), {})
            self.breath_f = 0
        if style == "hamon" and me.hamon < 40 and distance > 120 and rng.random() < 0.05:
            self.breath_f = rng.randint(40, 90)
            return InputFrame((0.0, 0.0), frozenset({"stand"}), {"stand": 1})
        stance_on = me.style.params.get("on")
        toggles = style == "stance_toggle" and stance_on and me.stance != stance_on
        if toggles and rng.random() < 0.04:
            return InputFrame(press_counts={"stand": 1})
        if style == "stance_cycle" and rng.random() < 0.012:
            # Several movesets on one key: it calls the next one in now and then, so
            # the whole kit shows up in Arcade and against the computer.
            return InputFrame(press_counts={"stand": 1})
        if style == "vampire" and me.stance != stance_on and me.blood > 50 and rng.random() < 0.01:
            return InputFrame(press_counts={"stand": 1})

        # Supers: when the opponent is open and close.
        if level.supers and me.hh >= me.rules.hha_cost and distance < 70 and rng.random() < 0.04:
            direction = toward if me.hh >= me.rules.gha_cost else Vec2()
            return InputFrame(
                quantize_8(direction.x, direction.y, 0.1), frozenset(), {"heart_heat": 1}
            )

        # Punish: a move that missed, or someone posing or breathing.
        if (seen.recovering or seen.vulnerable) and rng.random() < level.punish:
            choice = self._best_slot(me, distance, ranged=distance > 60)
            if choice is not None:
                slot, variant = choice
                presses[slot] = 1
                if variant:
                    move = (toward.x, toward.y)
                return InputFrame(quantize_8(*move, 0.1), frozenset(), presses)

        # Footsies: walk to the range the kit likes, strafing a little; strike in range.
        likes = self._likes_range(me)
        if rng.random() < 0.02:
            self.strafe = rng.choice((-0.6, 0.0, 0.0, 0.6))
        if distance > likes + 12:
            move = (toward.x - toward.y * self.strafe, toward.y + toward.x * self.strafe)
        elif distance < likes - 30 and likes > 60:
            move = (-toward.x, -toward.y)
        if rng.random() < level.aggression:
            choice = self._best_slot(me, distance, ranged=distance > 60)
            if choice is not None:
                slot, variant = choice
                presses[slot] = 1
                move = (toward.x, toward.y) if variant else (0.0, 0.0)
        if distance > 150 and rng.random() < 0.003:
            return InputFrame((0.0, 0.0), frozenset({"pose"}), {})
        return InputFrame(quantize_8(*move, 0.1), frozenset(held), presses)
