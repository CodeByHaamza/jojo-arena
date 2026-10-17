"""A pass over every kit: what repeats, what shows nothing, what is missing.

    python tools/audit_kits.py

Counts rather than opinions, so a pass over the roster is cheap to repeat:

1. labels two characters share (fine when the work shares them, lazy otherwise);
2. blows that are the same numbers on two characters - the same fighter twice;
3. how much of each kit is a plain punch, and how much of it has a look of its own;
4. ultimates that would show nothing at all: no cutscene, no effect, no projectile,
   no barrage of blows;
5. moves with no description.

Nothing here fails a build: it is a list to read before deciding what to fix.
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jojo_arena.characters import load_roster  # noqa: E402

# Names of blows that say nothing about who threw them.
PLAIN = {
    "DIRECT",
    "CROCHET",
    "REVERS",
    "COUP DE PIED",
    "COUP DE GENOU",
    "COUP DE COUDE",
    "COUP DE BOULE",
    "COUP DE TÊTE",
    "GRIFFE",
    "UPPERCUT",
    "BALAYAGE",
    "CHARGE",
    "ESTOC",
}
UNDEAD = ("vampire", "zombie", "pillar_man")
# The one exception the work allows: awakened, Kars makes a Ripple of his own, which the
# wiki puts at hundreds of times Joseph's. Everyone else the Ripple kills cannot use it.
OWN_RIPPLE = {("kars", "ultimate")}

# Techniques the work really does give to two characters.
SHARED_IN_THE_WORK = {
    "ABSORPTION",
    "ZOOM PUNCH",
    "OVERDRIVE",
    "SPACE RIPPER STINGY EYES",
    "SUNLIGHT YELLOW OVERDRIVE",
}


def main() -> None:
    fighters = [f for f in load_roster() if f.selectable]
    print(f"{len(fighters)} persos jouables\n")

    labels: dict[str, set[str]] = defaultdict(set)
    numbers: dict[tuple, list[str]] = defaultdict(list)
    for fighter in fighters:
        for move in fighter.kit.all_moves():
            if move.label:
                labels[move.label].add(fighter.id)
            if move.radius > 0 and move.name not in ("hha", "gha"):
                key = (
                    move.startup_f,
                    move.active_f,
                    move.recovery_f,
                    move.damage,
                    move.reach,
                    move.radius,
                )
                numbers[key].append(f"{fighter.id}/{move.name}")

    print("== Noms portés par plusieurs persos ==")
    for label, who in sorted(labels.items()):
        if len(who) > 1:
            tag = "(partagé dans l'œuvre)" if label in SHARED_IN_THE_WORK else "<-- à revoir"
            print(f"  {label:34} {', '.join(sorted(who)):34} {tag}")

    twins = {
        key: who for key, who in numbers.items() if len({name.split("/")[0] for name in who}) > 1
    }
    print(f"\n== Coups identiques au chiffre près entre deux persos : {len(twins)} ==")
    for key, who in twins.items():
        start, active, recovery, damage, reach, radius = key
        print(
            f"  {start}/{active}/{recovery} dmg {damage} portée {reach} r{radius}: {', '.join(who)}"
        )

    print("\n== Variété et identité visuelle ==")
    columns = ("perso", "coups", "noms plats", "avec effet", "portée max", "postures")
    print(f"  {columns[0]:14}{columns[1]:>6}{columns[2]:>12}", end="")
    print(f"{columns[3]:>12}{columns[4]:>12}{columns[5]:>10}")
    for fighter in sorted(fighters, key=lambda f: f.id):
        moves = [m for m in fighter.kit.all_moves() if m.radius > 0 or m.projectile]
        plain = sum(1 for m in moves if (m.label or "").strip() in PLAIN)
        with_fx = sum(1 for m in moves if m.fx)
        reach = max((m.reach for m in moves), default=0)
        print(
            f"  {fighter.id:14}{len(moves):6}{plain:12}{with_fx:12}"
            f"{reach:12.0f}{len(fighter.kit.stances):10}"
        )

    print("\n== Ultimes qui ne montreraient rien ==")
    empty = 0
    for fighter in sorted(fighters, key=lambda f: f.id):
        for slot in ("hha", "gha"):
            move = fighter.kit.shared_moves.get(slot)
            if move is None:
                print(f"  {fighter.id:14} {slot}: MANQUANT")
                empty += 1
                continue
            shows = (
                move.cinematic
                or move.fx
                or move.projectile
                or move.counter
                or move.hits > 1  # a barrage draws itself
                or move.web
            )
            if not shows:
                print(f"  {fighter.id:14} {slot}: {move.label}")
                empty += 1
    if not empty:
        print("  aucun")

    # The Ripple kills the undead: nobody it kills should be using it, and nobody who
    # breathes it should be paying with blood. (Straizo had been given Lisa Lisa's scarf.)
    print("\n== Natures contredites ==")
    wrong = []
    for fighter in fighters:
        nature, style = fighter.kit.nature, fighter.kit.style
        for stance_name, stance in fighter.kit.stances.items():
            if (fighter.id, stance_name) in OWN_RIPPLE:
                continue
            for move in stance.moves.values():
                if nature in UNDEAD and (move.hamon or move.hamon_cost):
                    wrong.append(f"{fighter.id} ({nature}) : {move.name} utilise l'Onde")
                if style == "hamon" and move.blood_cost:
                    wrong.append(f"{fighter.id} (hamon) : {move.name} coûte du sang")
        for move in fighter.kit.shared_moves.values():
            if nature in UNDEAD and (move.hamon or move.hamon_cost):
                wrong.append(f"{fighter.id} ({nature}) : {move.name} utilise l'Onde")
    print("  " + ("\n  ".join(wrong) if wrong else "aucune"))

    print("\n== Coups sans description ==")
    silent = [
        f"{fighter.id}: {move.name}"
        for fighter in fighters
        for move in fighter.kit.all_moves()
        if move.radius > 0 and not move.info
    ]
    print("  " + ("\n  ".join(silent) if silent else "aucun"))


if __name__ == "__main__":
    main()
