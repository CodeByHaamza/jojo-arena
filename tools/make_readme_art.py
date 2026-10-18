"""Draw the animated pictures of the README, with nothing but the standard library.

    python tools/make_readme_art.py            # everything, into docs/media/
    python tools/make_readme_art.py banner     # just one

SMIL is the only animation GitHub plays inside a README, so everything here is SVG with
`<animate>` and `<animateTransform>` - no script, no library, no external font. Each
drawing is a function that returns the file's text, so changing one is changing a few
lines of Python rather than editing XML by hand.

The faces of the roster are not drawn here: they come out of the game's own sprite
generator (`faces` below), so the README always shows the characters as they look in
the fight.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OUT = Path("docs/media")

NIGHT = "#140f1e"
GOLD = "#f0c23c"
PALE = "#fff6d0"
PURPLE = "#7a48c8"
LILAC = "#cdbbe8"
BLOOD = "#c8403a"
JADE = "#2ea24a"

UI = "'Trebuchet MS',Verdana,sans-serif"
JP = "'Noto Sans JP','Yu Gothic','Hiragino Kaku Gothic ProN','MS PGothic',sans-serif"


def escape(text: str) -> str:
    """XML text: the ASCII drawings are full of < and >."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def header(width: int, height: int, title: str, description: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"'
        f' width="{width}" height="{height}" role="img" aria-label="{title}">\n'
        f"  <title>{title}</title>\n  <desc>{description}</desc>\n"
    )


def menace(x: float, y: float, delay: float, size: int = 40) -> str:
    """One ゴ rising and fading, on its own beat."""
    return (
        f'  <text x="{x}" y="{y}" font-family="{JP}" font-weight="700" font-size="{size}"'
        f' fill="{PURPLE}" opacity="0.2">ゴ\n'
        f'    <animate attributeName="opacity" values="0.08;0.6;0.08" dur="2.2s"'
        f' begin="{delay}s" repeatCount="indefinite"/>\n'
        f'    <animateTransform attributeName="transform" type="translate"'
        f' values="0 12;0 -8;0 12" dur="2.2s" begin="{delay}s" repeatCount="indefinite"/>\n'
        "  </text>\n"
    )


def test_count() -> int:
    """How many tests the suite really has: asked of pytest, never typed by hand.

    If pytest is not around (someone just wants the pictures), the test files are counted
    instead, which is the same number give or take the parametrised cases.
    """
    import ast
    import re
    import subprocess
    import sys

    try:
        done = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=180,
        )
        found = re.search(r"(\d+) tests? collected", done.stdout)
        if found:
            return int(found.group(1))
    except (OSError, subprocess.SubprocessError):
        pass
    total = 0
    for path in sorted(Path("tests").glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        total += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        )
    return total


def counters() -> str:
    """The numbers that say what the project is, counting up as you look at them."""
    tests = test_count()
    figures = [
        ("19", "PERSOS JOUABLES", GOLD),
        ("3", "ARÈNES", JADE),
        (f"{tests}", "TESTS", "#5a9ef0"),
        ("94 %", "COUVERTURE", PURPLE),
        ("60", "IMAGES/SEC FIXES", BLOOD),
    ]
    width, height = 960, 150
    out = [header(width, height, "Les chiffres de JoJo Arena", "Compteurs animés.")]
    out.append(f'  <rect width="{width}" height="{height}" fill="{NIGHT}"/>\n')
    step = width / len(figures)
    for i, (value, label, color) in enumerate(figures):
        x = step * (i + 0.5)
        begin = i * 0.25
        out.append(
            f'  <g text-anchor="middle" font-family="{UI}" font-weight="700" opacity="0">\n'
            f'    <animate attributeName="opacity" values="0;1" dur="0.5s"'
            f' begin="{begin}s" fill="freeze"/>\n'
            f'    <text x="{x}" y="78" font-size="48" fill="{color}">{value}\n'
            f'      <animateTransform attributeName="transform" type="translate"'
            f' values="0 14;0 0" dur="0.6s" begin="{begin}s" fill="freeze"/>\n'
            "    </text>\n"
            f'    <text x="{x}" y="104" font-size="14" fill="{LILAC}"'
            f' letter-spacing="2">{label}</text>\n'
            "  </g>\n"
        )
        if i:
            out.append(
                f'  <rect x="{step * i - 0.5}" y="44" width="1" height="54"'
                f' fill="{PURPLE}" opacity="0.35"/>\n'
            )
    # A Ripple running under the row.
    out.append(f'  <rect x="0" y="128" width="960" height="2" fill="{GOLD}" opacity="0.25"/>\n')
    out.append(
        f'  <rect x="0" y="127" width="120" height="4" rx="2" fill="{PALE}">\n'
        '    <animate attributeName="x" values="-120;960;-120" dur="7s"'
        ' repeatCount="indefinite"/>\n'
        "  </rect>\n"
    )
    out.append("</svg>\n")
    return "".join(out)


