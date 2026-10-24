"""An ultimate has the shape of its technique, and a vortex pulls.

The rule is written down in CLAUDE.md: a beam is a long line, an explosion is a wide
radius, a trap is a wide line in front, a grab is unblockable - and a punch-sized circle
is only for a technique that really is a punch. This file is what keeps it true.
"""

from helpers import NONE, make_duel, press, run_held

from jojo_arena.characters import get_fighter, load_roster

# These ultimates really are blows: Ora Ora Final is a barrage of fists, Sunlight Yellow
# Overdrive is one Hamon punch, and the Pillar Men and the vampires take their prey in
# their hands. Anything not on this list has to look like what it is.
FISTS_AND_HANDS = {
    ("jotaro_p3", "hha"),  # the crushing fist: it is a fist
    ("jotaro_p3", "gha"),  # Ora Ora Final: a barrage of them, as it should be
    ("jonathan", "gha"),  # Sunlight Yellow Overdrive: one Hamon punch, up close
    ("dio_p3", "hha"),  # The World's kick
    ("avdol", "hha"),  # "Give me four wishes instead!": Magician's Red kicks forward (ASBR)
}


def test_no_ultimate_is_a_bare_punch():
    bare = []
    for entry in load_roster():
        kit = entry.kit
        if entry.id.startswith("mannequin"):
            continue
        for slot in ("hha", "gha"):
            move = kit.move(kit.base_stance_name, slot)
            if move is None or (entry.id, slot) in FISTS_AND_HANDS:
                continue
            if move.radius <= 0 and move.projectile is None and not move.at_target:
                continue  # not a strike at all: a buff, an escape, a counter
            looks_like_itself = (
                move.projectile is not None  # it is thrown
                or move.at_target  # it lands on the spot where they stand
                or (move.shape == "line" and move.reach >= 40)  # a beam, a cable, a whip
                or move.radius >= 26  # a blast, a dome, a zone
                or move.unblockable  # a grab
                or move.counter  # it answers whoever strikes
                or move.leap > 0  # it crosses the floor to reach them
                or move.web is not None
            )
            if not looks_like_itself:
                bare.append(f"{entry.id}.{slot} ({move.label}): circle reach {move.reach}")
    assert bare == [], "these ultimates are still punch-shaped: " + "; ".join(bare)


def test_wamuus_rift_leaves_the_horn_and_crosses_the_arena():
    kit = get_fighter("wamuu").kit
    rift = kit.move("base", "gha")
    assert rift.fx == "wind_beam" and rift.shape == "line"
    assert rift.reach >= 280  # from one wall to the other
    assert rift.hp_cost > 0  # and it tears him open to do it


def test_josephs_cables_cover_the_ground_in_front_of_him():
    cables = get_fighter("joseph_p2").kit.move("base", "gha")
    assert cables.fx == "cables" and cables.shape == "line"
    assert cables.reach >= 90 and cables.radius >= 20  # wide, not a jab


def test_the_sandstorm_drags_the_opponent_into_it():
    match = make_duel("wamuu", "mannequin_red", p1=(100, 100), p2=(210, 100))
    wamuu, dummy = match.fighters
    wamuu.hh = match.rules.hh_max
    start = dummy.pos.x
    run_held(match, match.rules.super_freeze_f + 30, p1=press("heart_heat"))
    assert dummy.pos.x < start - 10, "the storm should have pulled him in"
    assert dummy.hp < dummy.max_hp


def test_the_suction_stops_when_the_move_does():
    match = make_duel("wamuu", "mannequin_red", p1=(100, 100), p2=(260, 100))
    wamuu, dummy = match.fighters
    wamuu.hh = match.rules.hh_max
    run_held(match, match.rules.super_freeze_f + 30, p1=press("heart_heat"))
    pulled = dummy.pos.x
    for _ in range(120):
        match.step((NONE, NONE))
    assert abs(dummy.pos.x - pulled) < 40  # knocked back at the end, not still drifting in
