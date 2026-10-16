from jojo_arena.characters import get_fighter
from jojo_arena.combat.framedata import frame_data, signed
from jojo_arena.combat.rules import load_rules

RULES = load_rules()


def test_advantage_on_hit_and_block():
    jab = get_fighter("jotaro_p3").kit.move("base", "light")
    data = frame_data(jab, RULES)
    busy = jab.active_f - 1 + jab.recovery_f
    assert (data.startup, data.active, data.recovery) == (4, 3, 10)
    assert data.on_hit == jab.hitstun_f - busy
    blockstun = jab.blockstun_f or round(jab.hitstun_f * RULES.blockstun_ratio)
    assert data.on_block == blockstun - busy


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