def loop() -> str:
    """The five beats of a round, lighting up one after the other."""
    beats = [
        ("APPROCHE", "garde, dash, esquive", GOLD),
        ("CLASH", "deux coups se croisent", BLOOD),
        ("COMBO", "trois coups sur la même touche", "#5a9ef0"),
        ("HEART HEAT", "une barre, un ultime", PURPLE),
        ("CINÉMATIQUE", "si le premier coup touche", JADE),
    ]
    width, height = 960, 190
    out = [header(width, height, "La boucle d'un round", "Les cinq temps d'un échange.")]
    out.append(f'  <rect width="{width}" height="{height}" fill="{NIGHT}"/>\n')
    out.append(menace(26, 170, 0.0, 34))
    out.append(menace(900, 54, 0.6, 34))
    span = (width - 120) / (len(beats) - 1)
    for i, (title, under, color) in enumerate(beats):
        x = 60 + span * i
        begin = i * 0.9
        out.append(
            f"  <g>\n"
            f'    <circle cx="{x}" cy="78" r="26" fill="none" stroke="{color}"'
            f' stroke-width="2" opacity="0.35"/>\n'
            f'    <circle cx="{x}" cy="78" r="26" fill="none" stroke="{color}"'
            f' stroke-width="3" opacity="0">\n'
            f'      <animate attributeName="opacity" values="0;1;0" dur="4.5s"'
            f' begin="{begin}s" repeatCount="indefinite"/>\n'
            f'      <animate attributeName="r" values="26;32;26" dur="4.5s"'
            f' begin="{begin}s" repeatCount="indefinite"/>\n'
            "    </circle>\n"
            f'    <text x="{x}" y="86" text-anchor="middle" font-family="{UI}"'
            f' font-weight="700" font-size="22" fill="{color}">{i + 1}</text>\n'
            f'    <text x="{x}" y="128" text-anchor="middle" font-family="{UI}"'
            f' font-weight="700" font-size="15" fill="{PALE}">{title}</text>\n'
            f'    <text x="{x}" y="148" text-anchor="middle" font-family="{UI}"'
            f' font-size="11" fill="{LILAC}">{under}</text>\n'
            "  </g>\n"
        )
        if i < len(beats) - 1:
            out.append(
                f'  <line x1="{x + 30}" y1="78" x2="{x + span - 30}" y2="78"'
                f' stroke="{PURPLE}" stroke-width="2" opacity="0.4"/>\n'
                f'  <circle cx="{x + 30}" cy="78" r="3" fill="{PALE}">\n'
                f'    <animate attributeName="cx" values="{x + 30};{x + span - 30}"'
                f' dur="0.9s" begin="{begin + 0.3}s" repeatCount="indefinite"/>\n'
                "  </circle>\n"
            )
    out.append("</svg>\n")
    return "".join(out)


