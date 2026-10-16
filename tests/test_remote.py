"""Remote control of a long-range Stand (GDD "Mode contrôle"): Hierophant Green."""

from helpers import NONE, hold, kinds, make_duel, press, run

from jojo_arena.combat.fighter import State
from jojo_arena.engine.actions import InputFrame


def take_control(match, index=0):
    """Hold the Stand key until the Stand leaves its user."""
    frames = [NONE, NONE]
    for i in range(80):
        frames[index] = InputFrame(
            held=frozenset({"stand"}), press_counts={"stand": 1} if i == 0 else {}
        )
        match.step(tuple(frames))
        if match.fighters[index].remote:
            break
    frames[index] = NONE
    match.step(tuple(frames))
    assert match.fighters[index].remote


def steer(match, direction, frames, index=0):
    move = [NONE, NONE]
    move[index] = InputFrame(direction)
    for _ in range(frames):
        match.step(tuple(move))


def test_holding_the_stand_key_sends_hierophant_off():
    match = make_duel("kakyoin", "jotaro_p3", p1=(100, 100), p2=(330, 100))
    kakyoin = match.fighters[0]
    take_control(match)
    assert kakyoin.stance == "remote"
    start = kakyoin.pos.copy()
    steer(match, (1.0, 0.0), 40)
    assert kakyoin.pos == start  # Kakyoin stands still...
    assert kakyoin.remote_pos.x > start.x + 60  # ...Hierophant goes


def test_hierophant_stays_within_its_range():
    match = make_duel("kakyoin", "jotaro_p3", p1=(100, 100), p2=(330, 160))
    kakyoin = match.fighters[0]
    take_control(match)
    steer(match, (1.0, 0.0), 200)
    reach = kakyoin.style.params["remote_range"]
    assert kakyoin.remote_pos.distance_to(kakyoin.pos) <= reach + 0.01


def test_blows_come_from_hierophant():
    match = make_duel("kakyoin", "jotaro_p3", p1=(100, 100), p2=(260, 100))
    take_control(match)
    steer(match, (1.0, 0.0), 50)  # Hierophant now close to Jotaro, Kakyoin far
    events = run(match, 30, p1=press("light"))
    assert "hit" in kinds(events)


def test_a_hit_on_kakyoin_snaps_hierophant_back_and_stuns_him():
    match = make_duel("kakyoin", "jotaro_p3", p1=(100, 100), p2=(124, 100))
    kakyoin = match.fighters[0]
    take_control(match)
    run(match, 20, p2=press("light"))
    assert not kakyoin.remote and kakyoin.stance == "stand"
    assert kakyoin.state == State.HITSTUN
    assert kakyoin.stun_f >= kakyoin.rules.remote_break_stun_f - 20


def test_pressing_the_stand_key_calls_hierophant_back():
    match = make_duel("kakyoin", "jotaro_p3", p1=(100, 100), p2=(330, 100))
    take_control(match)
    events = run(match, 3, p1=press("stand"))
    assert not match.fighters[0].remote and "remote_end" in kinds(events)


def test_possession_steers_the_opponent():
    match = make_duel("kakyoin", "jotaro_p3", p1=(100, 100), p2=(250, 100))
    kakyoin, jotaro = match.fighters
    take_control(match)
    steer(match, (1.0, 0.0), 48)  # Hierophant right next to Jotaro
    events = run(match, 30, p1=press("heavy"))
    assert "possessed" in kinds(events)
    assert jotaro.possessed_f > 0
    start = jotaro.pos.copy()
    for _ in range(30):  # Kakyoin pushes up; Jotaro tries to attack and walk away
        match.step((InputFrame((0.0, -1.0)), press("light", move=(1.0, 0.0))))
    assert jotaro.pos.y < start.y - 15  # he walked where Kakyoin wanted
    assert jotaro.state != State.ATTACK
    run(match, 120)
    assert jotaro.possessed_f == 0  # it wears off


def test_possession_is_unblockable():
    match = make_duel("kakyoin", "jotaro_p3", p1=(100, 100), p2=(250, 100))
    take_control(match)
    steer(match, (1.0, 0.0), 48)
    guard = hold("guard")
    events = []
    events += match.step((press("heavy"), guard))
    for _ in range(30):
        events += match.step((NONE, guard))
    assert "possessed" in kinds(events)


def test_other_characters_have_no_remote_control():
    match = make_duel("jotaro_p3", "kakyoin")
    for i in range(60):
        frame = InputFrame(held=frozenset({"stand"}), press_counts={"stand": 1} if i == 0 else {})
        match.step((frame, NONE))
    assert not match.fighters[0].remote
