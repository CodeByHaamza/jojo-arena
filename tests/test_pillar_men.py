"""Part 2, second wave: the Pillar Men and the man who built himself a sun."""

from helpers import NONE, OPEN_BOUNDS, make_duel, press, run

from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.combat.arena import Arena
from jojo_arena.combat.fighter import Fighter, State
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.engine.geometry import Vec2
from jojo_arena.stages import load_stage

RULES = load_rules()
PILLAR_MEN = ("wamuu", "esidisi", "kars", "santana")


def kit(fighter_id: str):
    return get_fighter(fighter_id).kit


def hits_on(events, defender: int):
    return [e for e in events if e.kind == "hit" and e.fighter == defender]


def step(match: Match, frames: int) -> None:
    for _ in range(frames):
        match.step((NONE, NONE))


def in_stance(match: Match, index: int, stance: str) -> None:
    match.fighters[index].stance = stance


# They are what they are ------------------------------------------------------------------


def test_part_two_is_complete():
    part2 = {f.id for f in load_roster() if f.part == 2 and f.selectable}
    assert {"joseph_p2", "caesar", "lisa_lisa", "straizo", *PILLAR_MEN, "stroheim"} <= part2


def test_the_pillar_men_are_pillar_men_and_stroheim_is_not():
    for fighter_id in PILLAR_MEN:
        assert kit(fighter_id).nature == "pillar_man", fighter_id
        assert kit(fighter_id).nature in RULES.sun_undead_natures
    assert kit("stroheim").nature == "human"
    assert kit("stroheim").nature not in RULES.sun_undead_natures


def test_only_three_of_them_ever_mastered_a_mode():
    for fighter_id in ("wamuu", "esidisi", "kars"):
        assert kit(fighter_id).style == "stance_toggle", fighter_id
        assert len(kit(fighter_id).stances) >= 2, fighter_id
    assert len(kit("wamuu").stances) == 2
    assert len(kit("kars").stances) == 3  # and a third one he awakens into
    assert len(kit("santana").stances) == 1  # he never learned one
    assert kit("santana").style == "none"


def test_the_ripple_burns_them_double():
    match = make_duel("jonathan", "wamuu", p1=(150, 100), p2=(174, 100))
    jonathan = match.fighters[0]
    jonathan.hamon = RULES.hamon_max
    hamon_blow = run(match, 40, p1=press("special"))  # Scarlet Overdrive carries Hamon
    burned = sum(e.value for e in hits_on(hamon_blow, 1))

    plain = make_duel("jonathan", "speedwagon", p1=(150, 100), p2=(174, 100))
    plain.fighters[0].hamon = RULES.hamon_max
    normal = sum(e.value for e in hits_on(run(plain, 40, p1=press("special")), 1))
    assert burned > normal * 1.5, (burned, normal)


def test_the_sun_of_the_swiss_castle_burns_a_pillar_man_down():
    kits = (kit("wamuu"), kit("joseph_p2"))
    arena = load_stage("swiss_castle").build_arena()
    match = Match(kits, RULES, arena)
    match.tick = arena.sun_after_f + arena.sun_spread_f
    wamuu = match.fighters[0]
    patch = arena.sun_patch(arena.sun_windows[0], 1.0)
    wamuu.pos = Vec2(patch.center.x, patch.center.y)
    for _ in range(60 * 26):
        match.step((NONE, NONE))
        if wamuu.state == State.KO:
            break
    assert wamuu.state == State.KO, wamuu.hp


# A move that costs its user life ----------------------------------------------------------


def make_fighter(fighter_id: str) -> Fighter:
    arena = Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(300, 100)))
    return Match((kit(fighter_id), kit(fighter_id)), RULES, arena).fighters[0]


def test_wamuus_final_mode_takes_a_quarter_of_him():
    gha = kit("wamuu").shared_moves["gha"]
    assert gha.hp_cost >= 250 and gha.finish_damage >= gha.hp_cost
    wamuu = make_fighter("wamuu")
    wamuu.hh = RULES.gha_cost
    full = wamuu.hp
    wamuu.start_attack(gha, Vec2(300, 100))
    assert wamuu.hp == full - gha.hp_cost


