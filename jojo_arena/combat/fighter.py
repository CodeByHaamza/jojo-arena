"""One combatant: state machine, movement and how it reacts to hits."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum

from jojo_arena.combat.arena import Arena
from jojo_arena.combat.events import Event
from jojo_arena.combat.kit import ATTACK_SLOTS, BuffDef, Kit, MoveDef
from jojo_arena.combat.rules import HZ, Rules
from jojo_arena.combat.styles import make_style
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
    POSE = "pose"
    SWITCH = "switch"  # changing stance (bringing the Stand out or back)
    BREATHE = "breathe"  # Hamon breathing: filling the gauge, standing still
    CLASH = "clash"
    HITSTUN = "hitstun"
    KO = "ko"


ACTIONABLE = frozenset({State.IDLE, State.WALK})
GUARDING = frozenset({State.GUARD, State.BLOCKSTUN})
# "guard" is buffered only for Flash Cancel; holding it is read directly.
BUFFERED_ACTIONS = (*ATTACK_SLOTS, "dash", "heart_heat", "stand", "guard")
SUPER_MOVES = ("hha", "gha")


@dataclass
class Attack:
    """One use of a move, from its first startup frame to its last recovery frame."""

    move: MoveDef
    aim: Vec2
    serial: int
    target: Vec2 = field(default_factory=Vec2)  # where the opponent stood at the start
    frame: int = 0
    connected: bool = False
    hits_done: int = 0
    fired: bool = False  # projectile or trap already released (every volley)
    volleys: int = 0  # projectile volleys thrown so far
    stopped_time: bool = False  # time stop already triggered
    props_hit: set[int] = field(default_factory=set)
    slot: str = ""  # the button that started it (chains continue on the same button)
    start: Vec2 = field(default_factory=Vec2)  # where the user stood at the start
    dest: Vec2 | None = None  # where a leap lands
    armor_used: int = 0
    countered: bool = False  # caught by a counter: this blow is spent
    cutscene_done: bool = False
    hamon: bool = False  # carries Hamon (burns vampires and Pillar Men)
    boost: float = 1.0  # damage multiplier: a Hamon-boosted move hits harder

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
    def active_offset(self) -> int:
        """Frames since the move became active (negative while still in startup)."""
        return self.frame - self.move.startup_f

    @property
    def done(self) -> bool:
        return self.frame >= self.move.total_f

    @property
    def last_hit(self) -> bool:
        """The next hit to land is the final one of the move."""
        return self.hits_done + 1 >= self.move.hits


@dataclass
class PendingHit:
    """A hit taken in stopped time: the damage is dealt, the impact waits for time to move."""

    hitstun_f: int
    knockback: Vec2
    wall_bounce: bool


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
        self.min_hp = 0  # training with infinite life keeps it at 1 or more
        self.base_stance = next(iter(kit.stances))
        self.stance = self.base_stance
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
        self.hh = 0.0  # Heart Heat gauge
        self.hamon = rules.hamon_start if kit.style == "hamon" else 0.0
        self.blood = rules.blood_start if kit.style == "vampire" else 0.0
        self.regen_wait = 0  # vampires: steps before their wounds start to close
        self._regen_left = 0.0
        self._sun_left = 0.0
        self.iced_f = 0  # frozen solid by Vaporization Freezing (for the view)
        self._pose_heal_left = 0.0
        self.in_sun = False
        self.style = make_style(kit.style, kit.style_params)
        self.switch_target = self.stance
        self.resolve_announced = False
        self.cooldowns: dict[MoveDef, int] = {}
        self.disarmed_f = 0
        self.buff: BuffDef | None = None
        self.buff_f = 0
        self.frozen = False  # caught in someone else's stopped time
        self.pending_hits: list[PendingHit] = []
        self.cursor: Vec2 | None = None  # where the player aims (mouse), if anywhere
        # Remote control: the Stand away from its user, steered by the player.
        self.remote_pos: Vec2 | None = None
        self.remote_dir = Vec2()
        self.stand_hold_f = 0
        self.carrying: int | None = None  # index of the arena prop held overhead
        # Possessed: someone else steers this fighter's walk for a while.
        self.possessed_f = 0
        self.possessor: int | None = None
        # Combo scaling: moves landed in a row on this fighter, and the last one's id.
        self.combo_moves = 0
        self.combo_key: tuple | None = None
        # The button of the last attack, and of the one before (a pose counter predicts
        # that the opponent does the same thing again).
        self.last_slot = "light"
        self.prev_slot = ""

    # Queries ----------------------------------------------------------------------------

    @property
    def alive(self) -> bool:
        return self.state != State.KO

    def can_act(self) -> bool:
        return self.state in ACTIONABLE

    @property
    def invincible(self) -> bool:
        if self.state == State.DASH:
            return self.state_f < self.rules.dash_invincible_f
        if self.state == State.ATTACK and self.attack is not None:
            return self.attack.frame < self.attack.move.invincible_f
        return False

    @property
    def in_resolve(self) -> bool:
        """Résolution: low on life, hits harder and takes no chip damage."""
        return 0 < self.hp < self.max_hp * self.rules.resolve_threshold

    @property
    def breathing(self) -> bool:
        return self.state == State.BREATHE

    @property
    def aura_active(self) -> bool:
        return self.style.aura_active(self)

    @property
    def stand_out(self) -> bool:
        """The Stand is out with a body that can be hit (style setting `stand_body`)."""
        return self.aura_active and bool(self.style.params.get("stand_body"))

    @property
    def remote(self) -> bool:
        """The Stand is away, under remote control."""
        return self.remote_pos is not None

    def strike_origin(self) -> Vec2:
        """Where this fighter's blows and shots come from: the Stand when it is away."""
        return self.remote_pos if self.remote_pos is not None else self.pos

    def stand_spot(self) -> Vec2:
        """Where the Stand floats: in front of its user to strike, just behind otherwise,
        or wherever the player sent it."""
        if self.remote_pos is not None:
            return self.remote_pos
        if self.state in (State.ATTACK, State.CLASH):
            return self.pos + self.facing * self.rules.stand_front
        beside = Vec2(-self.facing.y, self.facing.x)
        return self.pos - self.facing * self.rules.stand_back + beside * self.rules.stand_side

    def stand_pos(self) -> Vec2 | None:
        """The Stand's position while it is out with a body, else None."""
        return self.stand_spot() if self.stand_out else None

    def hurtboxes(self) -> list[tuple[Vec2, float]]:
        """Circles where this fighter can be hit: the body, and the Stand while it is out."""
        boxes = [(self.pos, self.rules.hurt_radius)]
        stand = self.stand_pos()
        if stand is not None:
            boxes.append((stand, self.rules.stand_hurt_radius))
        return boxes

    @property
    def damage_dealt_mult(self) -> float:
        return self.buff.damage_dealt_mult if self.buff else 1.0

    @property
    def damage_taken_mult(self) -> float:
        return self.buff.damage_taken_mult if self.buff else 1.0

    def gain_hh(self, amount: float) -> None:
        self.hh = min(self.rules.hh_max, self.hh + amount)

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
        speed = base * self.kit.stances[self.stance].walk_speed_mult
        speed = speed * (self.buff.speed_mult if self.buff else 1.0)
        if self.carrying is not None:
            speed *= self.rules.carry_speed_mult  # a prop over the head
        return speed

    def aim_at(self, target: Vec2) -> Vec2:
        direction = (target - self.strike_origin()).normalized()
        return direction if direction.length_sq() else self.facing

    def hitboxes(self) -> list[tuple[Vec2, float]]:
        """Ground-plane circles of the current attack, while it can hit.

        One circle at `reach`; for "line" moves (a finger, a tentacle, a blade), a row of
        circles from the body out to `reach`, so there is no blind spot up close.
        """
        if self.frozen or self.attack is None or not self.attack.active:
            return []
        if self.attack.connected or self.attack.countered:
            return []
        move = self.attack.move
        if move.radius <= 0:
            return []
        if move.at_target:
            return [(self.attack.target, move.radius)]
        aim, origin = self.attack.aim, self.strike_origin()
        if move.shape == "line":
            count = max(1, math.ceil(move.reach / move.radius))
            step = move.reach / count
            return [(origin + aim * (step * (i + 1)), move.radius) for i in range(count)]
        return [(origin + aim * move.reach, move.radius)]

    def move_for(self, slot: str, frame: InputFrame | None = None) -> MoveDef | None:
        """The move an input starts now: depends on stance, disarm, held direction and
        cooldowns. None if nothing can come out."""
        stance = self.stance
        if self.disarmed_f > 0 and slot in ATTACK_SLOTS:
            stance = self.base_stance  # the Stand's weapon is gone for a moment
        move = None
        if slot in ("special", "heavy") and frame is not None and frame.move != (0.0, 0.0):
            # With a direction held: the variant of the move (special_alt, heavy_alt).
            move = self.kit.stances[stance].moves.get(f"{slot}_alt")
        move = move or self.kit.move(stance, slot)
        if move is not None and self.cooldowns.get(move, 0) > 0:
            return None
        if move is not None and move.blood_cost > self.blood:
            return None  # not enough blood for it
        return move

    def time_stop_ready(self) -> bool | None:
        """For the HUD: None if this kit cannot stop time, else whether it can right now."""
        moves = [m for m in self.kit.all_moves() if m.time_stop_f > 0 and m.name not in SUPER_MOVES]
        if not moves:
            return None
        return any(self.cooldowns.get(m, 0) == 0 for m in moves)

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

    def control(self, frame: InputFrame, target: Vec2) -> list[Event]:
        """Turn this step's input into actions. Only called while the fight is running."""
        self.walk_dir = Vec2()
        self.remote_dir = Vec2()
        self.guard_held = frame.is_held("guard") and not self.remote
        self.cursor = Vec2(*frame.cursor) if frame.cursor is not None else None
        remote_stance = self.style.params.get("remote")
        if remote_stance and frame.is_held("stand"):
            self.stand_hold_f += 1
            free = self.state in (State.IDLE, State.WALK, State.SWITCH)
            if self.stand_hold_f == self.rules.remote_hold_f and not self.remote and free:
                return self.enter_remote(remote_stance)
        else:
            self.stand_hold_f = 0
        if self.possessed_f > 0:
            # Steered by someone else: it walks where they push it, and nothing else.
            if self.can_act():
                move_dir = Vec2(*frame.move)
                self.walk_dir = move_dir
                if move_dir.length_sq():
                    self.facing = move_dir
                self.set_state(State.WALK if move_dir.length_sq() else State.IDLE)
            return []
        if self.state == State.ATTACK and self.attack is not None:
            if self._try_flash_cancel():
                return [Event("flash_cancel", self.pos, self.index)]
            if self.attack.connected:
                attack = self.attack
                if attack.move.name not in SUPER_MOVES:
                    # Super cancel: a blow that lands goes straight into a Heart Heat attack.
                    events = self._try_super(frame, target)
                    if events is not None:
                        return events
                    dash_ok = self.rules.dash_cancel_on_hit and attack.move.hits <= 1
                    if dash_ok and self._try_dash(frame, target):
                        return []
                slot = self._take_buffered(attack.move.cancel_on_hit)
                move = None
                if slot and slot == attack.slot and attack.move.chain:
                    move = self.kit.move(self.stance, attack.move.chain)
                elif slot:
                    move = self.move_for(slot, frame)
                if move is not None:
                    self.start_attack(move, target, slot, frame)
            return []
        if self.state == State.POSE:
            if frame.is_held("pose"):
                return []
            self.set_state(State.IDLE)
        if self.state == State.BREATHE:
            if frame.is_held("stand"):
                gain = self.rules.hamon_breath_per_f
                if self.in_sun:
                    gain *= self.rules.sun_hamon_mult
                self.hamon = min(self.rules.hamon_max, self.hamon + gain)
                return []
            self.set_state(State.IDLE)
        if self.state == State.GUARD:
            self.facing = self.aim_at(target)
            events = self._try_actions(frame, target)
            if events is None and not self.guard_held:
                self.set_state(State.IDLE)
            return events or []
        if not self.can_act():
            return []
        events = self._try_actions(frame, target)
        if events is not None:
            return events
        move_dir = Vec2(*frame.move)
        if self.remote:
            # The user stands still, defenseless; the direction steers the Stand.
            self.remote_dir = move_dir
            if self.state != State.IDLE:
                self.set_state(State.IDLE)
            return []
        if self.guard_held:
            self.facing = self.aim_at(target)
            self.set_state(State.GUARD)
            return []
        if frame.is_held("pose"):
            self.set_state(State.POSE)
            return []
        if move_dir.length_sq():
            self.walk_dir = move_dir
            self.facing = move_dir
            if self.state != State.WALK:
                self.set_state(State.WALK)
        elif self.state != State.IDLE:
            self.set_state(State.IDLE)
        return []

    def _try_actions(self, frame: InputFrame, target: Vec2) -> list[Event] | None:
        """Buffered actions possible from neutral or guard, by priority.

        Returns the events of the action started, or None if nothing started.
        """
        if self.remote:
            # Away, the Stand can only strike, or come back.
            if self._try_attack(frame, target):
                return []
            if self._take_buffered(("stand",)) and self.style.on_pressed(self):
                return [Event("remote_end", self.pos, self.index)]
            return None
        if self._try_dash(frame, target):
            return []
        events = self._try_super(frame, target)
        if events is not None:
            return events
        if self._try_attack(frame, target):
            return []
        if self._take_buffered(("stand",)) and self.style.on_pressed(self):
            return [Event(self.style.event, self.pos, self.index)]
        return None

    def _try_super(self, frame: InputFrame, target: Vec2) -> list[Event] | None:
        """The Heart Heat key alone: Heart Heat Attack (1 bar). With a direction held:
        Great Heat Attack (2 bars), or the HHA if there is only one bar."""
        if "heart_heat" not in self.buffer:
            return None
        supers = [("hha", self.rules.hha_cost)]
        if frame.move != (0.0, 0.0):
            supers.insert(0, ("gha", self.rules.gha_cost))
        for slot, cost in supers:
            move = self.kit.move(self.stance, slot)
            if move is not None and self.hh >= cost:
                del self.buffer["heart_heat"]
                self.hh -= cost
                self.start_attack(move, target)
                return [Event(slot, self.pos, self.index)]
        return None

    def _try_flash_cancel(self) -> bool:
        """Spend half a bar to drop the current attack instantly (combos, feints)."""
        if "guard" not in self.buffer or self.attack.move.name in SUPER_MOVES:
            return False
        if self.hh < self.rules.flash_cancel_cost:
            return False
        del self.buffer["guard"]
        self.hh -= self.rules.flash_cancel_cost
        self.set_state(State.IDLE)
        return True

    def enter_clash(self, facing: Vec2) -> None:
        self.velocity = Vec2()
        self.buffer.clear()
        self.facing = facing
        self.set_state(State.CLASH)

    def begin_stance_switch(self, target: str) -> None:
        self.switch_target = target
        self.set_state(State.SWITCH)

    def _try_attack(self, frame: InputFrame, target: Vec2) -> bool:
        for slot in ATTACK_SLOTS:
            if slot in self.buffer and (move := self.move_for(slot, frame)):
                del self.buffer[slot]
                self.start_attack(move, target, slot, frame)
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

    def start_attack(
        self, move: MoveDef, target: Vec2, slot: str = "", frame: InputFrame | None = None
    ) -> None:
        # A guard press made before the attack must not Flash Cancel it right away.
        self.buffer.pop("guard", None)
        aim = self.aim_at(target)
        dest = None
        if move.leap > 0:
            dest = self._leap_destination(move, target, frame)
            if (dest - self.pos).length_sq() > 1:
                aim = (dest - self.pos).normalized()
        self.facing = aim
        self._serial += 1
        if slot:
            self.prev_slot, self.last_slot = self.last_slot, slot
        self.set_state(State.ATTACK)
        self.attack = Attack(
            move, aim, self._serial, target=target.copy(), slot=slot, start=self.pos.copy()
        )
        self.attack.dest = dest
        self.attack.hamon = move.hamon
        self.blood = max(0.0, self.blood - move.blood_cost)
        if move.hamon_cost and self.hamon >= move.hamon_cost:
            # Enough Hamon: the move spends it and strikes harder. Without, it stays normal.
            self.hamon -= move.hamon_cost
            self.attack.hamon = True
            self.attack.boost = move.hamon_mult or self.rules.hamon_boost_mult
        if move.cooldown_f:
            self.cooldowns[move] = move.cooldown_f
        if move.buff:
            self.buff = self.kit.buffs[move.buff]
            self.buff_f = self.buff.duration_f

    def feed(self, life_drained: int) -> None:
        """A vampire drinks: the life drained fills its blood gauge."""
        if self.kit.style == "vampire":
            self.blood = min(
                self.rules.blood_max, self.blood + life_drained * self.rules.blood_per_drain
            )

    def burn_in_sun(self) -> bool:
        """One step of sunlight on an undead body: the blood boils away, then the sun
        burns. Returns True when this step's burn knocked the fighter out."""
        rules = self.rules
        if self.blood > 0:
            self.blood = max(0.0, self.blood - rules.sun_blood_per_f)
            return False
        self._sun_left += rules.sun_damage_per_f
        whole = int(self._sun_left)
        if whole:
            self._sun_left -= whole
            alive = self.alive
            self.hurt(whole)
            return alive and not self.alive
        return False

    def _vampire_step(self) -> None:
        """The freezing stance burns blood; untouched, the wounds close on blood."""
        rules = self.rules
        on = self.style.params.get("on")
        if on and self.stance == on:
            self.blood = max(0.0, self.blood - rules.vampire_stance_blood_per_f)
            if self.blood == 0 and self.can_act():
                self.begin_stance_switch(self.base_stance)  # dry: back to normal
        if self.regen_wait > 0:
            self.regen_wait -= 1
            return
        if self.hp >= self.max_hp or self.state in (State.HITSTUN, State.GUARD_BROKEN):
            return
        self._regen_left = min(1.0, self._regen_left + rules.vampire_regen_per_f)
        affordable = int(self.blood / rules.regen_blood_per_hp)
        whole = min(int(self._regen_left), self.max_hp - self.hp, affordable)
        if whole > 0:
            self.hp += whole
            self._regen_left -= whole
            self.blood -= whole * rules.regen_blood_per_hp

    def begin_breath(self) -> None:
        """Hamon breathing starts; it lasts while the style key is held."""
        self.set_state(State.BREATHE)

    def enter_remote(self, stance: str) -> list[Event]:
        """The Stand leaves its user's side: the player now steers it."""
        spot = self.pos + self.facing * self.rules.stand_front
        self.stance = stance
        self.remote_pos = spot
        self.buffer.pop("stand", None)
        self.set_state(State.IDLE)
        return [Event("remote_start", spot, self.index)]

    def leave_remote(self) -> None:
        """The Stand snaps back to its user's side."""
        self.remote_pos = None
        self.stance = self.style.params.get("on", self.stance)

    def _leap_destination(self, move: MoveDef, target: Vec2, frame: InputFrame | None) -> Vec2:
        """Where a leap lands: next to the opponent, or on the aimed point (mouse, right
        stick, else the held direction, else straight ahead), at most `leap` away."""
        if move.leap_to == "cursor":
            if frame is not None and frame.cursor is not None:
                point = Vec2(*frame.cursor)
            elif frame is not None and frame.stick is not None:
                point = self.pos + Vec2(*frame.stick).normalized() * move.leap
            elif frame is not None and frame.move != (0.0, 0.0):
                point = self.pos + Vec2(*frame.move).normalized() * move.leap
            else:
                point = self.pos + self.facing * move.leap
        else:
            offset = target - self.pos
            gap = self.rules.body_radius * 2
            point = target - offset.normalized() * gap if offset.length() > gap else self.pos
        delta = point - self.pos
        if delta.length() > move.leap:
            delta = delta.normalized() * move.leap
        return self.pos + delta

    def _leaping(self) -> bool:
        attack = self.attack
        return (
            self.state == State.ATTACK
            and attack is not None
            and attack.dest is not None
            and attack.phase == 0
        )

    @property
    def countering(self) -> bool:
        """In the window of a counter move: the next blow is caught and answered. A kit
        with a pose counter also catches it after posing a moment ("your next line is...")."""
        if self.frozen:
            return False
        if self.state == State.POSE and self.kit.pose_counter:
            return self.state_f >= self.kit.pose_counter_ready_f
        attack = self.attack
        return (
            self.state == State.ATTACK
            and attack is not None
            and bool(attack.move.counter)
            and attack.active
        )

    def armored(self) -> bool:
        attack = self.attack
        return (
            self.state == State.ATTACK
            and attack is not None
            and attack.phase < 2
            and attack.armor_used < attack.move.armor
        )

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
        elif self._leaping():
            attack = self.attack
            t = min(1.0, (attack.frame + 1) / max(1, attack.move.startup_f))
            self.pos, _, _ = arena.constrain(
                attack.start + (attack.dest - attack.start) * t, radius
            )
        elif self._lunging():
            step = self.attack.aim * self.attack.move.lunge
            self.pos, _, _ = arena.constrain(self.pos + step, radius)
        elif self.walk_dir.length_sq():
            self.pos, _, _ = arena.constrain(self.pos + self.walk_dir * self.walk_speed(), radius)
        if self.remote_pos is not None and self.remote_dir.length_sq():
            # The Stand flies where it is steered, within its range of its user.
            speed = self.style.params.get("remote_speed", 150) / HZ
            spot = self.remote_pos + self.remote_dir * speed
            leash = spot - self.pos
            reach = self.style.params.get("remote_range", 140)
            if leash.length() > reach:
                spot = self.pos + leash.normalized() * reach
            self.remote_pos, _, _ = arena.constrain(spot, self.rules.stand_hurt_radius)
        return events

    def _lunging(self) -> bool:
        """Moves with a lunge carry the body forward until they first connect; rushes
        keep pushing forward through every hit, driving the opponent back. A negative
        lunge carries it backward (a retreat)."""
        attack = self.attack
        return (
            self.state == State.ATTACK
            and attack is not None
            and attack.move.lunge != 0
            and attack.phase < 2
            and (attack.hits_done == 0 or attack.move.hits > 1)
        )

    @property
    def rushing(self) -> bool:
        """Starting or throwing a rush (a multi-hit barrage)."""
        attack = self.attack
        return (
            self.state == State.ATTACK
            and attack is not None
            and attack.move.hits > 1
            and attack.phase < 2
            and not self.frozen
        )

    def advance(self) -> None:
        """End-of-step timers."""
        self.state_f += 1
        rules = self.rules
        if self.state not in (State.HITSTUN, State.GUARD_BROKEN) and not self.pending_hits:
            self.combo_moves, self.combo_key = 0, None  # out of the combo: it starts over
        if self.state == State.ATTACK and self.attack is not None:
            self.attack.frame += 1
            attack, move = self.attack, self.attack.move
            # Rushes: the hitbox re-arms at a steady beat until all hits are used.
            if (
                attack.connected
                and attack.active
                and attack.hits_done < move.hits
                and move.hit_every_f
                and attack.active_offset % move.hit_every_f == 0
            ):
                attack.connected = False
            if attack.done:
                self.set_state(State.IDLE)
        elif self.state == State.DASH:
            if self.state_f >= rules.dash_duration_f + rules.dash_recovery_f:
                self.set_state(State.IDLE)
        elif self.state == State.SWITCH:
            if self.state_f >= rules.stance_switch_f:
                self.stance = self.switch_target
                self.set_state(State.IDLE)
        elif self.state == State.POSE:
            self.gain_hh(rules.hh_pose_per_f)
            if self.kit.pose_heal_per_s and self.alive:
                # A cheer that lifts the spirits: posing heals a little.
                self._pose_heal_left += self.kit.pose_heal_per_s / HZ
                whole = int(self._pose_heal_left)
                if whole:
                    self._pose_heal_left -= whole
                    self.hp = min(self.max_hp, self.hp + whole)
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
        for move in [m for m, left in self.cooldowns.items() if left > 0]:
            self.cooldowns[move] -= 1
        if self.possessed_f > 0:
            self.possessed_f -= 1
            if self.possessed_f == 0:
                self.possessor = None
        if self.disarmed_f > 0:
            self.disarmed_f -= 1
        if self.buff is not None and self.buff.heal_per_s and self.alive:
            self._pose_heal_left += self.buff.heal_per_s / HZ
            whole = int(self._pose_heal_left)
            if whole:
                self._pose_heal_left -= whole
                self.hp = min(self.max_hp, self.hp + whole)
        if self.buff is not None:
            self.buff_f -= 1
            if self.buff_f <= 0:
                self.buff = None
        if self.iced_f > 0:
            self.iced_f -= 1
        if self.kit.style == "vampire" and self.alive:
            self._vampire_step()

    # Taking damage ----------------------------------------------------------------------

    def hurt(self, damage: int) -> None:
        if damage > 0:
            self.regen_wait = max(self.regen_wait, self.rules.vampire_regen_delay_f)
        self.hp = max(self.min_hp, self.hp - damage)
        if self.hp == 0 and self.state != State.KO:
            self.set_state(State.KO)

    def take_hit(self, damage: int, hitstun_f: int, knockback: Vec2, wall_bounce: bool) -> bool:
        """Take a blow. Returns True when armor absorbed the impact (damage only)."""
        if self.frozen:
            # Stopped time: the damage is dealt now, the impact lands when time moves again.
            self.hurt(damage)
            self.pending_hits.append(PendingHit(hitstun_f, knockback, wall_bounce))
            return False
        if self.armored():
            self.attack.armor_used += 1
            self.hurt(damage)
            return True
        was_remote = self.remote
        if was_remote:
            self.leave_remote()  # struck: the Stand snaps back...
        self.velocity = knockback
        self.wall_bounce_armed = wall_bounce
        self.buffer.clear()
        self.hurt(damage)
        if self.state != State.KO:
            self.stun_f = hitstun_f
            if was_remote:
                self.stun_f = max(hitstun_f, self.rules.remote_break_stun_f)  # ...dazed
            self.set_state(State.HITSTUN)
        return False

    def release_pending_hits(self) -> bool:
        """Time moves again: all the hits taken in stopped time land at once."""
        if not self.pending_hits:
            return False
        hits, self.pending_hits = self.pending_hits, []
        knockback = Vec2()
        for hit in hits:
            knockback = knockback + hit.knockback
        if self.alive:
            self.take_hit(
                0,
                max(h.hitstun_f for h in hits),
                knockback,
                any(h.wall_bounce for h in hits),
            )
        else:
            self.velocity = knockback
        return True

    def take_block(self, chip: int, gauge_damage: float, blockstun_f: int, pushback: Vec2) -> bool:
        """Absorb a blocked hit. Returns True when it breaks the guard."""
        if not self.frozen:
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
