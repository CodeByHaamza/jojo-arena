"""Caesar: bubbles that drift after the opponent, the lenses he leaves behind, the
Cat Stance, and Burn Black."""

from helpers import NONE, hold, kinds, make_duel, press, run, run_held, run_until

from jojo_arena.engine.geometry import Vec2

GHA = press("heart_heat", move=(1.0, 0.0))


def test_caesars_bubbles_drift_after_the_opponent():
    match = make_duel("caesar", "mannequin_red", p1=(100, 100), p2=(260, 130))
    dummy = match.fighters[1]
    match.step((press("special"), NONE))
    run_until(match, lambda m: m.projectiles, 30)
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 150, p2=hold(move=(0.0, 1.0)))


def test_the_lenses_are_left_behind_and_fire_when_crossed():
    match = make_duel("caesar", "mannequin_red", p1=(100, 100), p2=(260, 100))
    caesar, dummy = match.fighters
    caesar.hamon = match.rules.hamon_max
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_held(match, 30)
    assert match.traps, "the lenses should hang there waiting"
    run_until(match, lambda m: dummy.hp < dummy.max_hp, 240, p2=hold(move=(-1.0, 0.0)))


def test_the_cat_stance_answers_whoever_strikes_him():
    match = make_duel("caesar", "mannequin_red", p1=(150, 100), p2=(172, 100))
    caesar, dummy = match.fighters
    match.step((press("special", move=(1.0, 0.0)), NONE))
    run_held(match, 6)
    assert caesar.countering
    events = match.step((NONE, press("light")))
    events += run_held(match, 20)
    assert "counter" in kinds(events)
    assert dummy.hp < dummy.max_hp


def test_burn_black_sets_him_alight_in_a_cutscene():
    match = make_duel("caesar", "mannequin_red", p1=(100, 100), p2=(124, 100))
    caesar, dummy = match.fighters
    caesar.hh = match.rules.hh_max
    events = run_held(match, match.rules.super_freeze_f + 40, p1=GHA)
    assert "cutscene_start" in kinds(events)
    assert match.cutscene is not None and match.cutscene.name == "burn_black"
    run_held(match, match.cutscene.frames_left + 4)
    assert dummy.max_hp - dummy.hp > 200


def lenses_laid(foe: str, gap: float = 160.0):
    """Caesar lays a lens in front of him, and the other one is far away."""
    match = make_duel("caesar", foe, p1=(100, 100), p2=(100 + gap, 100))
    caesar = match.fighters[0]
    caesar.hamon = match.rules.hamon_max
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_held(match, 30)
    assert match.traps
    return match


def test_a_lens_fires_sunlight_so_the_undead_take_it_twice():
    """The lens refracts sunlight (JoJo Wiki). Sunlight is what kills a Pillar Man."""
    hurt = {}
    for foe in ("mannequin_red", "santana"):
        match = lenses_laid(foe)
        target = match.fighters[1]
        run_until(
            match, lambda m: m.fighters[1].hp < m.fighters[1].max_hp, 300, p2=hold(move=(-1.0, 0.0))
        )
        run_held(match, 20)
        hurt[foe] = target.max_hp - target.hp
    assert hurt["santana"] > hurt["mannequin_red"] * 1.5, hurt


def test_a_blow_on_caesar_pops_every_lens():
    match = lenses_laid("wamuu", gap=250)
    caesar = match.fighters[0]
    caesar.take_hit(20, 24, Vec2(-1, 0), False)
    events = run(match, 3)
    assert "trap_popped" in kinds(events)
    assert not match.traps  # a bubble is a bubble