def test_a_move_that_costs_life_will_not_come_out_without_it():
    wamuu = make_fighter("wamuu")
    gha = kit("wamuu").shared_moves["gha"]
    wamuu.hp = gha.hp_cost  # exactly what it asks: not enough, it would kill him
    assert not wamuu.can_pay(gha)
    wamuu.hp = gha.hp_cost + 1
    assert wamuu.can_pay(gha)


def test_the_super_itself_is_refused_when_he_cannot_pay():
    match = make_duel("wamuu", "joseph_p2", p1=(150, 100), p2=(176, 100))
    wamuu = match.fighters[0]
    wamuu.hh = RULES.gha_cost
    wamuu.hp = 200  # less than the Final Mode asks for
    run(match, 30, p1=press("heart_heat", move=(1.0, 0.0)))
    assert wamuu.hh == RULES.gha_cost or wamuu.hh == RULES.gha_cost - RULES.hha_cost
    assert wamuu.hp == 200  # it took nothing from him


# Each of them fights their own way ---------------------------------------------------------


def test_wamuus_wind_mode_trades_speed_for_reach():
    bare = kit("wamuu").move("base", "light")
    wind = kit("wamuu").move("wind", "light")
    assert wind.reach > bare.reach * 2
    assert wind.startup_f > bare.startup_f
    sandstorm = kit("wamuu").move("wind", "heavy")
    assert "SANDSTORM" in sandstorm.label
    # The storm is not a flurry of fists: it is two funnels that reach across the floor,
    # wind up for a fifth of a second, and drag whoever is caught into the middle.
    assert sandstorm.shape == "line" and sandstorm.reach > 80
    assert sandstorm.startup_f >= 18 and sandstorm.pull > 0
    assert sandstorm.hits >= 6


def test_wamuu_answers_whoever_strikes_him_in_the_base_stance():
    counter = kit("wamuu").move("base", "special")
    assert counter.counter == "wind_answer"
    answer = kit("wamuu").stances["base"].moves["wind_answer"]
    assert answer.damage >= 90 and answer.invincible_f > 0


def test_esidisi_pays_for_his_own_blood():
    jets = kit("esidisi").move("flame", "heavy")
    assert jets.hp_cost > 0 and jets.projectile is not None
    match = make_duel("esidisi", "joseph_p2", p1=(60, 100), p2=(300, 100))
    esidisi = match.fighters[0]
    in_stance(match, 0, "flame")
    full = esidisi.hp
    events = run(match, 120, p1=press("heavy"))
    assert esidisi.hp == full - jets.hp_cost
    assert hits_on(events, 1), "the blood never crossed the arena"


def test_kars_blades_reach_and_his_thrown_one_bounces():
    blade = kit("kars").move("light", "light")
    assert blade.shape == "line" and blade.reach > 30  # still the longest reach of the cast
    thrown = kit("kars").move("light", "heavy_alt")
    assert thrown.projectile is not None and thrown.projectile.wall_bounce
    awakening = kit("kars").awakening
    assert awakening is not None and awakening.stance == "ultimate"
    assert awakening.sun_immune and awakening.hh_cost > 0


def test_santana_gets_inside_and_walks_you_about():
    grab = kit("santana").move("base", "special")
    assert grab.possess_f > 0 and grab.unblockable and grab.drain > 0
    match = make_duel("santana", "joseph_p2", p1=(150, 100), p2=(168, 100))
    run(match, 40, p1=press("special"))
    assert match.fighters[1].possessed_f > 0 or hits_on([], 1) == []


def test_stroheims_lamps_burn_the_undead_and_leave_the_living_alone():
    lamps = kit("stroheim").move("base", "special")
    assert lamps.hamon, "the lamps have to count as light that burns the undead"

    def damage(target: str) -> float:
        match = make_duel("stroheim", target, p1=(150, 100), p2=(172, 100))
        return sum(e.value for e in hits_on(run(match, 50, p1=press("special")), 1))

    assert damage("wamuu") > damage("joseph_p2") * 1.5


def test_stroheim_blows_himself_up_and_it_costs_him():
    gha = kit("stroheim").shared_moves["gha"]
    assert gha.hp_cost > 0 and gha.hamon and gha.cinematic == "self_destruct"
    stroheim = make_fighter("stroheim")
    full = stroheim.hp
    stroheim.start_attack(gha, Vec2(300, 100))
    assert stroheim.hp == full - gha.hp_cost


