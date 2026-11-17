# Costumes and Colours Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A fighter can have several sourced costumes, each with several sourced colours, picked on the select screen; two players on the same fighter never look the same.

**Architecture:** A costume is a look file that inherits another (`base = "<id>"`) and gets its own sprite sheet. A colour is a named palette written into the sheet's TOML and applied when the sheet is loaded (the loader already recolours the dummies). The choice travels in `Loadout`, which the simulation never sees.

**Tech Stack:** Python 3.12, pygame-ce, pytest; generator in `tools/spritegen/`.

**Spec:** `docs/superpowers/specs/2026-11-15-costumes-couleurs-design.md`

## Global Constraints

- Code, names, comments in English; game texts French and English (`label`, `label_en`).
- Every costume and every colour cites its `source`. Sourced first (the ASBR and EoH tints, whose origin JoJo Wiki gives); an invented colour only when there is none, and its `source` says so.
- No reference image in the repository: only the tones read off it and the name of the source. Images go to the scratchpad.
- The pixels of an existing sheet do not change. If two tones of a look collide and one has to move by one unit, the commit says so.
- One colour system: the dummies' `palette` in `roster.toml` keeps working through the same loader.
- The simulation (`combat/`), the balance and the replays do not change. `engine/` names no JoJo.
- The game reads sheets, never look files: a hand-drawn sheet can still replace a generated one.
- Commits conventional, no AI mention, no `Co-Authored-By`. Nothing is pushed.

## Review Focus

- `settings.json` names a costume or a colour that no longer exists: the fighter comes up in its normal costume and first colour, no crash → Task 3, `test_an_outfit_that_is_gone_falls_back`.
- A colour paints one material with the very tone another material starts from (white shirt → the grey the trousers had): each material ends in its own colour → Task 1, `test_a_tone_already_repainted_is_not_repainted_again`.
- A sheet with no `[colors]` at all (hand-drawn, or one of the sixteen fighters not done yet) asked for a colour: it loads as it is → Task 1, `test_a_sheet_without_colors_ignores_the_colour_asked`.
- Mirror match on a fighter whose costume has a single colour: both sides stay as they are, nothing loops → Task 3, `test_a_mirror_match_with_one_colour_stays_as_it_is`.
- A player browsing every colour of every costume on the select screen: the cache of repainted sheets stays bounded (6 to 12 MB each, the CI runner has 3 GB) → Task 1, `test_only_a_few_repainted_sheets_are_kept`.

---

### Task 1: The loader repaints in one pass and knows a sheet's colours

**Files:**
- Modify: `jojo_arena/engine/sprites.py` (`recolor`, `SheetSprites`, `_LOADED`)
- Test: `tests/test_sprites.py`

**Interfaces:**
- Produces:
  - `ColorInfo(id: str, label: str, label_en: str, source: str, stand: str, palette: dict[str, list[Color]])` (frozen dataclass); `palette` is empty for the sheet's own colour.
  - `SheetSprites.colors: dict[str, ColorInfo]` in the order of the sheet's `[colors.*]` (empty: the sheet has none); `SheetSprites.costume: tuple[str, str, str]` = `(label, label_en, source)` from `[costume]` (empty strings when absent).
  - `SheetSprites.load(png_path, spec_path, palette=None, color: str = "") -> SheetSprites | None`: `color` names one of the sheet's colours; unknown, empty or the first one: the sheet as it is.
  - `recolor(sheet, keys, palette) -> Surface`: same signature; each key tone goes to its target from the *original* image.
  - `REPAINTED_KEPT = 8`: repainted sheets kept in the cache (least recently asked dropped); sheets loaded as they are stay for good, as today.

- [ ] **Step 1: Write the failing tests** in `tests/test_sprites.py`

```python
def test_a_tone_already_repainted_is_not_repainted_again():
    # shirt: red -> green; trousers: green -> blue. One pass: red ends green, green ends blue.
    sheet = pygame.Surface((2, 1), pygame.SRCALPHA)
    sheet.set_at((0, 0), (200, 0, 0, 255))
    sheet.set_at((1, 0), (0, 200, 0, 255))
    keys = {"shirt": [[200, 0, 0]], "trousers": [[0, 200, 0]]}
    result = recolor(sheet, keys, {"shirt": [(0, 200, 0)], "trousers": [(0, 0, 200)]})
    assert result.get_at((0, 0))[:3] == (0, 200, 0)
    assert result.get_at((1, 0))[:3] == (0, 0, 200)

def test_transparent_pixels_stay_transparent_whatever_the_key():  # key (0,0,0), alpha 0 untouched
def test_a_sheet_knows_its_colours_and_its_costume(tmp_path):     # order kept, first has no palette
def test_a_sheet_is_loaded_in_the_colour_asked(tmp_path):         # load(..., color="b") repaints
def test_a_sheet_without_colors_ignores_the_colour_asked(tmp_path)
def test_an_unknown_colour_is_the_sheet_as_it_is(tmp_path)
def test_only_a_few_repainted_sheets_are_kept(tmp_path):          # REPAINTED_KEPT + 3 colours asked
```

