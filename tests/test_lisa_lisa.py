"""Lisa Lisa: the Ripple Chain, the Stylish Evade (a parry that catches blows and sends
projectiles back), the scarf that reels in, the acrobatic leap, and the scarf trap."""

from helpers import NONE, kinds, make_duel, press, run, run_held, run_until

from jojo_arena.characters import get_fighter

GHA = press("heart_heat", move=(1.0, 0.0))


def test_lisa_lisa_sends_a_projectile_back():
    match = make_duel("lisa_lisa", "speedwagon", p1=(100, 100), p2=(220, 100))
    lisa, speedwagon = match.fighters
    match.step((NONE, press("special")))
    run_until(match, lambda m: m.projectiles, 30)
    run_until(match, lambda m: (m.projectiles[0].pos - lisa.pos).length() < 60, 60)
    match.step((press("special"), NONE))
    events = run_until(match, lambda m: speedwagon.hp < speedwagon.max_hp, 90)
    assert "reflect" in kinds(events)
    assert lisa.hp == lisa.max_hp


def test_the_snake_muffler_catches_a_blow():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(150, 100), p2=(172, 100))
    lisa, dummy = match.fighters
    match.step((press("special"), NONE))
    run_held(match, 4)
    events = run(match, 30, p2=press("light"))
    assert "counter" in kinds(events)
    assert lisa.hp == lisa.max_hp and dummy.hp < dummy.max_hp


def test_the_binding_scarf_reels_the_opponent_in():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(100, 100), p2=(150, 100))
    dummy = match.fighters[1]
    match.step((press("heavy"), NONE))
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 30)
    run_held(match, 20)
    assert dummy.pos.x < 140


def test_lisa_lisa_flips_through_the_air_untouchable_and_lands_a_heel():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(100, 100), p2=(230, 100))
    lisa, dummy = match.fighters
    lisa.hamon = 100
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_held(match, 6)
    assert lisa.invincible and lisa.pos.x > 110  # in the air, on her way
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 30)
    assert lisa.pos.x > 200


def test_her_ultimate_is_a_counter_and_does_nothing_on_its_own():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(150, 100), p2=(176, 100))
    lisa, dummy = match.fighters
    lisa.hh = match.rules.hh_max
    run(match, match.rules.super_freeze_f + 30, p1=GHA)
    assert lisa.countering  # she poses, open, and waits
    assert dummy.hp == dummy.max_hp and match.cutscene is None


def test_whoever_strikes_her_during_it_is_wrapped_up():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(150, 100), p2=(172, 100))
    lisa, dummy = match.fighters
    lisa.hh = match.rules.hh_max
    run(match, match.rules.super_freeze_f + 20, p1=GHA)
    assert lisa.countering
    events = match.step((NONE, press("light")))
    events += run(match, 30)
    assert "counter" in kinds(events)
    assert match.cutscene is not None and match.cutscene.name == "scarf_trap"
    run(match, match.cutscene.frames_left + 4)
    assert dummy.max_hp - dummy.hp > 200


# The Ripple Chain: hers alone ---------------------------------------------------------


def test_the_ripple_chain_branches_three_ways():
    kit = get_fighter("lisa_lisa").kit
    starter = kit.move("base", "light")
    assert dict(starter.chains) == {
        "light": "scarf_smack",
        "heavy": "drop_kick",
        "special": "style_kick",
    }
    for middle in ("scarf_smack", "drop_kick", "style_kick"):
        links = dict(kit.move("base", middle).chains)
        assert links == {
            "light": "bad_time",
            "heavy": "snake_muffler",
            "special": "prepare_to_die",
        }, middle


def test_each_button_takes_the_chain_somewhere_else():
    for button, expected in (
        ("light", "scarf_smack"),
        ("heavy", "drop_kick"),
        ("special", "style_kick"),
    ):
        match = make_duel("lisa_lisa", "mannequin_red", p1=(150, 100), p2=(168, 100))
        lisa = match.fighters[0]
        run(match, 14, p1=press("light"))  # the starter lands
        assert lisa.attack is not None and lisa.attack.connected
        run(match, 4, p1=press(button))
        assert lisa.attack is not None and lisa.attack.move.name == expected


def test_the_chain_ends_and_does_not_loop():
    match = make_duel("lisa_lisa", "mannequin_red", p1=(150, 100), p2=(168, 100))
    lisa, dummy = match.fighters
    lisa.hamon = match.rules.hamon_max
    run(match, 14, p1=press("light"))
    run(match, 16, p1=press("light"))  # scarf smack
    run(match, 6, p1=press("heavy"))  # Snake Muffler, the ender
    assert lisa.attack is not None and lisa.attack.move.name == "snake_muffler"
    assert not lisa.attack.move.chains  # nothing follows an ender
    run(match, 26)  # let the ender land
    assert dummy.max_hp - dummy.hp > 80  # three links of the chain, start to finish
