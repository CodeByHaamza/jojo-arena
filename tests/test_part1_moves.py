"""Part 1 movesets: Jonathan's sword and his Hamon wave, Bruford's hair in everything."""

from helpers import NONE, make_duel, press, run

from jojo_arena.characters import get_fighter
from jojo_arena.combat.rules import load_rules

RULES = load_rules()


def kit(fighter_id: str):
    return get_fighter(fighter_id).kit


def hits_on(events, defender: int):
    return [e for e in events if e.kind == "hit" and e.fighter == defender]


# Jonathan: Luck & Pluck ------------------------------------------------------------------


def test_luck_and_pluck_is_a_flurry_of_sword_thrusts():
    hha = kit("jonathan").shared_moves["hha"]
    assert hha.hits >= 5 and hha.hit_every_f > 0  # a real barrage, not one thrust
    assert hha.shape == "line" and "blade" in hha.fx  # with the sword
    assert hha.last_damage >= hha.damage * 3  # and a finisher that ends it
    assert hha.hamon  # it still burns the undead
    assert not hha.clashable  # a super never falls into a rush duel


def test_luck_and_pluck_lands_several_times_and_the_last_blow_launches():
    match = make_duel("jonathan", "dio_p1", p1=(150, 100), p2=(180, 100))
    jonathan = match.fighters[0]
    jonathan.hh = RULES.hha_cost
    events = run(match, 90, p1=press("heart_heat"))
    landed = hits_on(events, 1)
    assert len(landed) >= 5, [e.value for e in landed]
    assert landed[-1].value > landed[0].value * 2  # the thrust that ends it hits hardest


def test_the_whole_flurry_is_worth_about_as_much_as_a_single_super_blow():
    hha = kit("jonathan").shared_moves["hha"]
    total = (hha.hits - 1) * hha.damage + hha.last_damage
    assert 170 <= total <= 210, total  # in line with the other one-bar supers


# Jonathan: Scarlet Overdrive -------------------------------------------------------------


def test_scarlet_overdrive_sends_a_wave_along_the_floor():
    move = kit("jonathan").move("base", "special")
    assert move.projectile is not None, "it has to reach across the arena now"
    assert move.projectile.look == "wave"
    assert move.radius > 0  # the fist that starts it still hits what is right there
    assert move.guard_damage > 1  # and it still caves a guard in


def test_the_wave_crosses_the_arena_and_hits_from_far_away():
    match = make_duel("jonathan", "dio_p1", p1=(60, 100), p2=(260, 100))
    jonathan = match.fighters[0]
    jonathan.hamon = RULES.hamon_max
    events = run(match, 120, p1=press("special"))
    assert hits_on(events, 1), "the wave never reached the opponent"
    assert match.fighters[0].pos.x < 100  # Jonathan stayed where he was


def test_the_wave_is_weaker_than_standing_next_to_him():
    move = kit("jonathan").move("base", "special")
    assert move.damage < move.projectile.damage * 1.5
    close = move.damage + move.projectile.damage
    assert close <= 95, close  # point blank both land: still in range of a special


# Bruford: the hair -----------------------------------------------------------------------


def test_bruford_fights_with_his_hair_in_almost_everything():
    bruford = kit("bruford")
    moves = [m for m in bruford.all_moves() if m.name not in ("light2",)]
    with_hair = [m for m in bruford.all_moves() if "hair" in m.fx]
    assert len(with_hair) >= 6, [m.label for m in with_hair]
    assert len(with_hair) > len(moves) // 2


def test_even_his_sword_blows_carry_the_hair():
    bruford = kit("bruford")
    for slot in ("light", "heavy", "heavy_alt"):
        move = bruford.move("base", slot)
        assert move.fx == "blade_hair", (slot, move.fx)
    assert bruford.shared_moves["hha"].fx == "blade_hair"


def test_the_second_blow_of_the_chain_is_a_hair_whip_that_reaches_further():
    bruford = kit("bruford")
    thrust, whip = bruford.move("base", "light"), bruford.stances["base"].moves["light2"]
    assert "hair" in whip.fx and whip.shape == "line"
    assert whip.reach > thrust.reach  # the hair goes where the sword cannot


def test_the_chain_still_runs_thrust_then_whip_then_piercing_hair():
    match = make_duel("bruford", "jonathan", p1=(150, 100), p2=(176, 100))
    played = []
    serial = -1
    for step in range(80):
        frame = press("light") if step % 10 == 0 else NONE
        match.step((frame, NONE))
        attack = match.fighters[0].attack
        if attack is not None and attack.serial != serial:
            serial = attack.serial
            played.append(attack.move.name)
    assert played[:3] == ["light", "light2", "light3"], played


def test_the_hair_still_drinks_what_it_pierces():
    match = make_duel("bruford", "jonathan", p1=(150, 100), p2=(200, 100))
    bruford = match.fighters[0]
    bruford.hurt(300)
    hurt = bruford.hp
    events = run(match, 60, p1=press("special"))  # the grasping hair, which drains
    assert match.fighters[0].hp > hurt  # what it took, it drank
    assert hits_on(events, 1)


# Speedwagon: the friends of Ogre Street --------------------------------------------------


def test_the_style_key_walks_through_speedwagon_and_his_two_friends():
    match = make_duel("speedwagon", "jonathan")
    speedwagon = match.fighters[0]
    seen = [speedwagon.stance]
    for _ in range(3):
        run(match, RULES.stance_switch_f + 2, p1=press("stand"))
        seen.append(match.fighters[0].stance)
    assert seen == ["base", "tattoo", "amato", "base"]  # a cycle, not a toggle


def test_each_friend_brings_a_moveset_of_their_own():
    kit_ = kit("speedwagon")
    street = kit_.move("base", "heavy")
    knives = kit_.move("tattoo", "heavy")
    kempo = kit_.move("amato", "heavy")
    assert len({street.label, knives.label, kempo.label}) == 3  # three different blows
    assert knives.projectile is not None and knives.projectile.count == 3  # thrown knives
    assert kempo.damage > street.damage  # the kempo kick hits hardest
    assert kempo.reach <= street.reach + 6  # but he has to be right there


def test_tattoo_throws_and_amato_answers():
    match = make_duel("speedwagon", "jonathan", p1=(60, 100), p2=(240, 100))
    speedwagon = match.fighters[0]
    speedwagon.stance = "tattoo"
    events = run(match, 120, p1=press("heavy"))
    assert hits_on(events, 1), "the knives never crossed the arena"
    counter = kit("speedwagon").stances["amato"].moves["special"]
    assert counter.counter == "kempo_riposte"
    assert kit("speedwagon").stances["amato"].moves["kempo_riposte"].damage >= 70


def test_the_hud_says_which_friend_is_out():
    kit_ = kit("speedwagon")
    assert kit_.stance_tags == {"tattoo": "TATTOO", "amato": "AMATO"}
    assert "tattoo" not in kit_.stance_tags.get("base", "")


def test_the_hat_supers_stay_his_whoever_is_out():
    kit_ = kit("speedwagon")
    for stance in kit_.stances:
        assert kit_.move(stance, "hha").projectile.look == "hat"
        assert kit_.move(stance, "gha").buff == "cool"