def kit_grades() -> list[tuple[str, str, list[tuple[str, str]]]]:
    """Grade every fighter from their own kit, so the chart shows measured values.

    Nothing here is decided by hand: the numbers come out of characters/*.toml.
    """
    from jojo_arena.characters import load_roster

    def grade(value: float, scale: list[float]) -> str:
        for mark, bound in zip("ABCDE", scale, strict=True):
            if value >= bound:
                return mark
        return "E"

    rows = []
    for entry in load_roster():
        if entry.id not in ("jotaro_p3", "wamuu", "kars", "caesar"):
            continue
        moves = [m for m in entry.kit.all_moves() if m.radius > 0 or m.projectile]
        hits = [m for m in moves if m.damage]
        power = max((m.damage * max(1, m.hits) for m in hits), default=0)
        speed = min((m.startup_f for m in hits), default=30)
        reach = max((m.reach for m in moves), default=0)
        stances = len(entry.kit.stances)
        life = entry.kit.max_hp
        rows.append(
            (
                entry.name.split()[0],
                entry.color,
                [
                    ("PUISSANCE", grade(power, [240, 170, 120, 80, 0])),
                    ("VITESSE", grade(-speed, [-4, -5, -6, -8, -99])),
                    ("PORTÉE", grade(reach, [150, 90, 50, 25, 0])),
                    ("VIE", grade(life, [1200, 1100, 1000, 900, 0])),
                    ("MOVESETS", grade(stances, [3, 2, 2, 1, 0])),
                ],
            )
        )
    return rows


def stats_card() -> str:
    """The stat chart of the manga, filled from what the kits actually say."""
    rows = kit_grades()
    headings = [name for name, _ in rows[0][2]]
    grades = {"A": 1.0, "B": 0.78, "C": 0.56, "D": 0.34, "E": 0.14}
    width = 960
    height = 74 + 52 * len(rows)
    out = [header(width, height, "Fiches de stats", "Les stats, calculees depuis les kits.")]
    out.append(f'  <rect width="{width}" height="{height}" fill="{NIGHT}"/>\n')
    left = 150
    column = (width - left - 46) / len(headings)
    for i, heading in enumerate(headings):
        x = left + column * (i + 0.5)
        out.append(
            f'  <text x="{x}" y="30" text-anchor="middle" font-family="{UI}"'
            f' font-size="11" fill="{LILAC}" letter-spacing="1">{heading}</text>\n'
        )
    for row, (name, color, marks) in enumerate(rows):
        y = 66 + row * 52
        for i, (_, mark) in enumerate(marks):
            x = left + column * i + 6
            full = column - 20
            size = full * grades[mark]
            begin = row * 0.3 + i * 0.08
            out.append(
                f'  <rect x="{x}" y="{y - 10}" width="{full}" height="12" rx="2"'
                f' fill="{PURPLE}" opacity="0.22"/>\n'
                f'  <rect x="{x}" y="{y - 10}" width="0" height="12" rx="2" fill="{color}">\n'
                f'    <animate attributeName="width" values="0;{size:.1f}" dur="0.8s"'
                f' begin="{begin}s" fill="freeze"/>\n'
                "  </rect>\n"
                f'  <text x="{x + full + 7}" y="{y}" font-family="{UI}" font-weight="700"'
                f' font-size="12" fill="{PALE}" opacity="0">{mark}\n'
                f'    <animate attributeName="opacity" values="0;1" dur="0.3s"'
                f' begin="{begin + 0.7}s" fill="freeze"/>\n'
                "  </text>\n"
            )
        out.append(
            f'  <text x="24" y="{y + 6}" font-family="{UI}" font-weight="700"'
            f' font-size="18" fill="{color}">{name}</text>\n'
        )
    out.append("</svg>\n")
    return "".join(out)


