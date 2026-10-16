"""Fight replays: the fight is deterministic, so the players' inputs are enough to play
it again exactly, frame for frame (to reproduce a bug, or to watch a fight again).

A replay holds a little description of the fight (`meta`: fighters, stage, mode...), the
two players' inputs for every step, and the commands given from the pause menu at given
steps (training options), so those are replayed too.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from jojo_arena.engine.actions import NEUTRAL, InputFrame

FORMAT = 1


def frame_to_data(frame: InputFrame) -> object:
    """A compact form: 0 for no input at all, else a short list."""
    if frame == NEUTRAL:
        return 0
    data: list = [
        round(frame.move[0], 4),
        round(frame.move[1], 4),
        sorted(frame.held),
        dict(sorted(frame.press_counts.items())),
    ]
    if frame.cursor is not None or frame.stick is not None:
        data.append(list(frame.cursor) if frame.cursor is not None else None)
        data.append(list(frame.stick) if frame.stick is not None else None)
    return data


def frame_from_data(data: object) -> InputFrame:
    if data == 0:
        return NEUTRAL
    move = (float(data[0]), float(data[1]))
    held = frozenset(data[2])
    counts = {str(k): int(v) for k, v in data[3].items()}
    cursor = tuple(data[4]) if len(data) > 4 and data[4] is not None else None
    stick = tuple(data[5]) if len(data) > 5 and data[5] is not None else None
    return InputFrame(move, held, counts, cursor, stick)


@dataclass
class Replay:
    meta: dict
    frames: list[tuple[InputFrame, InputFrame]] = field(default_factory=list)
    commands: dict[int, list[dict]] = field(default_factory=dict)

    def record(self, frames: tuple[InputFrame, InputFrame]) -> None:
        self.frames.append(frames)

    def command(self, command: dict) -> None:
        """A pause-menu command, applied before the next step when replaying."""
        self.commands.setdefault(len(self.frames), []).append(command)

    def to_data(self) -> dict:
        return {
            "format": FORMAT,
            "meta": self.meta,
            "commands": {str(step): cmds for step, cmds in self.commands.items()},
            "frames": [[frame_to_data(a), frame_to_data(b)] for a, b in self.frames],
        }

    @classmethod
    def from_data(cls, data: dict) -> Replay:
        if data.get("format") != FORMAT:
            raise ValueError(f"unsupported replay format {data.get('format')}")
        frames = [(frame_from_data(a), frame_from_data(b)) for a, b in data["frames"]]
        commands = {int(step): list(cmds) for step, cmds in data.get("commands", {}).items()}
        return cls(dict(data["meta"]), frames, commands)


def save_replay(path: Path, replay: Replay) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(replay.to_data(), separators=(",", ":")), encoding="utf-8")
    tmp.replace(path)


def load_replay(path: Path) -> Replay:
    return Replay.from_data(json.loads(path.read_text(encoding="utf-8")))