A helper `colored_sheet(tmp_path, colors: int)` writes a 64 × 192 PNG of one flat tone and a TOML with `[recolor] body = [[tone]]` and `colors` tables `c0` (no palette), `c1`… (`[colors.cN.palette] body = [[r, g, b]]`).

- [ ] **Step 2: Run** `pytest tests/test_sprites.py -q` — the new tests fail (`ColorInfo` missing, chain repaint).
- [ ] **Step 3: Implement.** `recolor`: two rounds of `PixelArray.replace` — every key tone to a placeholder no sprite pixel can have (alpha 254), then every placeholder to its target (alpha 255) — so no target is ever read as a key. `load`: resolve `color` against `spec_data["colors"]`, merge its palette over `palette`, add the colour to the cache key; repainted entries live in an `OrderedDict` capped at `REPAINTED_KEPT`.
- [ ] **Step 4: Run** `pytest tests/test_sprites.py tests/test_fight_view.py -q` — pass (the dummies still come out red and blue).
- [ ] **Step 5: Commit** `feat: a sheet is repainted in one pass and knows its colours`

### Task 2: The generator writes costumes and colours into the sheets

**Files:**
- Modify: `tools/spritegen/look.py` (`Look`, `load_look`), `tools/spritegen/sheet.py` (`build_sheet`)
- Test: `tests/test_spritegen.py`

**Interfaces:**
- Consumes: the sheet format of Task 1 (`[costume]`, `[recolor]`, `[colors.<id>]`, `[colors.<id>.palette]`).
- Produces, in a look file:
  - `base = "<look id>"`: the file starts from `looks/<look id>.toml` (same folder). `[palette]`, `[body]`, `[build]`, `[face]`: its entries replace the base's, the others stay. `[[parts]]`: its list replaces the base's when it gives one. `name`, `pose`: its own, else the base's. `[anims.*]` and `[poses.*]`: the base's, always; a costume that gives any is refused. `[colors.*]`, `[costume]`: its own only.
  - `[costume]`: `label`, `label_en`, `source` (all three, or refused).
  - `[colors.<id>]`: `label`, `label_en`, `source` (all three, or refused), `stand` (optional), `[colors.<id>.palette]` with slots written as in `[palette]` (one hex: its four tones are computed). The first colour has no `palette`; a later one without `palette` is refused; a slot the look does not have is refused.
  - `Look.base: str`, `Look.costume: CostumeDef | None`, `Look.colors: dict[str, ColorDef]`; `ColorDef(label, label_en, source, stand, palette: dict[str, list[Color]])`.
  - `recolor_slots(look) -> list[str]`: `look.recolor` plus every slot a colour changes, in palette order.
  - `check_recolor_keys(look) -> None`: raises `ValueError("<id>: '<slot>' and '<other>' share the tone #rrggbb: a colour could not tell them apart")` when a tone of a slot to repaint equals a tone of another palette slot, or the outline.

- [ ] **Step 1: Write the failing tests** in `tests/test_spritegen.py`: `test_a_costume_starts_from_its_base_and_says_only_what_changes`, `test_a_costume_cannot_bring_its_own_animations`, `test_colours_go_into_the_sheet_with_their_tones`, `test_the_first_colour_is_the_look_itself`, `test_two_materials_sharing_a_tone_are_refused_by_name`, `test_a_colour_naming_an_unknown_material_is_refused`, `test_a_look_without_colours_writes_the_sheet_it_always_wrote` (byte-identical TOML for `looks/kakyoin.toml`).
- [ ] **Step 2: Run** `pytest tests/test_spritegen.py -q` — the new tests fail.
- [ ] **Step 3: Implement** in `look.py` and `sheet.py`. `build_sheet` calls `check_recolor_keys` only when the look has colours.
- [ ] **Step 4: Run** `pytest tests/test_spritegen.py -q` — pass, `test_generated_sheets_are_up_to_date` included (no existing sheet moves).
- [ ] **Step 5: Commit** `feat: a look can be a costume of another, and carry its colours`

