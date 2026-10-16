"""Young Joseph: the Clacker Volley and its finisher, the sledgehammer, the tricks of
the trade, the secret technique of running away, and "your next line is...!" """

from helpers import NONE, hold, kinds, make_duel, press, run, run_held, run_until


def test_the_clacker_volley_is_a_barrage_with_a_finisher():
    match = make_duel("joseph_p2", "mannequin_red", p1=(150, 100), p2=(176, 100))
    joseph, dummy = match.fighters
    joseph.hamon = match.rules.hamon_max
    volley = joseph.kit.move("base", "heavy")
    assert volley.hits >= 8 and volley.chain == "who_laughs"
    events = run(match, 60, p1=press("heavy"))  # pressed once: the whole barrage
    assert kinds(events).count("hit") >= 5, kinds(events)
    assert dummy.max_hp - dummy.hp > 50


def test_the_hammer_goes_through_a_guard():
    match = make_duel("joseph_p2", "mannequin_red", p1=(150, 100), p2=(170, 100))
    dummy = match.fighters[1]
    hammer = match.fighters[0].kit.move("base", "special_alt")
    assert hammer.unblockable and hammer.damage > 80
    run_until(
        match,
        lambda m: dummy.hp < dummy.max_hp,
        90,
        p1=press("special", move=(1.0, 0.0)),
        p2=hold("guard"),
    )


def test_the_tricks_of_the_trade_play_their_cutscene():
    match = make_duel("joseph_p2", "mannequin_red", p1=(150, 100), p2=(174, 100))
    joseph, dummy = match.fighters
    joseph.hh = match.rules.hh_max
    gha = press("heart_heat", move=(1.0, 0.0))
    events = run_held(match, match.rules.super_freeze_f + 40, p1=gha)
    assert "cutscene_start" in kinds(events)
    assert match.cutscene is not None and match.cutscene.name == "overdrive_beat"
    run_held(match, match.cutscene.frames_left + 4)
    assert dummy.max_hp - dummy.hp > 200


def test_the_secret_technique_runs_away_invincible():
    match = make_duel("joseph_p2", "mannequin_red", p1=(200, 100), p2=(240, 100))
    joseph = match.fighters[0]
    start = joseph.pos.x
    match.step((press("heavy", move=(1.0, 0.0)), NONE))
    run_held(match, 4)
    assert joseph.invincible
    run_held(match, 14)
    assert joseph.pos.x < start - 40


def test_he_calls_the_same_button_again_and_counters_it():
    match = make_duel("joseph_p2", "mannequin_red", p1=(150, 100), p2=(172, 100))
    joseph, dummy = match.fighters
    dummy.last_slot = "light"  # the dummy's last attack was a light blow
    run_held(match, 40, p1=hold("pose"))
    assert joseph.countering
    events = match.step((hold("pose"), press("light")))
    events += run_held(match, 20, p1=hold("pose"))
    assert "counter" in kinds(events) and "foreseen" in kinds(events)
    run_held(match, 40)
    assert joseph.hp == joseph.max_hp and dummy.hp < dummy.max_hp


def test_a_wrong_call_leaves_him_open():
    match = make_duel("joseph_p2", "mannequin_red", p1=(150, 100), p2=(172, 100))
    joseph, dummy = match.fighters
    dummy.last_slot = "special"  # he expects a special...
    run_held(match, 40, p1=hold("pose"))
    match.step((hold("pose"), press("light")))  # ...and gets a jab
    run_held(match, 30, p1=hold("pose"))
    assert joseph.hp < joseph.max_hp
