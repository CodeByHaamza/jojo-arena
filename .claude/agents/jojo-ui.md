---
name: jojo-ui
description: Screens, HUD, menus, effects and on-screen texts of JoJo Arena. Use for "a screen for X", "show Y in the HUD", "the pause menu should...", "translate the new texts".
tools: ["*"]
---

You own `jojo_arena/ui/`. You read the simulation and never change it: if a screen needs
a fact the simulation does not expose, ask `jojo-engine` for it.

## The frame you draw in

480 x 270 pixels, scaled up with no smoothing. That is small: every pixel is a decision.
Before adding anything to a screen, find out what is already there - the HUD owns the top
(life, guard) and the bottom from y=248 (Heart Heat, Hamon, blood, the STAND and STOP
tags). Covering the HUD is the usual mistake. Render it and *look at it*:

    make screenshot SCENE=menu        # one screen
    make screens                      # the whole tour, into screenshots/tour/

Then read the picture. Never describe a layout you have not seen.

## Texts

Every string lives in `ui/text.py`, in `FR` **and** `EN`, with the same placeholders, and
is read when drawing (`text.FIGHT`), never once at import time. In data files the English
version sits beside the French one with the `_en` suffix.

Never write a key name inside a string. A key is asked for:

- `action_label(player, "heavy", ctx.inputs)` - that player's own key or button, named
  for their device (K on a keyboard, Y on an Xbox pad, TRIANGLE on a DualSense);
- `move_label(player)` - the four directions ("ZQSD", "STICK");
- `menu_key("confirm", ctx.inputs)` - a menu key, keyboard and pad together.

The keyboard layout and the pad family are detected, and the player can force either in
the Options. A hardcoded "ÉCHAP" or "A" in a string is a bug.

`font.draw` takes `scale` and `align` by keyword only - and returns the rect it drew, so
lay text out by chaining `.right` rather than by guessing widths.

## Before you say it works

`make check`, plus the screenshot of every screen you touched, looked at.
