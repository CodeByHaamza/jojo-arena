"""The player's sound pack: say what it should hold, check what it holds, cut files into it.

    python tools/sound_pack.py manifest     # write MANIFEST.md in the pack: every file wanted
    python tools/sound_pack.py check        # what the pack has, what it lacks, what it has in vain
    python tools/sound_pack.py cut          # cut the files of the pack's inbox (needs ffmpeg)

The pack is a folder beside the player's settings, never part of the game or of its
repository (see jojo_arena/ui/sound_pack.py). `cut` reads `inbox/cuts.toml` in the pack:

    [[cut]]
    file = "some_recording.wav"            # a file of the inbox
    slot = "voices/jotaro_p3/stand.heavy"  # where it goes (a name of the manifest)
    start = 12.4                           # seconds; leave both out to take the whole file
    end = 13.9
    gain_db = 0                            # louder (+) or quieter (-), after levelling
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jojo_arena.characters import load_roster  # noqa: E402
from jojo_arena.characters.lines import load_exchanges  # noqa: E402
from jojo_arena.controls import controls_path  # noqa: E402
from jojo_arena.engine import i18n  # noqa: E402
from jojo_arena.engine.audio import SOUND_FILES  # noqa: E402
from jojo_arena.stages import STAGE_IDS  # noqa: E402
from jojo_arena.ui.music import TRACKS  # noqa: E402
from jojo_arena.ui.sound_pack import Slot, expected_slots, pack_dir  # noqa: E402
from jojo_arena.ui.sounds import build_sounds  # noqa: E402

KINDS = {"sfx": "Bruitages", "music": "Musique", "voices": "Voix"}
MUSIC_NOTES = {"menu": "les menus"}
VOICE_NOTES = {
    "pose": "sa provocation : la touche Pose, et son entrée en scène sans réplique",
    "win": "sa victoire, quand il n'a pas de réplique pour cet adversaire",
    "ko": "son K.O.",
}
# What each effect of the game is, for whoever fills the pack (the game synthesizes them
# all: a file here plays in its place).
SFX_NOTES = {
    "hit": "un coup léger qui touche",
    "hit_heavy": "un coup lourd qui touche",
    "whoosh": "un coup qui part, un dash",
    "block": "un coup bloqué par la garde",
    "guard_break": "la garde qui casse",
    "clash": "deux coups qui se rencontrent (clash)",
    "time_stop": "le temps s'arrête",
    "time_resume": "le temps reprend son cours",
    "ko": "le K.O.",
    "super": "un ultime qui démarre (Heart Heat)",
    "hamon": "le Hamon : étincelles de l'Onde sur un coup",
    "freeze": "le gel (Dio, partie 1)",
    "sizzle": "ce qui brûle : le feu, le soleil sur un vampire",
    "chain": "des chaînes",
    "beam": "un rayon (les yeux de Dio, de Straizo)",
    "boom": "une explosion",
    "pop": "une bulle qui éclate",
    "wind": "le vent (Wamuu)",
    "splat": "de la chair (Santana)",
    "blade": "une lame",
    "gunshot": "un coup de feu",
    "stylish": "une esquive stylée, une prédiction juste",
    "menu_move": "menu : le curseur bouge",
    "menu_ok": "menu : valider",
    "menu_back": "menu : retour",
    "menu_locked": "menu : choix indisponible",
}


class _Names:
    """Stands in for the audio player while the game lists its effects."""

    def __init__(self) -> None:
        self.names: list[str] = []

    def add(self, name: str, samples) -> None:
        self.names.append(name)


def sfx_names() -> list[str]:
    """The name of every effect the game synthesizes."""
    listing = _Names()
    build_sounds(listing)
    return listing.names


def wanted() -> list[Slot]:
    """Every file a complete pack holds, with what goes in each. The lines two fighters
    exchange are given as the games say them (in English): that is what to look for."""
    tracks = set(TRACKS) | set(STAGE_IDS)
    language = i18n.language()
    i18n.set_language("en")
    try:
        slots = expected_slots(load_roster(), load_exchanges(), sfx_names(), tracks)
    finally:
        i18n.set_language(language)
    noted = []
    for slot in slots:
        hint = slot.hint
        short = slot.name.split("/", 1)[1]
        if slot.kind == "sfx":
            hint = SFX_NOTES.get(short, "")
        elif slot.kind == "music":
            hint = MUSIC_NOTES.get(short, f"l'arène « {short} »")
        elif not hint:
            hint = VOICE_NOTES.get(short.rsplit("/", 1)[-1], "")
        noted.append(Slot(slot.name, slot.kind, hint))
    return noted


def manifest_text(slots: list[Slot]) -> str:
    """The manifest: one table per kind, one line per file, with what goes in it."""
    lines = [
        "# Pack de sons : ce qu'il peut contenir",
        "",
        "Écrit par `tools/sound_pack.py manifest`. Un fichier par ligne, en `.ogg` ou `.wav`,",
        "au nom indiqué. Un fichier absent n'est pas une erreur : le jeu joue alors son propre",
        "son (ou rien, pour une voix).",
    ]
    for kind, title in KINDS.items():
        rows = [slot for slot in slots if slot.kind == kind]
        lines += [
            "",
            f"## {title} ({len(rows)})",
            "",
            "| Fichier | Ce que c'est |",
            "| --- | --- |",
        ]
        lines += [f"| `{slot.name}` | {slot.hint} |" for slot in rows]
    return "\n".join(lines) + "\n"


def found(folder: Path) -> set[str]:
    """The slots the pack fills: its sound files, by name without the extension."""
    names = set()
    for kind in KINDS:
        base = folder / kind
        for path in base.rglob("*") if base.is_dir() else ():
            if path.is_file() and path.suffix.lower() in SOUND_FILES:
                names.add(f"{kind}/{path.relative_to(base).with_suffix('').as_posix()}")
    return names


def check_text(slots: list[Slot], have: set[str]) -> str:
    names = {slot.name for slot in slots}
    lines = []
    for kind, title in KINDS.items():
        of_kind = [slot.name for slot in slots if slot.kind == kind]
        filled = [name for name in of_kind if name in have]
        lines.append(f"{title} : {len(filled)}/{len(of_kind)}")
    stray = sorted(have - names)
    if stray:
        lines += ["", "Dans le pack, mais à aucun emplacement du jeu :"]
        lines += [f"  {name}" for name in stray]
    return "\n".join(lines)


def cut_command(source: Path, target: Path, cut: dict) -> list[str]:
    """The ffmpeg call that cuts one file into its slot: trimmed, levelled, the format the
    game reads (voices and effects in mono, music left in stereo)."""
    command = ["ffmpeg", "-y", "-loglevel", "error"]
    if "start" in cut:
        command += ["-ss", str(cut["start"])]
    if "end" in cut:
        command += ["-to", str(cut["end"])]
    command += ["-i", str(source)]
    filters = ["loudnorm=I=-16:TP=-1.5"]
    if cut.get("gain_db"):
        filters.append(f"volume={cut['gain_db']}dB")
    music = cut["slot"].startswith("music/")
    command += ["-af", ",".join(filters), "-ac", "2" if music else "1"]
    command += ["-ar", "44100" if music else "22050", "-c:a", "libvorbis", "-q:a", "5"]
    return [*command, str(target)]


def cut_all(folder: Path) -> list[str]:
    """Cut every entry of inbox/cuts.toml into the pack. Returns what was written."""
    inbox = folder / "inbox"
    plan = inbox / "cuts.toml"
    if not plan.exists():
        raise SystemExit(f"rien à couper : {plan} n'existe pas")
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg est introuvable : installe-le, puis relance")
    known = {slot.name for slot in wanted()}
    written = []
    for cut in tomllib.loads(plan.read_text(encoding="utf-8")).get("cut", []):
        source, slot = inbox / cut["file"], cut["slot"]
        if not source.exists():
            raise SystemExit(f"{source} n'existe pas")
        if slot not in known:
            raise SystemExit(f"« {slot} » n'est pas un emplacement du jeu (voir MANIFEST.md)")
        target = folder / f"{slot}.ogg"
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(cut_command(source, target, cut), check=True)
        written.append(slot)
    return written


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("action", choices=["manifest", "check", "cut"])
    parser.add_argument("--pack", type=Path, help="the pack folder (default: beside the settings)")
    args = parser.parse_args(argv)
    folder = args.pack or pack_dir(controls_path())
    if args.action == "manifest":
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "MANIFEST.md"
        target.write_text(manifest_text(wanted()), encoding="utf-8")
        print(f"{len(wanted())} emplacements -> {target}")
    elif args.action == "check":
        print(f"Pack : {folder}")
        print(check_text(wanted(), found(folder)))
    else:
        for slot in cut_all(folder):
            print(f"coupé : {slot}")


if __name__ == "__main__":
    main()
