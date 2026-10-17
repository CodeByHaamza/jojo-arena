from jojo_arena.characters import get_fighter
from jojo_arena.combat.framedata import frame_data, signed
from jojo_arena.combat.rules import load_rules

RULES = load_rules()


def test_advantage_on_hit_and_block():
    jab = get_fighter("jotaro_p3").kit.move("base", "light")
    data = frame_data(jab, RULES)
    busy = jab.active_f - 1 + jab.recovery_f
    assert (data.startup, data.active, data.recovery) == (jab.startup_f, 3, jab.recovery_f)
    assert data.on_hit == jab.hitstun_f - 1 - busy == 7
    blockstun = jab.blockstun_f or round(jab.hitstun_f * RULES.blockstun_ratio)
    assert data.on_block == blockstun - 1 - busy == -1


def test_no_advantage_for_shots_rushes_or_cutscenes():
    kit = get_fighter("dio_p3").kit
    for move in (kit.move("base", "special"), kit.move("stand", "heavy"), kit.move("base", "gha")):
        data = frame_data(move, RULES)
        assert data.on_hit is None and data.on_block is None


def test_grabs_have_no_block_advantage():
    grab = get_fighter("dio_p3").kit.move("base", "heavy")
    assert frame_data(grab, RULES).on_block is None


def test_signed():
    assert (signed(6), signed(-2), signed(0), signed(None)) == ("+6", "-2", "0", "-")


def test_no_light_blow_is_plus_on_block():
    """A jab that leaves its user at an advantage after a guard means the opponent never
    gets their turn back. Star Platinum's ORA was +1 at one point: it is not a speed, it
    is a lock."""
    from jojo_arena.characters import load_roster

    plus = []
    for fighter in load_roster():
        for stance_name, stance in fighter.kit.stances.items():
            for slot in ("light", "light2", "light3"):
                move = stance.moves.get(slot)
                if move is None or move.hits > 1 or not move.radius:
                    continue
                data = frame_data(move, RULES)
                if data.on_block is not None and data.on_block > 0:
                    plus.append(f"{fighter.id}/{stance_name}/{slot} {data.on_block:+}")
    assert plus == [], "these light blows are plus on block: " + ", ".join(plus)