### Task 3: The outfit travels from the roster to every screen

**Files:**
- Modify: `jojo_arena/characters/__init__.py`, `jojo_arena/ui/loadout.py`, `jojo_arena/ui/fight_view.py` (`FighterView.__init__`), `jojo_arena/ui/portraits.py` (`FighterLook`), `jojo_arena/ui/fight_scene.py`, `jojo_arena/ui/setup_scene.py`, `jojo_arena/settings.py`
- Test: `tests/test_outfits.py` (new), `tests/test_poses.py` (constructor calls)

**Interfaces:**
- Consumes: `SheetSprites.load(..., color=)`, `SheetSprites.colors`, `ColorInfo.stand`.
- Produces:
  - `FighterDef.costumes: dict[str, str]` — costume id → sheet path, from `costumes = { id = "dir/name" }` in `roster.toml`, in file order.
  - `Loadout(pose="", stand_pose="", costume="", color="")`; `""` is the normal costume and the first colour.
  - `outfit_sheet(fighter_def, loadout) -> str`: the sheet path of the costume asked (the normal one when unknown).
  - `resolve_loadout(sprites, loadout)`: unchanged signature; also keeps `color` only if `sprites.colors` has it (else `""`), and passes `costume` through.
  - `distinct(first: Loadout, second: Loadout, colors: list[str]) -> Loadout`: `second`, moved to the colour after `first`'s in `colors` when both have the same costume and colour; unchanged when `colors` has fewer than two.
  - `random_loadout(sprites, rng, costumes=(), colors=())`: also picks a costume and a colour.
  - `FighterView(fighter_def, loadout)` and `FighterLook(fighter_def, loadout=None)` load the costume's sheet in the colour asked, and the Stand's sheet in the colour `ColorInfo.stand` names.
  - `Settings.outfits: dict[str, list[str]]` — fighter id → `[costume, colour]`, saved and parsed like `poses`.
  - `FightScene`: the second side's loadout goes through `distinct` when both sides field the same fighter. Versus the computer, the computer picks with `random_loadout` first; the training dummy and the Arcade opponents keep the normal costume and take the first colour left free. `SetupScene` and the entrance draw both fighters from `ctx.loadouts`.

- [ ] **Step 1: Write the failing tests** in `tests/test_outfits.py`, on sheets built in `tmp_path` and on `mannequin_red` where a roster fighter is needed: `test_a_costume_is_its_own_sheet`, `test_a_colour_repaints_the_fighter_and_names_its_stands_colour`, `test_an_outfit_that_is_gone_falls_back`, `test_a_mirror_match_never_shows_twice_the_same`, `test_a_mirror_match_with_one_colour_stays_as_it_is`, `test_different_costumes_keep_the_colour_each_picked`, `test_the_computer_picks_an_outfit_too`, `test_the_settings_keep_the_outfits`, `test_a_replay_plays_the_same_fight_whatever_is_worn` (two `Match`es stepped with the same inputs: equal positions and life; the loadout never reaches them).
- [ ] **Step 2: Run** `pytest tests/test_outfits.py -q` — fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pytest tests/test_outfits.py tests/test_poses.py tests/test_lines.py tests/test_ui.py -q` — pass.
- [ ] **Step 5: Commit** `feat: a fighter wears the costume and the colour picked, on every screen`

### Task 4: The select screen picks costume, colour and poses in one list

**Files:**
- Modify: `jojo_arena/ui/select_scene.py`, `jojo_arena/ui/text.py`
- Test: `tests/test_outfits.py`, `tests/test_poses.py` (the pose step's layout)

**Interfaces:**
- Consumes: Task 3.
- Produces:
  - `CharacterSelectScene.outfit_rows() -> list[str]`: of `"costume"`, `"color"`, `"pose"`, `"stand_pose"`, in that order. Costume and colour only with two choices or more; the pose rows as today.
  - `CharacterSelectScene.choices(row: str) -> list[str]`: the ids one row cycles through.
  - Up/Down changes row, Left/Right the value, Enter confirms, Escape goes back to the grid (as today). Changing the costume keeps the poses and takes that costume's first colour. For player 2 on player 1's fighter and costume, player 1's colour is skipped.
  - While the step is open, the panel shows the name, the Stand's name, then one line per row (`LABEL  < value >`, the active one in gold with its arrows), then the source of the active line; the role, the life and the blurb give way.
  - The preview shows the costume and the colour live: idle with the Stand on the costume and colour rows, the pose on the pose rows.
  - Texts: `COSTUME_ROW` ("COSTUME" / "COSTUME"), `COLOR_ROW` ("COULEUR" / "COLOR"), `COSTUME_NORMAL` ("NORMAL" / "NORMAL"), `POSE_STAND_ROW` shortened to "STAND" in the list.
  - `ctx.settings.outfits[fighter_id]` is written on confirm, read on open.

- [ ] **Step 1: Write the failing tests**: `test_the_rows_are_only_those_with_a_choice`, `test_left_right_change_the_costume_and_the_colour_restarts`, `test_player_two_cannot_take_player_ones_colour`, `test_the_preview_wears_what_is_picked`, `test_the_last_outfit_is_offered_first`, `test_every_costume_colour_and_pose_name_fits_its_line` (over every roster sheet, both languages: `font.text_width(label) <= SIDE_W - 62`).
- [ ] **Step 2: Run** — fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pytest tests/test_outfits.py tests/test_poses.py tests/test_ui.py -q` — pass; `python tools/screenshot_tour.py` runs through.
- [ ] **Step 5: Commit** `feat: costume, colour and poses are picked in one list on the select screen`

