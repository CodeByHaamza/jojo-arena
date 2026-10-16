---
name: jojo-art
description: The look of the characters and the icons of JoJo Arena - look files, generated sprite sheets, key-pose animations, part emblems and glossary icons. Use for "draw Wamuu", "the silhouette is wrong", "a new animation for that move".
tools: ["*"]
---

The sprites are **generated from a data file**, never drawn by hand:
`jojo_arena/characters/looks/<id>.toml` describes a body (`[build]`), a palette, a face
and a list of costume parts. The README lists every part and its options; the generator
is `tools/spritegen/`.

    make sprites                        # everything
    python tools/make_sprites.py <id>   # one character

Then **look at the result**: `build/sprite_previews/<id>.png` (the three views) and
`<id>_sheet.png` (every animation). Say what you see, not what you intended.

The style, which is not up for debate: around 48 px tall in 64 x 64 cells, black outline
(#17121f), two or three shading tones, a small highlight, saturated characters over a
dull floor, an elliptical shadow under each one.

What makes a character readable here is the **silhouette**: Jotaro is tall and square,
Kakyoin is slim. Get the build right before the colours.

A move can have its own animation, written pose by pose in the look file
(`[anims.<name>]`, see CONTRIBUTING): key poses, in-betweens computed.

A sheet drawn by hand may replace a generated one with no code change, as long as the
file names and the cell format stay. A missing sheet falls back to a coloured shape.

A test checks that every sheet is in step with its look file: regenerate before
committing.
