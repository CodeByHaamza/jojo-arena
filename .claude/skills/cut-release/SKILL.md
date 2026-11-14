---
name: cut-release
description: Use when publishing a version of JoJo Arena - "ship a release", "publish v0.2.0", "build the exe for players". Covers the checks, `make release-pr`, the pull request into main, and what GitHub Actions does on its own once it is merged.
---

# Cutting a release

A release is one `.exe` a player downloads and double-clicks. Nothing to install.

Pull requests go to `develop`; **a merge into `main` is a release**. There is no tag to
push by hand: the release workflow creates it.

## 1. The state of develop

- On `develop`, nothing uncommitted, the same as `origin/develop`.
- `make check` passes.
- `make screens` and **look at the pictures**: the tests open every screen, they do not
  notice text over text or a panel covering the fight.
- `make demo` for a couple of minutes: no crash, the fight ends.
- `docs/ROADMAP.md` matches what the version really does.
- The `## Non publié` section of `CHANGELOG.md` says, for a player, what is new.

Which number: a new playable character or mode is a minor (`0.2.0`); fixes alone are a
patch (`0.1.1`). The version bump is the owner's call.

## 2. The .exe, locally, before the pull request

    make exe
    dist\JoJoArena.exe

Launch the real thing once: the title screen, a fight, the options. The `.exe` embeds the
data, so a file missing from the package only shows up here. Check it also runs from a
folder whose path has a space and an accent in it.

## 3. One command

    make release-pr VERSION=0.2.0

`tools/release_pr.py` writes the version in `pyproject.toml` and
`jojo_arena/__init__.py`, turns `## Non publié` into `## 0.2.0 - <date>` (an empty
`## Non publié` stays on top), commits `chore: release 0.2.0`, pushes `develop` and opens
the pull request `develop` -> `main` with the notes as its description.

On that pull request the CI also runs `tools/release_pr.py --check`: the version must be
above the last `v*` tag, and the changelog must have its section.

## 4. Merge

Merging into `main` runs `.github/workflows/release.yml`: the tests on Linux (the home
server's runner) and on Windows, the `.exe` built and smoke-tested
(`--demo --frames 600`), then the tag `v0.2.0` and the Release with the `.exe` attached
and the changelog section as notes. A version already tagged publishes nothing and says
so. If the run fails, nothing is published: fix on `develop`, open the pull request again.

## 5. After

Read the release notes as a player would: what is new, what to download, what to press.
Keep the line saying it is a free, non-commercial, unofficial fan game.

Never open the release pull request, and never merge it, without being asked.
