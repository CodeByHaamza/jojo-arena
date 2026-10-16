---
name: new-fighter
description: Use when adding a playable character to JoJo Arena, or when asked "add <name> to the roster", "make <name> playable", "a kit for <name>". Walks the whole path from the manga to a character you can pick on the select screen, in the order that avoids rework.
---

# Adding a fighter

A character is **data**. Nine files, in this order; skipping one is how a character ends
up half in the game.

## 1. Decide who they are (before any file)

From `docs/GDD.md`: which part, which role (brawler / zoner / trickster / grappler),
which fighting style (`stance_toggle` for a Stand, `hamon`, `vampire`, `none`), and the
one sentence that says what it feels like to fight them.

If the GDD does not say, look it up (JoJo Wiki, the manga, All Star Battle R) and write
the answer into the GDD decisions **before** building. Do not invent silently.

Pick the id now, and keep it everywhere: `wamuu`, `joseph_p2`, `dio_p3` - part suffix
only when the same character exists in several parts.

## 2. The kit - `jojo_arena/characters/<id>.toml`

`docs/KITS.md` lists every field. Copy the closest existing kit and change what the
character *is*. What a kit needs:

- `name`, `max_hp`, `walk_speed`, `style`, and `strength` for a Stand;
- one stance (`[stances.base]`), plus a second one (`[stances.stand]`,
  `[stances.freeze]`...) for a style that toggles;
- per stance: `light`, `heavy`, `special`, and the `_alt` variants reached by holding a
  direction; chains with `chain = "light2"`;
- `[moves.hha]` (1 bar) and `[moves.gha]` (2 bars, usually a cutscene);
- on every move: `label`, `label_en`, `info`, `info_en`, and `shout` when they shout.

Frames are at 60 Hz, speeds and knockback in pixels per second. Jab 4 frames of startup,
heavy 12-16, super 18. Damage around 30 for a jab, 70 for a heavy, 160 for an HHA.

## 3. The look - `jojo_arena/characters/looks/<id>.toml`

Build first (height, shoulders, limbs: the silhouette), then the palette, then the
costume parts (the README lists them all). Then:

    make sprites

and look at `build/sprite_previews/<id>.png` and `<id>_sheet.png`. If the silhouette is
not instantly recognisable, fix the build before anything else.

## 4. The roster - `jojo_arena/characters/roster.toml`

Name, kit, sprites, colour, aura, Stand and its sprite sheet, role and blurb, both
languages. Without this entry the character does not appear on the select screen.

## 5. The glossary - `jojo_arena/characters/lore/part<n>.toml`

`[[characters]]` and, for a Stand user, `[[stands]]`: description, family, origin of the
name, the six stats (A to E). A test fails if a playable character has no entry.

## 6. The test - `tests/test_<id>.py`

Not "it loads": the moves that matter, played out. `tests/helpers.py` gives you
`make_duel`, `press`, `hold`, `run`, `run_until`. One test per thing that makes the
character special (the grab drains, the counter answers, the trap fires).

## 7. Try it by hand

    make training P1=<id> P2=jotaro_p3

Every move, once. Then set the dummy to repeat your new heavy blow with a delay of 0 and
read the frame meter: a heavy blow that is safe on block needs a reason.

## 8. `make check`, then the docs

`docs/ROADMAP.md` (tick the line), `docs/GDD.md` (the decisions about this character),
and the README roster line if there is one.

## 9. Commit

One commit, `feat: <name>, <what makes them special in one line>`. Never push unless you
are asked to.
