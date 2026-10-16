---
name: repro-replay
description: Use when something went wrong in a fight in JoJo Arena and has to be reproduced - a crash, a move that did not come out, damage that looks wrong, a bug report with a replay file attached. Turns a replay into a failing test.
---

# From a replay to a failing test

The fight is deterministic: the same inputs give the same fight, frame for frame. So a
replay is a complete, exact bug report.

## 1. Get the replay

The player presses **F9** during the fight, or it is saved when they leave. The files
live in `%APPDATA%\JoJoArena\replays\` (`~/.local/share/JoJoArena/replays/` elsewhere).

    .venv\Scripts\python.exe -m jojo_arena --replay <file>

Watch it. Note the step at which it goes wrong - the replay is a list of input frames,
one per logic step, so a step number is a precise address.

## 2. Read it

A replay is JSON: `meta` (fighters, stage, mode), `frames` (the two players' inputs per
step), `commands` (what was changed in the pause menu, and when). Load it in Python:

```python
from jojo_arena.combat.replay import load_replay
replay = load_replay(path)
print(replay.meta, len(replay.frames))
```

## 3. Replay it with no screen

This is the step that turns a report into a test: `combat/` never imports pygame, so the
whole fight runs headless.

```python
from jojo_arena.characters import get_fighter
from jojo_arena.combat.match import Match
from jojo_arena.combat.rules import load_rules
from jojo_arena.stages import load_stage

kits = tuple(get_fighter(i).kit for i in replay.meta["fighters"])
match = Match(kits, load_rules(), load_stage(replay.meta["stage"]).build_arena())
for step, frames in enumerate(replay.frames):
    events = match.step(tuple(frames))
    # print what you are chasing, at the step you noted
```

Print the state around the bad step: `fighter.state`, `fighter.attack`, `fighter.hp`, the
events. The fight tells you what it did.

## 4. Shrink it

Cut the replay down to the few steps that still show the bug, then rewrite those inputs
by hand with `tests/helpers.py` (`press`, `hold`, `run`, `run_until`). The test you want
is five lines, not a replay file committed into the repo.

Put it in the right `tests/test_*.py`, make sure it **fails** on the current code, and
only then fix the bug.

## 5. If the replay does not reproduce

Then the simulation is no longer deterministic, which is a worse bug than the one you
were chasing. Look for: a bare `random`, something read from the clock, a `set` or `dict`
iterated in a way that depends on insertion from drawing code, or `ui/` writing into the
simulation. Report it first.