def divider() -> str:
    """A thin manga divider: speed lines sweeping, with the menace on top of them."""
    width, height = 960, 30
    out = [header(width, height, "Separateur", "Lignes de vitesse.")]
    for i in range(26):
        x = i * 38
        out.append(
            f'  <line x1="{x}" y1="26" x2="{x + 30}" y2="4" stroke="{PURPLE}"'
            f' stroke-width="2" opacity="0.35">\n'
            f'    <animate attributeName="opacity" values="0.12;0.5;0.12" dur="2.4s"'
            f' begin="{i * 0.07}s" repeatCount="indefinite"/>\n'
            "  </line>\n"
        )
    out.append(
        f'  <text x="480" y="22" text-anchor="middle" font-family="{JP}" font-weight="700"'
        f' font-size="18" fill="{GOLD}" opacity="0.8">ゴ ゴ ゴ ゴ ゴ</text>\n'
    )
    out.append("</svg>\n")
    return "".join(out)


ASCII_FIGHT = [
    [
        "   o                                        o   ",
        "  /|\\        . . . . . . . . . . .        /|\\  ",
        "  / \\                                     / \\  ",
        "              approche, garde haute             ",
    ],
    [
        "       o                            o           ",
        "      /|\\      >>>        <<<      /|\\          ",
        "      / \\                          / \\          ",
        "            les deux avancent                   ",
    ],
    [
        "          o                    o                ",
        "         /|X====  CLASH!  ====X|\\               ",
        "         / \\                  / \\              ",
        "        deux coups se croisent : on martele     ",
    ],
    [
        "          o                                     ",
        "         /|/  ORA ORA ORA ORA ORA  >>>  o       ",
        "         / \\                           /|\\     ",
        "        seize coups, six degats chacun          ",
    ],
    [
        "          o                                     ",
        "         /|\\   ***  ZA WARUDO  ***      o       ",
        "         / \\                           -+-      ",
        "        le temps s'arrete : personne ne bouge   ",
    ],
    [
        "          o                                     ",
        "         /|\\  ======  DORARARA  ======>  x      ",
        "         / \\                            /|\\    ",
        "        la cinematique part : K.O.              ",
    ],
]


def ascii_fight() -> str:
    """A whole exchange in ASCII, one frame at a time, the way a terminal would show it."""
    width, height = 660, 200
    hold = 1.6
    total = hold * len(ASCII_FIGHT)
    out = [header(width, height, "Un echange en ASCII", "Les six temps d'un echange.")]
    out.append(f'  <rect width="{width}" height="{height}" rx="8" fill="#0f0b17"/>\n')
    out.append(
        f'  <rect x="0" y="0" width="{width}" height="26" rx="8" fill="#241b33"/>\n'
        f'  <circle cx="18" cy="13" r="5" fill="{BLOOD}"/>\n'
        f'  <circle cx="36" cy="13" r="5" fill="{GOLD}"/>\n'
        f'  <circle cx="54" cy="13" r="5" fill="{JADE}"/>\n'
        f'  <text x="80" y="18" font-family="monospace" font-size="12"'
        f' fill="{LILAC}">jojo-arena — un round</text>\n'
    )
    for i, frame in enumerate(ASCII_FIGHT):
        begin = i * hold
        out.append('  <g opacity="0">\n')
        out.append(
            f'    <animate attributeName="opacity" values="0;1;1;0"'
            f' keyTimes="0;0.06;0.94;1" dur="{hold}s" begin="{begin}s"'
            f' repeatCount="indefinite" repeatDur="{total * 99}s"/>\n'
        )
        for line_no, line in enumerate(frame):
            colour = LILAC if line_no == 3 else PALE
            size = 13 if line_no == 3 else 15
            line = escape(line)
            out.append(
                f'    <text x="26" y="{60 + line_no * 26}" font-family="monospace"'
                f' font-size="{size}" fill="{colour}" xml:space="preserve">{line}</text>\n'
            )
        out.append("  </g>\n")
    out.append("</svg>\n")
    return "".join(out)