### Task 5: Jonathan — his four colours, shirtless, The Inherited Soul

**Files:**
- Modify: `jojo_arena/characters/looks/jonathan.toml`, `jojo_arena/characters/roster.toml`
- Create: `jojo_arena/characters/looks/jonathan_shirtless.toml`, `jojo_arena/characters/looks/jonathan_inherited_soul.toml`, their sheets under `jojo_arena/assets/sprites/`
- Test: `tests/test_outfits.py`

**Content** (JoJo Wiki, ASBR and EoH pages of Jonathan, "Costumes & Tints"; tones read off the tint renders, kept in the scratchpad):

| Costume | Source | Colours (id: source) |
| --- | --- | --- |
| Normal | his *Phantom Blood* attire | `anime`: ASBR tint A, the anime's colours · `tome4`: tint B, cover of volume 4 · `tome3`: tint C, cover of volume 3 · `j534`: tint D, Adventure Battle Card J-534 |
| `shirtless` | EoH Special Costume F: chapter 35, episode 7 | `anime`: episode 7 · `inverse`: EoH's inverted version |
| `inherited_soul` | ASBR Extra Costume A: *JOESTAR The Inherited Soul* merchandise | `blanc`: tint A · `noir`: tint B |

- [ ] **Step 1: Write the failing test** `test_every_roster_costume_has_its_sheet_two_colours_and_its_sources` (every `FighterDef.costumes` entry loads; its sheet and the base sheet of a fighter that has costumes carry `[costume]` and at least two colours, each with `label`, `label_en`, `source`).
- [ ] **Step 2: Write the looks**, run `make sprites`, look at `build/sprite_previews/` and at a contact sheet of every colour next to its render.
- [ ] **Step 3: Run** `pytest tests/test_outfits.py tests/test_spritegen.py -q` — pass.
- [ ] **Step 4: Commit** `feat: Jonathan's colours, shirtless and in The Inherited Soul whites`

### Task 6: Jotaro, DIO, Avdol and their Stands

**Files:** as Task 5, for `jotaro_p3` (`coatless`, `inherited_soul`), `dio_p3` (`shadow`), `avdol` (`father`), and the colours of `star_platinum`, `the_world`, `magicians_red`.

**Content:** the table of the spec ("Le contenu du premier lot"). One fighter at a time: fetch the tint renders, write the colours, regenerate, compare, commit (`feat: <name>'s costumes and colours`). An image that cannot be found is reported, not replaced by a guess.

### Task 7: The docs, and the step in the fighter checklist

**Files:** `docs/GDD.md`, `docs/ROADMAP.md` (tick step 3), `docs/ARCHITECTURE.md`, `docs/KITS.md` or `README.md` (the look format: `base`, `[costume]`, `[colors.*]`), `CHANGELOG.md`, `.claude/skills/new-fighter/SKILL.md`, `CLAUDE.md` ("Imaginer un perso": costumes and colours with their sources).

- [ ] **Step 1: Write them.** **Step 2: Run** `make check`. **Step 3: Commit** `docs: costumes and colours, and their step when a fighter is made`
