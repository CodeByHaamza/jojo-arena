"""Each character's signature moves do what makes them unique."""

from helpers import NONE, hold, kinds, make_duel, press, run, run_until

from jojo_arena.engine.actions import InputFrame
from jojo_arena.engine.geometry import Vec2


def stand_out(match, index=0):
    frames = [NONE, NONE]
    frames[index] = press("stand")
    match.step(tuple(frames))
    run_until(match, lambda m: m.fighters[index].can_act(), 100)


def chain_names(match, button: str, steps: int = 60) -> list[str]:
    names = []
    for _ in range(steps):
        match.step((press(button), NONE))
        attack = match.fighters[0].attack
        if attack is not None and (not names or names[-1] != attack.move.name):
            names.append(attack.move.name)
    return names


def test_every_fighter_has_a_three_hit_string_without_the_stand():
    for fighter_id, length in (("jotaro_p3", 3), ("dio_p3", 3), ("polnareff", 3), ("kakyoin", 2)):
        match = make_duel(fighter_id, "mannequin_red")
        names = chain_names(match, "light")
        assert names[:length] == ["light", "light2", "light3"][:length], fighter_id


def test_jotaro_shrugs_and_star_platinum_answers():
    match = make_duel("jotaro_p3", "dio_p3", p2=(172, 100))
    match.step((press("special", move=(-1.0, 0.0)), NONE))  # Yare yare daze
    run(match, 6)
    events = run(match, 40, p2=press("light"))
    assert "counter" in kinds(events)
    assert match.fighters[1].hp < match.fighters[1].max_hp - 80


def test_jotaro_headbutt_crushes_a_guard():
    match = make_duel("jotaro_p3", "dio_p3")
    guard = hold("guard")
    match.step((NONE, guard))
    match.step((press("heavy"), guard))
    for _ in range(30):
        match.step((NONE, guard))
    assert match.fighters[1].guard_gauge < match.fighters[1].rules.guard_gauge_max * 0.5


def test_dio_leaps_onto_his_prey():
    match = make_duel("dio_p3", "jotaro_p3", p1=(100, 100), p2=(220, 100))
    events = run(match, 40, p1=press("special", move=(1.0, 0.0)))
    assert match.fighters[0].pos.x > 180
    assert "hit" in kinds(events)


def test_kakyoin_grapples_where_the_player_aims():
    match = make_duel("kakyoin", "jotaro_p3", p1=(150, 100), p2=(300, 100))
    aim = InputFrame((0.0, 1.0), press_counts={"special": 1}, cursor=(150.0, 190.0))
    match.step((aim, NONE))
    run(match, 30)
    assert match.fighters[0].pos.y > 170


def test_hierophant_tentacle_reels_the_opponent_in():
    match = make_duel("kakyoin", "jotaro_p3", p1=(150, 100), p2=(190, 100))
    stand_out(match)
    before = match.fighters[1].pos.x
    events = run(match, 40, p1=press("heavy"))
    assert "hit" in kinds(events)
    assert match.fighters[1].pos.x < before  # pulled toward Kakyoin


def test_polnareff_chariot_flashes_out_for_a_long_thrust():
    match = make_duel("polnareff", "jotaro_p3", p1=(150, 100), p2=(194, 100))
    assert match.fighters[0].stance == "base"
    events = run(match, 30, p1=press("special"))
    assert "hit" in kinds(events)  # 44 px away, without bringing the Stand out


def test_polnareff_pride_sharpens_his_blows():
    match = make_duel("polnareff", "jotaro_p3", p2=(300, 100))
    run(match, 30, p1=press("special", move=(0.0, 1.0)))
    assert match.fighters[0].buff is not None
    assert match.fighters[0].damage_dealt_mult > 1


def test_every_signature_move_is_reachable():
    """No move in a kit is dead data: each is a button, a chain link or a counter answer
    (of a move or of the pose)."""
    from jojo_arena.characters import load_roster

    for fighter in load_roster():
        kit = fighter.kit
        shared_links = {m.chain for m in kit.shared_moves.values()}
        shared_links |= {m.counter for m in kit.shared_moves.values()}
        for stance in kit.stances.values():
            # The five attack buttons, plus the two super slots: a stance may give
            # a super of its own (awakened Kars does not fight like Kars).
            reachable = {"light", "heavy", "heavy_alt", "special", "special_alt"}
            reachable |= {"hha", "gha"}
            reachable |= {kit.pose_counter} - {""}
            reachable |= shared_links - {""}  # an ultimate can chain or counter too
            for move in stance.moves.values():
                reachable |= {move.chain, move.counter} - {""}
                reachable |= {name for _, name in move.chains}  # a branching chain
            assert set(stance.moves) <= reachable, (fighter.id, set(stance.moves) - reachable)


def test_grapple_falls_back_on_the_held_direction_without_a_mouse():
    match = make_duel("kakyoin", "jotaro_p3", p1=(150, 100), p2=(300, 100))
    match.step((press("special", move=(0.0, 1.0)), NONE))
    run(match, 30)
    assert match.fighters[0].pos.y > 160
    assert match.fighters[0].pos.x == Vec2(150, 0).x


def test_dio_throws_a_dozen_knives_with_the_world():
    match = make_duel("dio_p3", "jotaro_p3", p2=(330, 100))
    stand_out(match)
    run(match, 20, p1=press("special", move=(1.0, 0.0)))
    knives = [p for p in match.projectiles if p.defn.look == "knife"]
    assert len(knives) == 12
    assert len({round(p.velocity.angle(), 3) for p in knives}) == 12  # no two overlap


def test_a_direction_with_heavy_is_a_running_attack():
    for fighter_id in ("jotaro_p3", "dio_p3", "kakyoin", "polnareff"):
        match = make_duel(fighter_id, "mannequin_red", p2=(300, 100))
        match.step((press("heavy", move=(1.0, 0.0)), NONE))
        assert match.fighters[0].attack.move.name == "heavy_alt", fighter_id


def test_a_blow_that_lands_cancels_into_a_super():
    match = make_duel("jotaro_p3", "mannequin_red")
    jotaro = match.fighters[0]
    jotaro.hh = 100
    names = []
    for i in range(30):
        frame = press("light") if i == 0 else (press("heart_heat") if i == 6 else NONE)
        match.step((frame, NONE))
        if jotaro.attack is not None and (not names or names[-1] != jotaro.attack.move.name):
            names.append(jotaro.attack.move.name)
    assert names[:2] == ["light", "hha"]


def test_a_blow_that_lands_cancels_into_a_dash():
    match = make_duel("jotaro_p3", "mannequin_red")
    jotaro = match.fighters[0]
    for i in range(12):
        frame = press("light") if i == 0 else (press("dash", move=(0.0, 1.0)) if i == 6 else NONE)
        match.step((frame, NONE))
    assert jotaro.state.name == "DASH"


def test_kakyoin_tentacles_burst_from_the_ground_under_the_opponent():
    match = make_duel("kakyoin", "jotaro_p3", p1=(100, 100), p2=(200, 100))
    stand_out(match)
    events = run(match, 40, p1=press("heavy", move=(1.0, 0.0)))
    assert match.fighters[0].pos.x < 110  # Kakyoin stayed back...
    assert "hit" in kinds(events)  # ...and the ground struck 100 px away