def terminal(lines: list[tuple[str, str]], title: str, width: int = 900) -> str:
    """A terminal window drawn as SVG, from lines the repo really printed."""
    height = 48 + 18 * len(lines)
    out = [header(width, height, title, "Sortie reelle d'une commande du depot.")]
    out.append(f'  <rect width="{width}" height="{height}" rx="8" fill="#0f0b17"/>\n')
    out.append(
        f'  <rect x="0" y="0" width="{width}" height="26" rx="8" fill="#241b33"/>\n'
        f'  <circle cx="18" cy="13" r="5" fill="{BLOOD}"/>\n'
        f'  <circle cx="36" cy="13" r="5" fill="{GOLD}"/>\n'
        f'  <circle cx="54" cy="13" r="5" fill="{JADE}"/>\n'
        f'  <text x="80" y="18" font-family="monospace" font-size="12"'
        f' fill="{LILAC}">{title}</text>\n'
    )
    for i, (text_line, colour) in enumerate(lines):
        safe = escape(text_line)
        out.append(
            f'  <text x="18" y="{46 + i * 18}" font-family="monospace" font-size="13"'
            f' fill="{colour}" xml:space="preserve" opacity="0">{safe}\n'
            f'    <animate attributeName="opacity" values="0;1" dur="0.2s"'
            f' begin="{i * 0.12}s" fill="freeze"/>\n'
            "  </text>\n"
        )
    out.append("</svg>\n")
    return "".join(out)


def audit_terminal() -> str:
    """Run the audit for real and draw what it printed: a README that copies a result by
    hand ends up lying about it."""
    import contextlib
    import io

    from tools import audit_kits

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        audit_kits.main()
    keep, lines = [], buffer.getvalue().splitlines()
    for line in lines:
        if line.startswith("=="):
            keep.append((line, GOLD))
        elif "aucun" in line or ": 0 ==" in line:
            keep.append((line, JADE))
        elif "partage dans l" in line or "partagé dans l" in line:
            keep.append((line, LILAC))
        elif line.strip():
            keep.append((line, PALE))
        if len(keep) >= 14:
            break
    keep.insert(0, ("$ python tools/audit_kits.py", GOLD))
    return terminal(keep, "audit_kits.py — ce qui se repete d'un perso a l'autre")


def profile_card() -> str:
    """A card for a GitHub profile: the project, who writes it, and the menace around it."""
    width, height = 820, 240
    out = [header(width, height, "JoJo Arena — carte de projet", "Carte pour un profil GitHub.")]
    out.append(f'  <rect width="{width}" height="{height}" rx="14" fill="{NIGHT}"/>\n')
    out.append(
        f'  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="14"'
        f' fill="none" stroke="{PURPLE}" stroke-width="2" opacity="0.6"/>\n'
    )
    for x, y, delay in ((40, 210, 0.0), (90, 226, 0.3), (700, 70, 0.6), (760, 54, 0.9)):
        out.append(menace(x, y, delay, 34))
    out.append(
        f'  <text x="40" y="76" font-family="{UI}" font-weight="700" font-size="42"'
        f' fill="{GOLD}">JOJO ARENA</text>\n'
        f'  <text x="40" y="104" font-family="{UI}" font-size="15" fill="{LILAC}">'
        "Arena fighter 1v1 · pixel art vu de dessus · fan game</text>\n"
        f'  <text x="40" y="140" font-family="{UI}" font-size="13" fill="{PALE}">'
        "Python 3.12 · pygame-ce · simulation deterministe a 60 Hz</text>\n"
        f'  <text x="40" y="162" font-family="{UI}" font-size="13" fill="{PALE}">'
        f"19 persos · 3 arenes · {test_count()} tests · 94 % de couverture</text>\n"
    )
    # The line that says who writes it, with a Ripple running under it.
    out.append(
        f'  <text x="40" y="202" font-family="{UI}" font-weight="700" font-size="16"'
        f' fill="{PALE}">developpe par Hamza Karrouchi</text>\n'
        f'  <rect x="40" y="210" width="240" height="2" fill="{GOLD}" opacity="0.3"/>\n'
        f'  <rect x="40" y="209" width="60" height="4" rx="2" fill="{PALE}">\n'
        f'    <animate attributeName="x" values="40;220;40" dur="4s" repeatCount="indefinite"/>\n'
        "  </rect>\n"
    )
    # ORA / MUDA drifting on the right, the way they drift across the fight.
    for i, (word, colour, y, dur) in enumerate(
        (("ORA", GOLD, 96, 5.0), ("MUDA", "#7ab8f0", 134, 6.0), ("ドドド", PURPLE, 172, 4.4))
    ):
        out.append(
            f'  <text x="560" y="{y}" font-family="{JP if i == 2 else UI}" font-weight="700"'
            f' font-size="26" fill="{colour}" opacity="0.5">{word}\n'
            f'    <animate attributeName="x" values="560;700;560" dur="{dur}s"'
            ' repeatCount="indefinite"/>\n'
            f'    <animate attributeName="opacity" values="0.2;0.7;0.2" dur="{dur}s"'
            ' repeatCount="indefinite"/>\n'
            "  </text>\n"
        )
    out.append("</svg>\n")
    return "".join(out)


