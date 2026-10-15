"""One combatant: state machine, movement and how it reacts to hits."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from jojo_arena.combat.arena import Arena
from jojo_arena.combat.events import Event
from jojo_arena.combat.kit import ATTACK_SLOTS, Kit, MoveDef
from jojo_arena.combat.rules import HZ, Rules
from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Vec2

# A press is remembered this long, so an attack pressed slightly early still comes out.
BUFFER_F = 8


class State(StrEnum):
    IDLE = "idle"
    WALK = "walk"
    ATTACK = "attack"
    HITSTUN = "hitstun"
    KO = "ko"


ACTIONABLE = frozenset({State.IDLE, State.WALK})


@dataclass
class Attack:
    """One use of a move, from its first startup frame to its last recovery frame."""

    move: MoveDef
    aim: Vec2
    serial: int
    frame: int = 0
    connected: bool = False
    fired: bool = False  # projectile already spawned
    props_hit: set[int] = field(default_factory=set)

    @property
    def phase(self) -> int:
        """0 = startup, 1 = active, 2 = recovery."""
        if self.frame < self.move.startup_f:
            return 0
        if self.frame < self.move.startup_f + self.move.active_f:
            return 1
        return 2

    def phase_info(self) -> tuple[int, int, int]:
        """(phase, frames spent in it, its length), for animation timing."""
        m = self.move
        starts = (0, m.startup_f, m.startup_f + m.active_f)
        lengths = (m.startup_f, m.active_f, m.recovery_f)
        p = self.phase
        return p, self.frame - starts[p], lengths[p]

    @property
    def active(self) -> bool:
        return self.phase == 1

    @property
    def done(self) -> bool:
        return self.frame >= self.move.total_f


class Fighter:
    def __init__(self, index: int, kit: Kit, rules: Rules, pos: Vec2, facing: Vec2) -> None:
        self.index = index
        self.kit = kit
        self.rules = rules
        self.pos = pos.copy()
        self.facing = facing.normalized()
        self.velocity = Vec2()  # knockback, decays with friction
        self.walk_dir = Vec2()
        self.max_hp = kit.max_hp
        self.hp = kit.max_hp
        self.stance = next(iter(kit.stances))
        self.state = State.IDLE
        self.state_f = 0
        self.attack: Attack | None = None
        self.stun_f = 0
        self.wall_bounce_armed = False
        self.buffer: dict[str, int] = {}
        self._serial = 0

    # Queries ----------------------------------------------------------------------------

    @property
    def alive(self) -> bool:
        return self.state != State.KO

    def can_act(self) -> bool:
        return self.state in ACTIONABLE

    def walk_speed(self) -> float:
        base = self.kit.walk_speed or self.rules.walk_speed
        return base * self.kit.stances[self.stance].walk_speed_mult

    def aim_at(self, target: Vec2) -> Vec2:
        direction = (target - self.pos).normalized()
        return direction if direction.length_sq() else self.facing

    def hitbox(self) -> tuple[Vec2, float] | None:
        """Ground-plane circle of the current attack, while it can hit."""
        if self.attack is None or not self.attack.active or self.attack.connected:
            return None
        move = self.attack.move
        if move.radius <= 0:
            return None
        return self.pos + self.attack.aim * move.reach, move.radius

    # Per-step logic ---------------------------------------------------------------------

    def set_state(self, state: State) -> None:
        self.state = state
        self.state_f = 0
        if state != State.ATTACK:
            self.attack = None

    def remember_presses(self, frame: InputFrame) -> None:
        """Called every step, even during hitstop, so no press is ever lost."""
        for action in list(self.buffer):
            self.buffer[action] -= 1
            if self.buffer[action] <= 0:
                del self.buffer[action]
        for action in ATTACK_SLOTS:
            if frame.was_pressed(action):
                self.buffer[action] = BUFFER_F

    def _take_buffered(self, actions) -> str | None:
        for action in actions:
            if action in self.buffer:
                del self.buffer[action]
                return action
        return None

    def control(self, frame: InputFrame, target: Vec2) -> None:
        """Turn this step's input into actions. Only called while the fight is running."""
        self.walk_dir = Vec2()
        if self.state == State.ATTACK and self.attack and self.attack.connected:
            slot = self._take_buffered(self.attack.move.cancel_on_hit)
            if slot and (move := self.kit.move(self.stance, slot)):
                self.start_attack(move, target)
            return
        if not self.can_act():
            return
        slot = self._take_buffered(ATTACK_SLOTS)
        if slot and (move := self.kit.move(self.stance, slot)):
            self.start_attack(move, target)
            return
        move_dir = Vec2(*frame.move)
        if move_dir.length_sq():
            self.walk_dir = move_dir
            self.facing = move_dir
            if self.state != State.WALK:
                self.set_state(State.WALK)
        elif self.state != State.IDLE:
            self.set_state(State.IDLE)

    def start_attack(self, move: MoveDef, target: Vec2) -> None:
        aim = self.aim_at(target)
        self.facing = aim
        self._serial += 1
        self.set_state(State.ATTACK)
        self.attack = Attack(move, aim, self._serial)

    def integrate(self, arena: Arena) -> list[Event]:
        """Move the body for this step and resolve walls, props and wall bounces."""
        events: list[Event] = []
        radius = self.rules.body_radius
        speed = self.velocity.length()
        if speed > 0:
            target = self.pos + self.velocity
            pos, normal, obstacle = arena.constrain(target, radius)
            # Only a real impact damages a prop, not a body sliding along it.
            if obstacle is not None and normal is not None and self.velocity.dot(normal) < -0.5:
                damage = speed * HZ * self.rules.obstacle_damage_per_speed
                if obstacle.damage(damage):
                    events.append(Event("prop_break", obstacle.rect.center))
                    pos, normal, _ = arena.constrain(target, radius)  # crash through it
                else:
                    events.append(Event("prop_hit", pos))
            if normal is not None and self.velocity.dot(normal) < 0:
                bounce = self.wall_bounce_armed and speed >= self.rules.wall_bounce_min_speed
                if bounce:
                    self.velocity = self.velocity.reflect(normal) * self.rules.wall_bounce_keep
                    self.wall_bounce_armed = False
                    events.append(Event("wall_bounce", pos, self.index))
                    if self.state == State.HITSTUN:
                        self.stun_f += self.rules.wall_bounce_stun_f
                        self.hurt(self.rules.wall_bounce_damage)
                else:
                    # Slide along the surface: drop the part of the speed going into it.
                    self.velocity = self.velocity - normal * self.velocity.dot(normal)
            self.pos = pos
            new_speed = max(0.0, self.velocity.length() - self.rules.knockback_friction)
            self.velocity = self.velocity.normalized() * new_speed
        elif self.walk_dir.length_sq():
            self.pos, _, _ = arena.constrain(self.pos + self.walk_dir * self.walk_speed(), radius)
        return events

    def advance(self) -> None:
        """End-of-step timers."""
        self.state_f += 1
        if self.state == State.ATTACK and self.attack is not None:
            self.attack.frame += 1
            if self.attack.done:
                self.set_state(State.IDLE)
        elif self.state == State.HITSTUN:
            self.stun_f -= 1
            if self.stun_f <= 0:
                self.wall_bounce_armed = False
                self.set_state(State.IDLE)

    # Taking damage ----------------------------------------------------------------------

    def hurt(self, damage: int) -> None:
        self.hp = max(0, self.hp - damage)
        if self.hp == 0 and self.state != State.KO:
            self.set_state(State.KO)

    def take_hit(self, damage: int, hitstun_f: int, knockback: Vec2, wall_bounce: bool) -> None:
        self.velocity = knockback
        self.wall_bounce_armed = wall_bounce
        self.buffer.clear()
        self.hurt(damage)
        if self.state != State.KO:
            self.stun_f = hitstun_f
            self.set_state(State.HITSTUN)
