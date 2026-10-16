---
name: cut-release
description: Use when publishing a version of JoJo Arena - "ship a release", "tag v0.2.0", "build the exe for players". Covers the checks, the version bump, the tag, and what GitHub Actions does on its own.
---

# Cutting a release

A release is one `.exe` a player downloads and double-clicks. Nothing to install.

## 1. The state of the branch

- On `main`, nothing uncommitted.
- `make check` passes.
- `make screens` and **look at the pictures**: the tests open every screen, they do not
  notice text over text or a panel covering the fight.
- `make demo` for a couple of minutes: no crash, the fight ends.
- `docs/ROADMAP.md` matches what the version really does.

## 2. The version, in two places that must agree

- `pyproject.toml` - `version = "0.2.0"`
- `jojo_arena/__init__.py` - `__version__ = "0.2.0"`

The release workflow fails on purpose if they do not match the tag. The version goes in
the replay files, so it also says which build a bug came from.

Which number: a new playable character or mode is a minor (`0.2.0`); fixes alone are a
patch (`0.1.1`).

## 3. The .exe, locally, before the tag

    make exe
    dist\JoJoArena.exe

Launch the real thing once: the title screen, a fight, the options. The `.exe` embeds the
data, so a file missing from the package only shows up here. Check it also runs from a
folder whose path has a space and an accent in it.

## 4. Tag and push

    git commit -am "chore: version 0.2.0"
    git tag v0.2.0
    git push origin main
    git push origin v0.2.0

`.github/workflows/release.yml` then checks the version against the tag, runs lint and
the tests, builds the `.exe`, smoke-tests it (`--demo --frames 600`) and publishes the
Release with the `.exe` attached. Watch the run; if it fails, delete the tag
(`git push --delete origin v0.2.0`), fix, tag again.

## 5. After

Read the release notes as a player would: what is new, what to download, what to press.
Keep the line saying it is a free, non-commercial, unofficial fan game.

Never push a tag without being asked. The version bump is the owner's call.