def faces(out_dir: Path) -> list[Path]:
    """One face per fighter, rendered by the game's own sprite generator."""
    import pygame

    from jojo_arena.characters import load_roster
    from jojo_arena.ui.portraits import FighterLook

    pygame.init()
    folder = out_dir / "faces"
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for entry in load_roster():
        if not entry.selectable:
            continue
        look = FighterLook(entry)
        face = pygame.transform.scale_by(look.face(22), 3)
        path = folder / f"{entry.id}.png"
        pygame.image.save(face, str(path))
        written.append(path)
    pygame.quit()
    return written


def frames() -> str:
    """A frame meter, with the numbers read from the kit itself.

    Startup, active frames and recovery of one real blow, and what it leaves on block -
    what the training room shows, drawn the same way."""
    from jojo_arena.characters import get_fighter
    from jojo_arena.combat.framedata import frame_data, signed
    from jojo_arena.combat.rules import load_rules

    rules = load_rules()
    kit = get_fighter("jotaro_p3").kit
    move = kit.move("stand", "light") or kit.move(kit.base_stance_name, "light")
    data = frame_data(move, rules)
    bands = [
        ("DÉMARRAGE", data.startup, "#5a9ef0"),
        ("ACTIF", data.active, BLOOD),
        ("RÉCUPÉRATION", data.recovery, PURPLE),
    ]
    total = sum(count for _, count, _ in bands)
    width, height = 960, 186
    out = [header(width, height, "Une frise de frames", "Le frame meter du mode entraînement.")]
    out.append(f'  <rect width="{width}" height="{height}" fill="{NIGHT}"/>\n')
    out.append(
        f'  <text x="26" y="34" font-family="{UI}" font-weight="700" font-size="17"'
        f' fill="{GOLD}">{move.label}</text>\n'
        f'  <text x="26" y="54" font-family="{UI}" font-size="12" fill="{LILAC}">'
        f"{total} images en tout, à 60 par seconde — lues dans characters/jotaro_p3.toml</text>\n"
    )
    left, right = 26, width - 26
    span = right - left
    cycle = total / 60
    x = left
    for label, count, color in bands:
        run = span * count / total
        out.append(
            f'  <rect x="{x}" y="72" width="{run - 3}" height="34" rx="3" fill="{color}"'
            f' opacity="0.9"/>\n'
            f'  <text x="{x + run / 2}" y="94" text-anchor="middle" font-family="{UI}"'
            f' font-weight="700" font-size="13" fill="{NIGHT}">{count}</text>\n'
            f'  <text x="{x + run / 2}" y="126" text-anchor="middle" font-family="{UI}"'
            f' font-size="11" fill="{LILAC}" letter-spacing="1">{label}</text>\n'
        )
        x += run
    # The playhead runs the length of the move, at the speed the move really takes.
    out.append(
        f'  <rect x="{left}" y="66" width="3" height="46" fill="{PALE}">\n'
        f'    <animate attributeName="x" values="{left};{right}" dur="{cycle:.2f}s"'
        ' repeatCount="indefinite"/>\n'
        "  </rect>\n"
    )
    readings = (
        ("SUR TOUCHE", signed(data.on_hit), JADE),
        ("SUR GARDE", signed(data.on_block), BLOOD if (data.on_block or 0) < 0 else JADE),
    )
    for i, (label, value, color) in enumerate(readings):
        cx = left + 150 + i * 240
        out.append(
            f'  <text x="{cx}" y="160" font-family="{UI}" font-size="12"'
            f' fill="{LILAC}">{label}</text>\n'
            f'  <text x="{cx + 96}" y="162" font-family="{UI}" font-weight="700"'
            f' font-size="18" fill="{color}">{value}</text>\n'
        )
    out.append(
        f'  <text x="{right}" y="161" text-anchor="end" font-family="{UI}" font-size="11"'
        f' fill="{LILAC}">mesuré par le jeu, pas recopié à la main</text>\n'
    )
    out.append("</svg>\n")
    return "".join(out)


