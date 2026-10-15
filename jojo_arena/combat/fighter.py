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
    GUARD = "guard"
    BLOCKSTUN = "blockstun"
    GUARD_BROKEN = "guard_broken"
    DASH = "dash"
    HITSTUN = "hitstun"
    KO = "ko"


ACTIONABLE = frozenset({State.IDLE, State.WALK})
GUARDING = frozenset({State.GUARD, State.BLOCKSTUN})
BUFFERED_ACTIONS = (*ATTACK_SLOTS, "dash")


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
        self.guard_gauge = rules.guard_gauge_max
        self.guard_regen_wait = 0
        self.guard_held = False
        self.dash_dir = Vec2()
        self.evaded = False  # this dash already earned a Stylish Evade

    # Queries ----------------------------------------------------------------------------

    @property
    def alive(self) -> bool:
        return self.state != State.KO

    def can_act(self) -> bool:
        return self.state in ACTIONABLE

    @property
    def invincible(self) -> bool:
        return self.state == State.DASH and self.state_f < self.rules.dash_invincible_f

    def in_stylish_window(self) -> bool:
        return (
            self.state == State.DASH
            and self.state_f < self.rules.stylish_window_f
            and not self.evaded
        )

    def guards_against(self, source: Vec2) -> bool:
        """True if guarding and `source` is inside the guarded front arc."""
        if self.state not in GUARDING:
            return False
        to_source = (source - self.pos).normalized()
        if not to_source.length_sq():
            return True
        return to_source.dot(self.facing) >= self.rules.guard_arc_cos - 1e-9

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
        for action in BUFFERED_ACTIONS:
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
        self.guard_held = frame.is_held("guard")
        if self.state == State.ATTACK and self.attack and self.attack.connected:
            slot = self._take_buffered(self.attack.move.cancel_on_hit)
            if slot and (move := self.kit.move(self.stance, slot)):
                self.start_attack(move, target)
            return
        if self.state == State.GUARD:
            self.facing = self.aim_at(target)
            if self._try_dash(frame, target) or self._try_attack(target):
                return
            if not self.guard_held:
                self.set_state(State.IDLE)
            return
        if not self.can_act():
            return
        if self._try_dash(frame, target) or self._try_attack(target):
            return
        if self.guard_held:
            self.facing = self.aim_at(target)
            self.set_state(State.GUARD)
            return
        move_dir = Vec2(*frame.move)
        if move_dir.length_sq():
            self.walk_dir = move_dir
            self.facing = move_dir
            if self.state != State.WALK:
                self.set_state(State.WALK)
        elif self.state != State.IDLE:
            self.set_state(State.IDLE)

    def _try_attack(self, target: Vec2) -> bool:
        slot = self._take_buffered(ATTACK_SLOTS)
        if slot and (move := self.kit.move(self.stance, slot)):
            self.start_attack(move, target)
            return True
        return False

    def _try_dash(self, frame: InputFrame, target: Vec2) -> bool:
        if self._take_buffered(("dash",)) is None:
            return False
        direction = Vec2(*frame.move)
        if direction.length_sq():
            self.facing = direction
        else:
            # No direction: step back, still looking at the opponent.
            self.facing = self.aim_at(target)
            direction = -self.facing
        self.dash_dir = direction.normalized()
        self.evaded = False
        self.set_state(State.DASH)
        return True

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
        elif self.state == State.DASH and self.state_f < self.rules.dash_duration_f:
            step = self.dash_dir * self.rules.dash_speed
            self.pos, _, _ = arena.constrain(self.pos + step, radius)
        elif self.walk_dir.length_sq():
            self.pos, _, _ = arena.constrain(self.pos + self.walk_dir * self.walk_speed(), radius)
        return events

    def advance(self) -> None:
        """End-of-step timers."""
        self.state_f += 1
        rules = self.rules
        if self.state == State.ATTACK and self.attack is not None:
            self.attack.frame += 1
            if self.attack.done:
                self.set_state(State.IDLE)
        elif self.state == State.DASH:
            if self.state_f >= rules.dash_duration_f + rules.dash_recovery_f:
                self.set_state(State.IDLE)
        elif self.state in (State.HITSTUN, State.BLOCKSTUN, State.GUARD_BROKEN):
            self.stun_f -= 1
            if self.stun_f <= 0:
                if self.state == State.GUARD_BROKEN:
                    self.guard_gauge = rules.guard_gauge_max
                self.wall_bounce_armed = False
                blocking = self.state == State.BLOCKSTUN and self.guard_held
                self.set_state(State.GUARD if blocking else State.IDLE)
        if self.state not in GUARDING:
            if self.guard_regen_wait > 0:
                self.guard_regen_wait -= 1
            else:
                self.guard_gauge = min(
                    rules.guard_gauge_max, self.guard_gauge + rules.guard_regen_per_f
                )

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

    def take_block(self, chip: int, gauge_damage: float, blockstun_f: int, pushback: Vec2) -> bool:
        """Absorb a blocked hit. Returns True when it breaks the guard."""
        self.velocity = pushback
        self.guard_regen_wait = self.rules.guard_regen_delay_f
        self.guard_gauge = max(0.0, self.guard_gauge - gauge_damage)
        self.hurt(chip)
        if self.state == State.KO:
            return False
        if self.guard_gauge <= 0:
            self.stun_f = self.rules.guard_break_stun_f
            self.set_state(State.GUARD_BROKEN)
            return True
        self.stun_f = blockstun_f
        self.set_state(State.BLOCKSTUN)
        return False
