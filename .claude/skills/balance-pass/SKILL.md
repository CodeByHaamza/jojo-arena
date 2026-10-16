---
name: balance-pass
description: Use when a fight of JoJo Arena feels wrong - "X is too strong", "that move is unpunishable", "nobody uses Y", or for a balance pass over a part of the roster. Measures first with the balance bot and the frame meter, then changes numbers in the data files only.
---

# Balancing a fight

Never change a number before you have measured the thing you are about to change.

## 1. The raw numbers

    make balance FIGHTS=40

Bot against bot on every matchup, win rates. **What it measures is close-range raw
power.** The bot plays neither zoning nor remote control, so:

- a zoner (Kakyoin, Caesar, Straizo) losing to the bot means nothing;
- a brawler losing to everyone means something;
- a character above about 65% against the whole cast is worth a look.

## 2. The frames

The other half, and it does not lie.

- In training, pause -> dummy settings -> pick the suspect move as the dummy's action,
  delay **0**, in between **guard**.
- Block it, then try to punish it. The frame meter at the bottom right shows, frame by
  frame, when each side got free, and prints the advantage it measured.
- The frame data line gives the same thing as `startup/active/recovery  hit/block`.

What to look for:

| Reading | What it means |
| --- | --- |
| Heavy blow at 0 or better on block | nothing punishes it: usually too good |
| Big damage, startup under 8 frames | it beats everything on reaction |
| Advantage on hit over about +12 | a free follow-up, so a loop |
| A move never used by anyone | its risk is not paid for |

## 3. Change one thing

**Only TOML files**: `jojo_arena/combat/rules.toml` and
`jojo_arena/characters/*.toml`. A balance change in Python code is a bug.

Prefer, in this order: recovery frames (makes a move punishable without weakening what
it does), then startup, then damage. Damage last: it is what the player feels, and the
smallest change that fixes the problem is the right one.

Write the reason in the comment above the value. Then measure again, the same way.

## 4. What not to do

- Do not flatten the cast. Jotaro hitting harder than Kakyoin is the design.
- Do not balance a character against the bot alone: the bot is a measuring stick, not a
  player.
- Do not change five values at once; you will not know which one worked.

## 5. Finish

`make check`, then the decision line in `docs/GDD.md` when the change alters how a
character is meant to feel. Commit as `fix:` (a value that was wrong) or `feat:` (a
deliberate change of feel), one commit for the pass.
