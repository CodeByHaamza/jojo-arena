"""Balance check: the computer plays every matchup many times and counts the wins.

    python tools/balance.py                 # every pair of selectable fighters, 20 fights each
    python tools/balance.py --fights 100    # more fights, steadier numbers
    python tools/balance.py jotaro_p3 dio_p3

Both sides are the computer at its top level (combat/ai.py): it spaces, guards, punishes
and spends its gauges, but it does not plan, so the numbers say more about raw power
than about what a good player can do. Still, a fighter far above 60 % against everyone is
worth a look. Each fight is one round on the Cairo street, with a time limit.
"""

from __future__ import annotations

import argparse
import itertools
import os
import sys
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jojo_arena.characters import get_fighter, load_roster  # noqa: E402
from jojo_arena.combat.ai import CpuPlayer  # noqa: E402
from jojo_arena.combat.rounds import Phase, Rounds  # noqa: E402
from jojo_arena.combat.rules import load_rules  # noqa: E402
from jojo_arena.stages import load_stage  # noqa: E402

MAX_STEPS = 60 * 120  # two minutes of play, at most
LEVEL = 3  # both sides played by the computer at its best


@dataclass
class Result:
    wins: int = 0
    losses: int = 0
    draws: int = 0
    damage_dealt: int = 0
    fights: int = 0

    @property
    def win_rate(self) -> float:
        played = self.wins + self.losses + self.draws
        return (self.wins + 0.5 * self.draws) / played if played else 0.0


def fight(p1: str, p2: str, seed: int) -> tuple[int | None, int, int]:
    """One single-round fight between two bots: (winner index or None, damage by each)."""
    rules = load_rules()
    stage = load_stage("cairo_night")
    kits = (get_fighter(p1).kit, get_fighter(p2).kit)
    rounds = Rounds(kits, rules, stage.build_arena, 1)
    bots = (CpuPlayer(LEVEL, seed * 2 + 1), CpuPlayer(LEVEL, seed * 2 + 2))
    for _ in range(MAX_STEPS):
        match = rounds.match
        frames = tuple(bots[i].think(f, match.opponent(f)) for i, f in enumerate(match.fighters))
        rounds.step(frames)
        if rounds.phase == Phase.MATCH_OVER:
            break
    a, b = rounds.match.fighters
    return rounds.winner, b.max_hp - b.hp, a.max_hp - a.hp


def run(fighters: list[str], fights: int) -> dict[tuple[str, str], Result]:
    table: dict[tuple[str, str], Result] = {}
    for p1, p2 in itertools.permutations(fighters, 2):
        result = table.setdefault((p1, p2), Result())
        for seed in range(fights):
            winner, dealt, _taken = fight(p1, p2, seed)
            result.fights += 1
            result.damage_dealt += dealt
            if winner is None:
                result.draws += 1
            elif winner == 0:
                result.wins += 1
            else:
                result.losses += 1
    return table


def report(table: dict[tuple[str, str], Result], fighters: list[str]) -> str:
    width = max(len(f) for f in fighters) + 2
    lines = ["Win rate of the row fighter against the column fighter:", ""]
    lines.append(" " * width + "".join(f"{f[:10]:>12}" for f in fighters) + "     overall")
    for row in fighters:
        cells, total = [], Result()
        for col in fighters:
            if row == col:
                cells.append(f"{'-':>12}")
                continue
            result = table[(row, col)]
            cells.append(f"{result.win_rate * 100:>11.0f}%")
            total.wins += result.wins
            total.losses += result.losses
            total.draws += result.draws
        lines.append(f"{row:<{width}}" + "".join(cells) + f"{total.win_rate * 100:>11.0f}%")
    return "\n".join(lines)


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("fighters", nargs="*", help="fighter ids (default: all selectable)")
    parser.add_argument("--fights", type=int, default=20, help="fights per matchup and side")
    args = parser.parse_args(argv)
    fighters = args.fighters or [f.id for f in load_roster() if f.selectable]
    print(report(run(fighters, args.fights), fighters))


if __name__ == "__main__":
    main(sys.argv[1:])
