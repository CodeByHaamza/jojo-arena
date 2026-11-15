"""The sound pack: a folder of real sound files beside the player's settings, read in place
of what the game synthesizes. The engine reads folders, the game names the slots, the tool
says what a pack should hold and cuts files into it. No sound file is part of the game."""

import sys
import wave
from pathlib import Path

import pygame
import pytest
from helpers import NONE, make_duel, press

from jojo_arena.characters import get_fighter, load_roster
from jojo_arena.characters.lines import load_exchanges
from jojo_arena.engine import audio, music
from jojo_arena.engine.audio import AudioPlayer
from jojo_arena.engine.music import MusicPlayer
from jojo_arena.stages import load_stage
from jojo_arena.ui import sounds
from jojo_arena.ui.fight_view import FightView
from jojo_arena.ui.music import TRACKS, track_for_stage
from jojo_arena.ui.sound_pack import (
    expected_slots,
    generic_slot,
    line_slot,
    load_pack,
    move_slot,
    pack_dir,
    say,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import sound_pack as tool  # noqa: E402  (tools/sound_pack.py)


def beep(path: Path, frames: int = 400) -> Path:
    """A tiny valid sound file: a few silent samples."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(22050)
        out.writeframes(b"\x00\x00" * frames)
    return path


@pytest.fixture
def mixer(monkeypatch):
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.quit()
    pygame.mixer.init(22050, -16, 1, 512)
    yield
    audio.set_player(None)
    music.set_player(None)
    pygame.mixer.quit()


class Heard:
    """Stands in for the audio player: knows some sounds, keeps what was played."""

    def __init__(self, known=()) -> None:
        self.known = set(known)
        self.played: list[str] = []

    def add(self, name, samples) -> None:
        self.known.add(name)

    def has(self, name: str) -> bool:
        return name in self.known

    def play(self, name: str, volume: float = 1.0) -> bool:
        if name not in self.known:
            return False
        self.played.append(name)
        return True


@pytest.fixture
def heard():
    player = Heard()
    audio.set_player(player)
    yield player
    audio.set_player(None)


# The engine reads a folder of sounds -------------------------------------------------------------


def test_a_folder_of_sounds_is_read_by_path_without_the_extension(mixer, tmp_path):
    beep(tmp_path / "boom.wav")
    beep(tmp_path / "someone" / "shout.wav")
    (tmp_path / "notes.txt").write_text("not a sound")
    player = AudioPlayer()
    assert player.load_folder(tmp_path, prefix="voices/") == [
        "voices/boom",
        "voices/someone/shout",
    ]
    assert player.has("voices/someone/shout") and not player.has("voices/notes")
    assert player.play("voices/boom") is True
    assert player.play("voices/nobody") is False


def test_a_file_read_from_a_folder_replaces_the_sound_of_that_name(mixer, tmp_path):
    player = AudioPlayer()
    sounds.build_sounds(player)
    synthesized = player.sounds["time_stop"]
    beep(tmp_path / "time_stop.wav")
    assert player.load_folder(tmp_path) == ["time_stop"]
    assert player.sounds["time_stop"] is not synthesized


def test_a_missing_folder_or_a_broken_file_is_no_sound_and_no_error(mixer, tmp_path):
    player = AudioPlayer()
    assert player.load_folder(tmp_path / "nothing_here") == []
    (tmp_path / "broken.wav").write_bytes(b"this is not audio")
    beep(tmp_path / "fine.wav")
    assert player.load_folder(tmp_path) == ["fine"]


def test_music_files_stand_in_for_rendered_tracks_and_add_their_own(mixer, tmp_path):
    beep(tmp_path / "menu.wav")
    beep(tmp_path / "somewhere_new.wav")
    player = MusicPlayer({})
    assert player.load_folder(tmp_path) == ["menu", "somewhere_new"]
    assert player.has("somewhere_new") and not player.has("nowhere")
    player.request("somewhere_new")
    player.tick()
    assert player._playing == "somewhere_new"


# The game names the slots ---------------------------------------------------------------------


def test_a_move_has_its_slot_and_a_super_is_the_same_in_every_stance():
    kit = get_fighter("jotaro_p3").kit
    star_finger = kit.move("stand", "special_alt")
    assert move_slot("jotaro_p3", kit, "stand", star_finger) == "voices/jotaro_p3/stand.special_alt"
    gha = kit.move("base", "gha")
    assert move_slot("jotaro_p3", kit, "base", gha) == "voices/jotaro_p3/gha"
    assert move_slot("jotaro_p3", kit, "stand", gha) == "voices/jotaro_p3/gha"
    assert line_slot("jotaro_p3", "intro", "dio_p3") == "voices/jotaro_p3/intro.dio_p3"
    assert generic_slot("dio_p3", "ko") == "voices/dio_p3/ko"


def test_say_plays_the_first_slot_the_pack_has(heard):
    heard.known = {"voices/a/win"}
    assert say("voices/a/victory.b", "voices/a/win") is True
    assert heard.played == ["voices/a/win"]
    assert say("voices/a/victory.b") is False


def test_without_audio_nothing_is_said():
    audio.set_player(None)
    assert say("voices/a/win") is False


def test_the_pack_lives_beside_the_players_settings(tmp_path):
    assert pack_dir(tmp_path / "controls.json") == tmp_path / "sound_pack"


def test_the_game_reads_the_three_folders_of_a_pack(mixer, tmp_path):
    audio.set_player(AudioPlayer())
    music.set_player(MusicPlayer(TRACKS))
    sounds.build_sounds(audio._player)
    beep(tmp_path / "sfx" / "time_stop.wav")
    beep(tmp_path / "music" / "swiss_castle.wav")
    beep(tmp_path / "voices" / "dio_p3" / "stand.special.wav")
    assert track_for_stage("swiss_castle") == "menu"  # no track of its own, so far
    loaded = load_pack(tmp_path)
    assert loaded == {
        "sfx": ["time_stop"],
        "music": ["swiss_castle"],
        "voices": ["voices/dio_p3/stand.special"],
    }
    assert audio.has("voices/dio_p3/stand.special")
    assert track_for_stage("swiss_castle") == "swiss_castle"  # the pack brings one
    assert track_for_stage("cairo_night") == "cairo_night"


def test_no_pack_changes_nothing(mixer, tmp_path):
    audio.set_player(AudioPlayer())
    music.set_player(MusicPlayer(TRACKS))
    assert load_pack(tmp_path / "sound_pack") == {"sfx": [], "music": [], "voices": []}


def test_every_shout_and_every_line_has_a_slot_and_no_slot_twice():
    roster = [f for f in load_roster() if f.selectable]
    exchanges = load_exchanges()
    slots = expected_slots(roster, exchanges, ["hit"], ["menu"])
    names = [slot.name for slot in slots]
    assert len(names) == len(set(names))
    for fighter in roster:
        for stance_name, stance in fighter.kit.stances.items():
            for move in stance.moves.values():
                if move.shout:
                    assert move_slot(fighter.id, fighter.kit, stance_name, move) in names
        assert generic_slot(fighter.id, "pose") in names
    for exchange in exchanges.values():
        a, b = sorted(exchange.fighters)
        for who, _ in exchange.intro:
            assert line_slot(who, "intro", b if who == a else a) in names
        for who in exchange.victory:
            assert line_slot(who, "victory", b if who == a else a) in names


# In a fight -------------------------------------------------------------------------------


def test_a_move_is_voiced_when_the_pack_has_its_voice(heard, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    try:
        defs = [get_fighter("avdol"), get_fighter("mannequin_red")]
        match = make_duel("avdol", "mannequin_red", p1=(100, 100), p2=(300, 100))
        view = FightView(load_stage("cairo_night"), defs)
        slot = move_slot("avdol", defs[0].kit, "base", defs[0].kit.move("base", "special"))
        heard.known = {slot, "whoosh"}
        for i in range(6):
            events = match.step((press("special") if i == 0 else NONE, NONE))
            view.on_events(events, match)
            view.update(match)
        assert heard.played.count(slot) == 1  # said once, as the move starts
    finally:
        pygame.display.quit()


# The tool -----------------------------------------------------------------------------------


def test_the_manifest_lists_every_effect_track_and_voice_with_what_it_is():
    slots = tool.wanted()
    names = {slot.name for slot in slots}
    assert {f"sfx/{name}" for name in tool.sfx_names()} <= names
    assert set(tool.SFX_NOTES) == set(tool.sfx_names())  # every effect is described
    assert {"music/menu", "music/cairo_night", "music/swiss_castle"} <= names
    by_name = {slot.name: slot for slot in slots}
    assert by_name["sfx/time_stop"].hint and by_name["voices/jotaro_p3/ko"].hint
    assert by_name["voices/jotaro_p3/intro.dio_p3"].hint == "You bastard!"  # the game's line
    text = tool.manifest_text(slots)
    assert "`voices/jotaro_p3/intro.dio_p3`" in text and "## Musique" in text


def test_check_counts_what_the_pack_holds_and_names_what_fits_nowhere(tmp_path):
    beep(tmp_path / "sfx" / "time_stop.wav")
    beep(tmp_path / "voices" / "jotaro_p3" / "ko.wav")
    beep(tmp_path / "voices" / "nobody" / "hello.wav")
    beep(tmp_path / "inbox" / "raw.wav")  # the inbox is not part of the pack
    have = tool.found(tmp_path)
    assert have == {"sfx/time_stop", "voices/jotaro_p3/ko", "voices/nobody/hello"}
    report = tool.check_text(tool.wanted(), have)
    assert "Bruitages : 1/" in report and "voices/nobody/hello" in report


def test_a_cut_is_trimmed_levelled_and_written_in_the_format_the_game_reads(tmp_path):
    cut = {"file": "raw.wav", "slot": "voices/jotaro_p3/ko", "start": 1.5, "end": 2.25}
    command = tool.cut_command(tmp_path / "raw.wav", tmp_path / "out.ogg", cut)
    assert command[0] == "ffmpeg" and command[-1].endswith("out.ogg")
    assert command[command.index("-ss") + 1] == "1.5"
    assert command[command.index("-to") + 1] == "2.25"
    assert command[command.index("-ac") + 1] == "1"  # a voice: mono
    assert "loudnorm" in command[command.index("-af") + 1]
    song = {"file": "song.mp3", "slot": "music/menu", "gain_db": -3}
    command = tool.cut_command(tmp_path / "song.mp3", tmp_path / "menu.ogg", song)
    assert "-ss" not in command and command[command.index("-ac") + 1] == "2"  # music: stereo
    assert "volume=-3dB" in command[command.index("-af") + 1]


def test_a_cut_to_a_slot_the_game_does_not_have_is_refused(tmp_path, monkeypatch):
    beep(tmp_path / "inbox" / "raw.wav")
    (tmp_path / "inbox" / "cuts.toml").write_text(
        '[[cut]]\nfile = "raw.wav"\nslot = "voices/jotaro_p3/no_such_move"\n', encoding="utf-8"
    )
    monkeypatch.setattr(tool.shutil, "which", lambda name: "ffmpeg")
    with pytest.raises(SystemExit, match="emplacement"):
        tool.cut_all(tmp_path)


def test_no_sound_file_is_part_of_the_game():
    """The pack is the player's: nothing recorded ships with the game or its repository."""
    recorded = (".ogg", ".wav", ".mp3", ".flac")
    files = [p for p in (ROOT / "jojo_arena").rglob("*") if p.suffix.lower() in recorded]
    assert files == []