def statuses() -> str:
    """What a blow can leave behind: the three status effects, with the numbers that are
    really in rules.toml."""
    from jojo_arena.combat.rules import load_rules

    rules = load_rules()
    rows = [
        ("burn", "FEU", "#f0901c", "sang bouillant, lance-flammes", "la plaie ne se referme plus"),
        ("chill", "GEL", "#9ad8ff", "congélation par vaporisation", "ni onde respirée, ni sang bu"),
        ("shock", "COURANT", "#f0d020", "l'onde conduite par une écharpe", "la garde se défait"),
    ]
    width, height = 960, 60 + 74 * len(rows)
    out = [header(width, height, "Les altérations d'état", "Feu, gel, courant.")]
    out.append(f'  <rect width="{width}" height="{height}" fill="{NIGHT}"/>\n')
    out.append(
        f'  <text x="26" y="36" font-family="{UI}" font-weight="700" font-size="17"'
        f" fill=\"{GOLD}\">CE QU'UN COUP LAISSE DERRIÈRE LUI</text>\n"
    )
    for i, (key, name, color, who, effect) in enumerate(rows):
        defn = rules.statuses[key]
        y = 76 + i * 74
        seconds = defn.max_f / 60
        out.append(
            f'  <rect x="26" y="{y - 22}" width="{width - 52}" height="56" rx="6"'
            f' fill="{color}" opacity="0.07"/>\n'
            f'  <circle cx="60" cy="{y + 6}" r="15" fill="{color}" opacity="0.25">\n'
            f'    <animate attributeName="opacity" values="0.15;0.5;0.15" dur="1.4s"'
            f' begin="{i * 0.35}s" repeatCount="indefinite"/>\n'
            "  </circle>\n"
            f'  <circle cx="60" cy="{y + 6}" r="7" fill="{color}">\n'
            f'    <animate attributeName="r" values="6;9;6" dur="1.4s" begin="{i * 0.35}s"'
            ' repeatCount="indefinite"/>\n'
            "  </circle>\n"
            f'  <text x="92" y="{y + 2}" font-family="{UI}" font-weight="700" font-size="16"'
            f' fill="{color}">{name}</text>\n'
            f'  <text x="92" y="{y + 22}" font-family="{UI}" font-size="12"'
            f' fill="{LILAC}">{who}</text>\n'
            f'  <text x="330" y="{y + 2}" font-family="{UI}" font-size="13"'
            f' fill="{PALE}">{effect}</text>\n'
            f'  <text x="330" y="{y + 22}" font-family="{UI}" font-size="11"'
            f' fill="{LILAC}">{seconds:.1f} s au plus, relancé par un second coup,'
            " jamais empilé</text>\n"
        )
        # A bar draining, the way the status itself drains away.
        bar_x, bar_w = 700, 220
        out.append(
            f'  <rect x="{bar_x}" y="{y - 4}" width="{bar_w}" height="12" rx="3"'
            f' fill="{PURPLE}" opacity="0.25"/>\n'
            f'  <rect x="{bar_x}" y="{y - 4}" width="{bar_w}" height="12" rx="3"'
            f' fill="{color}">\n'
            f'    <animate attributeName="width" values="{bar_w};0" dur="{seconds:.1f}s"'
            ' repeatCount="indefinite"/>\n'
            "  </rect>\n"
        )
    out.append("</svg>\n")
    return "".join(out)


