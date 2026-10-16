"""The balance tool runs: bots fight a matchup and the table comes out."""

import balance


def test_a_bot_fight_ends_with_a_result():
    winner, dealt, taken = balance.fight("jotaro_p3", "kakyoin", seed=1)
    assert winner in (0, 1, None)
    assert dealt >= 0 and taken >= 0


def test_the_report_lists_every_fighter():
    table = balance.run(["jotaro_p3", "dio_p3"], fights=1)
    text = balance.report(table, ["jotaro_p3", "dio_p3"])
    assert "jotaro_p3" in text and "dio_p3" in text and "%" in text