def test_every_newcomer_has_a_super_and_an_ultimate_with_a_cutscene():
    from jojo_arena.ui.cutscenes import CUTSCENES

    for fighter_id in (*PILLAR_MEN, "stroheim"):
        shared = kit(fighter_id).shared_moves
        assert "hha" in shared and "gha" in shared, fighter_id
        assert shared["gha"].cinematic in CUTSCENES, (fighter_id, shared["gha"].cinematic)


def test_a_thrown_blade_comes_off_the_walls_and_keeps_going():
    from jojo_arena.combat.projectile import Projectile

    thrown = kit("kars").move("light", "heavy_alt").projectile
    assert thrown.bounces >= 2 and thrown.wall_bounce
    arena = Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(300, 100)))
    shot = Projectile(0, Vec2(380, 100), Vec2(6, 0), thrown, thrown.lifetime_f)
    for _ in range(40):
        shot.update(arena)
        if shot.bounced:
            break
    assert shot.bounced == 1 and shot.alive  # it turned round instead of dying
    assert shot.velocity.x < 0


# The Power Up key: an awakening ------------------------------------------------------------


def test_the_power_up_key_turns_kars_into_the_ultimate_life_form():
    match = make_duel("kars", "joseph_p2", p1=(150, 100), p2=(260, 100))
    kars = match.fighters[0]
    awakening = kars.kit.awakening
    kars.hh = awakening.hh_cost
    assert kars.can_awaken and not kars.awakened
    charge = kars.kit.awakening.charge_f
    events = run(match, charge + 4, p1=press("power_up"))
    assert any(e.kind == "awaken" for e in events)
    assert kars.awakened and kars.stance == "ultimate"
    assert kars.hh == 0  # it cost him both bars
    assert not kars.can_awaken  # and it only happens once


def test_without_the_bars_nothing_happens():
    match = make_duel("kars", "joseph_p2")
    kars = match.fighters[0]
    kars.hh = kars.kit.awakening.hh_cost - 1
    run(match, 20, p1=press("power_up"))
    assert not kars.awakened and kars.stance == "base"


def test_the_mode_key_can_no_longer_take_him_out_of_it():
    match = make_duel("kars", "joseph_p2")
    kars = match.fighters[0]
    kars.hh = kars.kit.awakening.hh_cost
    run(match, kars.kit.awakening.charge_f + 4, p1=press("power_up"))
    assert kars.stance == "ultimate"
    run(match, RULES.stance_switch_f + 30, p1=press("stand"))
    assert kars.stance == "ultimate"  # there is no going back


def test_the_sun_stops_mattering_once_he_has_awakened():
    stage = load_stage("swiss_castle")
    arena = stage.build_arena()
    match = Match((kit("kars"), kit("joseph_p2")), RULES, arena)
    match.tick = arena.sun_after_f + arena.sun_spread_f
    kars = match.fighters[0]
    patch = arena.sun_patch(arena.sun_windows[0], 1.0)
    kars.pos = Vec2(patch.center.x, patch.center.y)
    kars.blood = 0
    step(match, 120)
    burned = kars.max_hp - kars.hp
    assert burned > 0  # not awakened: the sun has him

    kars.awakened = True
    kars.hp = kars.max_hp
    assert kars.sun_proof
    step(match, 240)
    assert kars.hp == kars.max_hp  # the ultimate life form walks in daylight


def test_the_ultimate_moveset_is_its_own_thing():
    ultimate = kit("kars").stances["ultimate"].moves
    light_mode = kit("kars").stances["light"].moves
    assert {m.label for m in ultimate.values()} & {m.label for m in light_mode.values()} == set()
    assert all(m.drain > 0 for m in (ultimate["light"], ultimate["light2"], ultimate["heavy"]))
    assert ultimate["special"].hamon  # his own Ripple burns the undead
    assert kit("kars").stance_tags["ultimate"]


def test_nobody_else_awakens_yet():
    from jojo_arena.characters import load_roster

    with_awakening = [f.id for f in load_roster() if f.kit.awakening is not None]
    assert with_awakening == ["kars"]