def camps() -> str:
    """The two camps of the title screen, walking into each other."""
    from jojo_arena.characters import load_roster

    roster = [f for f in load_roster() if f.selectable]
    sides = (
        ([f.name for f in roster if f.side == "hero"], "#5ad0a0", -1, "AVEC LES JOESTAR"),
        ([f.name for f in roster if f.side == "villain"], BLOOD, 1, "CONTRE EUX"),
    )
    width, height = 960, 160
    out = [header(width, height, "Les deux camps", "Gentils et méchants, face à face.")]
    out.append(f'  <rect width="{width}" height="{height}" fill="{NIGHT}"/>\n')
    out.append(menace(30, 150, 0.2, 30))
    out.append(menace(900, 50, 0.8, 30))
    for names, color, way, title in sides:
        anchor = width / 2 + way * 70
        out.append(
            f'  <text x="{anchor + way * 170}" y="40" text-anchor="middle"'
            f' font-family="{UI}" font-weight="700" font-size="14" fill="{color}"'
            f' letter-spacing="2">{title}</text>\n'
        )
        for i, name in enumerate(names):
            row, column = divmod(i, 2)
            x = anchor + way * (30 + column * 150)
            y = 72 + row * 22
            out.append(
                f'  <text x="{x}" y="{y}" text-anchor="{"end" if way < 0 else "start"}"'
                f' font-family="{UI}" font-size="12" fill="{PALE}" opacity="0">{name}\n'
                f'    <animate attributeName="opacity" values="0;1;1;0.6" keyTimes='
                f'"0;0.2;0.85;1" dur="5s" begin="{0.1 * i:.1f}s" repeatCount="indefinite"/>\n'
                f'    <animate attributeName="x" values="{x + way * 24};{x}" dur="0.8s"'
                f' begin="{0.1 * i:.1f}s" repeatCount="indefinite"/>\n'
                "  </text>\n"
            )
    out.append(
        f'  <text x="{width / 2}" y="100" text-anchor="middle" font-family="{UI}"'
        f' font-weight="700" font-size="30" fill="{GOLD}">VS\n'
        '    <animate attributeName="font-size" values="28;34;28" dur="1.6s"'
        ' repeatCount="indefinite"/>\n'
        "  </text>\n"
    )
    out.append("</svg>\n")
    return "".join(out)


DRAWINGS = {
    "chiffres": counters,
    "boucle": loop,
    "stats": stats_card,
    "separateur": divider,
    "ascii": ascii_fight,
    "audit": audit_terminal,
    "carte": profile_card,
    "frames": frames,
    "etats": statuses,
    "camps": camps,
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("only", nargs="*", help=f"one of: {', '.join(DRAWINGS)}, faces")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    wanted = args.only or [*DRAWINGS, "faces"]
    args.out.mkdir(parents=True, exist_ok=True)
    for name in wanted:
        if name == "faces":
            written = faces(args.out)
            print(f"{len(written)} faces -> {args.out / 'faces'}")
            continue
        path = args.out / f"{name}.svg"
        path.write_text(DRAWINGS[name](), encoding="utf-8")
        print(f"{path} ({path.stat().st_size // 1024 or 1} KB)")


if __name__ == "__main__":
    main()
