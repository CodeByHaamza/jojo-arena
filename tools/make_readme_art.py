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


def counters() -> str:
    """The numbers that say what the project is, counting up as you look at them."""
    figures = [
        ("19", "PERSOS JOUABLES", GOLD),
        ("3", "ARÈNES", JADE),
        ("941", "TESTS", "#5a9ef0"),
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


DRAWINGS = {
    "chiffres": counters,
    "boucle": loop,
    "stats": stats_card,
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