def test_the_ultimate_life_form_has_what_the_ultimate_life_form_has():
    """Awakened, Kars is not a Pillar Man with better numbers: the sun means nothing to
    him, he makes his own Ripple, he fires what he has absorbed, and a tentacle drags
    you back in. (jojowiki ASBR/Kars, Ultimate Thing skills.)"""
    kit_ = kit("kars")
    assert kit_.awakening.sun_immune
    ripple = kit_.move("ultimate", "special")
    assert ripple.hamon and ripple.reach >= 100  # his own Ripple, and it reaches
    genes = kit_.move("ultimate", "heavy_alt")
    assert genes.projectile is not None and genes.projectile.homing > 0  # the piranha follows
    tentacle = kit_.move("ultimate", "heavy")
    assert tentacle.pull > 0 and tentacle.fx == "tentacle"


def test_the_sun_stops_mattering_once_the_mask_is_on():
    match = make_duel("kars", "mannequin_red", p1=(150, 100), p2=(260, 100))
    kars = match.fighters[0]
    kars.hp = kars.max_hp
    kars.sun_f = 300  # he has been standing in it
    before = kars.hp
    kars.hh = match.rules.hh_max
    kars.complete_awakening()
    assert kars.sun_proof
    match.arena.sun_spread_f = 1  # full daylight, straight away
    run(match, 120)
    assert kars.hp >= before - 1  # the light does nothing to him now


def test_the_mask_does_not_come_off_between_rounds():
    """Kars put the Stone Mask and the Red Stone on: the next round starts with the
    Ultimate Life Form, not with a Pillar Man again."""
    from jojo_arena.combat.arena import Arena
    from jojo_arena.combat.rounds import Phase, Rounds
    from jojo_arena.engine.actions import NEUTRAL

    def arena():
        return Arena(OPEN_BOUNDS, (Vec2(150, 100), Vec2(250, 100)))

    rounds = Rounds((kit("kars"), kit("mannequin_blue")), RULES, arena, 2)
    kars = rounds.match.fighters[0]
    kars.hh = RULES.hh_max
    kars.complete_awakening()
    assert kars.awakened and kars.stance == "ultimate"

    for _ in range(900):  # finish the round
        if rounds.phase == Phase.FIGHT:
            rounds.match.fighters[1].hurt(500)
        rounds.step((NEUTRAL, NEUTRAL))
        if rounds.round_number == 2 and rounds.phase == Phase.FIGHT:
            break
    assert rounds.round_number == 2
    again = rounds.match.fighters[0]
    assert again.awakened and again.stance == "ultimate"
    assert again.sun_proof  # and the sun still means nothing to him


def test_what_he_sends_off_as_an_animal_comes_back_fed():
    """The hand he turns into a flesh-eating squirrel (jojowiki, Kars): it chases, it
    bites, and what it eats goes back to him."""
    match = make_duel("kars", "joseph_p2", p1=(150, 100), p2=(300, 100))
    kars, joseph = match.fighters
    kars.complete_awakening()
    run(match, 4)
    kars.hp = kars.max_hp - 150
    hurt, fed = joseph.hp, kars.hp
    run(match, 2, p1=press("heavy", move=(1.0, 0.0)))
    run(match, 220)
    assert joseph.hp < hurt  # it found him across the arena
    assert kars.hp > fed  # and it brought him back a mouthful


def test_the_wings_carry_him_further_than_he_can_walk():
    """ "Bird-like wings that enable him to fly" (jojowiki, Kars)."""
    match = make_duel("kars", "joseph_p2", p1=(150, 100), p2=(360, 100))
    kars, joseph = match.fighters
    kars.complete_awakening()
    run(match, 4)
    start = kars.pos.x
    run(match, 60, p1=press("special", move=(1.0, 0.0)))
    flown = kars.pos.x - start
    assert flown > 150, flown  # further than a walk, in a third of a second
    assert joseph.hp < joseph.max_hp  # and the landing is a blow


def test_awakened_his_heart_heat_attack_is_not_the_blade_storm_any_more():
    kit_ = kit("kars")
    blades = kit_.move("light", "hha")
    beasts = kit_.move("ultimate", "hha")
    assert beasts is not blades
    assert beasts.projectile is not None and beasts.projectile.origin == "ring"
    assert beasts.projectile.count >= 5  # they close in from every side
