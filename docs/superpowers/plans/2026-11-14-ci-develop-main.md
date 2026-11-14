# CI `develop` / `main` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PRs go to `develop` and are tested once per push on the home server; a merge on `main` publishes the Release by itself.

**Architecture:** Two repos. `jojo-arena` gets a release tool (`tools/release_pr.py`), rewritten workflows and docs. `maison` gets an ephemeral GitHub runner container (`jojo-runner/`) with a server-side guard (job-started hook) that refuses any job that is not from the repository itself. GitHub settings (default branch, ruleset on `main`, fork approval) are set with `gh api`.

**Tech Stack:** GitHub Actions, Python 3.12 (pytest), Docker Compose, Node (vitest) in `maison`, bash.

**Spec:** `docs/superpowers/specs/2026-11-14-ci-develop-main-design.md`

## Global Constraints

- jojo-arena commits: conventional (`feat:`, `fix:`, `ci:`, `docs:`, `chore:`…), English, **no `Co-Authored-By`, no mention of an AI tool** (CLAUDE.md + commit-msg hook).
- maison: French file/function names and comments, zero runtime dependency, pure functions separated from effects, `vitest` tests, inventory updated for every container and secret file (`inventaire/`), **a secret value is never read, printed or committed**.
- Repository: `CodeByHaamza/jojo-arena`. Runner label: `maison`. Base image: `ghcr.io/actions/actions-runner:2.338.2`.
- Runner limits: `cpus: "3"`, `mem_limit: 2g`, `PYTEST_XDIST_AUTO_NUM_WORKERS=3`, no Docker socket, user `runner` (uid 1001) **without sudo**.
- Secret file on the server: `/home/hamza/.secrets/jojo-runner.env`, mode 600, one key `JOJO_RUNNER_PAT` (fine-grained PAT, "Administration: read and write" on jojo-arena only). Written by the owner.
- Version heading in the CHANGELOG: `## X.Y.Z - YYYY-MM-DD`, under an always-present `## Non publié`.

## Review Focus

- The home server is off: PR checks stay "queued"; the ruleset lets the admin bypass. Documented in INFRA.md (Task 2), no code.
- A push on `main` whose version already has a tag (admin push without bump): `release.yml` publishes nothing and says so, never fails on "tag exists" → Task 2 step "release skips an existing tag".
- `## Non publié` empty or missing: `release_pr.py` refuses before touching a file → Task 1 test `test_close_unreleased_refuses_an_empty_section`.
- A version not above the last tag (same, lower, or malformed like `0.2`): refused → Task 1 tests `test_check_refuses_a_version_not_above_the_tag`, `test_parse_version_refuses_two_parts`.
- An event whose `pull_request.head.repo` is `null` (deleted fork) or a `pull_request_target`: refused by the guard → Task 3 tests.

---

### Task 1: Release tooling (jojo-arena)

**Files:**
- Create: `tools/release_pr.py`
- Modify: `tools/release_notes.py` (section lookup)
- Modify: `Makefile` (target `release-pr`, add to `help`)
- Test: `tests/test_release_pr.py`, `tests/test_release_notes.py`

**Interfaces:**
- Produces (used by Task 2's workflows):
  - `python tools/release_pr.py X.Y.Z` — bump, changelog, commit, push `develop`, open PR `develop` → `main`.
  - `python tools/release_pr.py --check` — exit 0 if the current version is above the last `v*` tag and the CHANGELOG has its `## X.Y.Z - …` section; else prints why, exit 1.
  - `python tools/release_pr.py --version` — prints the current version (from `jojo_arena/__init__.py`).
- Pure functions in `tools/release_pr.py`:
  - `parse_version(text: str) -> tuple[int, int, int]` (raises `ValueError` unless exactly three integers)
  - `set_version_pyproject(text: str, version: str) -> str` (the `version = "…"` line of `[project]` only)
  - `set_version_init(text: str, version: str) -> str` (`__version__ = "…"`)
  - `close_unreleased(changelog: str, version: str, date: str) -> str` (raises `ValueError` if `## Non publié` is missing or empty)
  - `check_release(version: str, last_tag: str | None, changelog: str) -> list[str]` (problems, empty = ok)

- [ ] **Step 1: Write the failing tests** in `tests/test_release_pr.py`:

```python
def test_parse_version_reads_three_numbers():
    assert parse_version("0.12.3") == (0, 12, 3)
    assert parse_version("v1.0.0") == (1, 0, 0)

def test_parse_version_refuses_two_parts():
    with pytest.raises(ValueError):
        parse_version("0.2")

def test_set_version_touches_only_the_project_version():
    text = '[project]\nversion = "0.1.0"\n[tool.ruff]\ntarget-version = "py312"\n'
    out = set_version_pyproject(text, "0.2.0")
    assert 'version = "0.2.0"' in out and 'target-version = "py312"' in out

def test_close_unreleased_keeps_an_empty_section_on_top():
    log = "# Journal\n\n## Non publié\n\n### Ajouté\n\n- Avdol.\n"
    out = close_unreleased(log, "0.2.0", "2026-11-14")
    assert out.index("## Non publié") < out.index("## 0.2.0 - 2026-11-14") < out.index("- Avdol.")

def test_close_unreleased_refuses_an_empty_section():
    with pytest.raises(ValueError):
        close_unreleased("# Journal\n\n## Non publié\n\n## 0.1.0 - 2026-01-01\n", "0.2.0", "2026-11-14")

def test_check_refuses_a_version_not_above_the_tag():
    log = "## Non publié\n\n## 0.2.0 - 2026-11-14\n\n- x\n"
    assert check_release("0.2.0", "v0.2.0", log)
    assert check_release("0.1.9", "v0.2.0", log)
    assert check_release("0.2.0", "v0.1.0", log) == []

def test_check_accepts_the_first_release_and_wants_its_section():
    assert check_release("0.1.0", None, "## Non publié\n\n## 0.1.0 - 2026-11-14\n\n- x\n") == []
    assert check_release("0.1.0", None, "## Non publié\n\n- x\n")  # no section of its own
```

And in `tests/test_release_notes.py`:

```python
def test_a_dated_heading_is_found_by_its_version():
    log = "## Non publié\n\n## 0.2.0 - 2026-11-14\n\n- Avdol.\n"
    assert "- Avdol." in notes_for("v0.2.0", log)
```

- [ ] **Step 2: Run them to see them fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_release_pr.py tests/test_release_notes.py -q`
Expected: FAIL (`ModuleNotFoundError: release_pr`, and the dated heading not found).

- [ ] **Step 3: Implement** the pure functions above, `main(argv)` for the three command lines, and in `release_notes.notes_for` match a section whose title's first word is the version (`title.split()[0] == version`). `main` for `X.Y.Z`: refuse unless on `develop`, clean, and equal to `origin/develop` (`git` via `subprocess.run(check=True)`); write both files and the CHANGELOG (date = `datetime.date.today().isoformat()`); `git commit -m "chore: release X.Y.Z"`; `git push origin develop`; `gh pr create --base main --head develop --title "chore: release X.Y.Z" --body-file <notes>` with notes from `release_notes.notes_for`. `--check` reads the last tag with `git describe --tags --abbrev=0 --match "v*"` (no tag → `None`). Makefile: `release-pr: $(VENV_PY)` → `$(PY) tools/release_pr.py $(VERSION)`.

- [ ] **Step 4: Run the tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_release_pr.py tests/test_release_notes.py -q`
Expected: PASS. Then `ruff check . && ruff format --check .` clean.

- [ ] **Step 5: Commit** — `feat: one command prepares a release, and the CI checks the version` (files above).

### Task 2: Workflows and docs (jojo-arena)

**Files:**
- Rewrite: `.github/workflows/ci.yml`, `.github/workflows/release.yml`
- Modify: `.github/workflows/balance.yml`, `.github/dependabot.yml` (`target-branch: "develop"` on both ecosystems)
- Modify: `docs/INFRA.md` (sections "Intégration continue", "Publier"), `CONTRIBUTING.md` (PRs go to `develop`), `README.md` (how a Release is made), `.claude/skills/cut-release/SKILL.md` (new flow: `make release-pr VERSION=…`, merge = Release)

**Interfaces:**
- Consumes: Task 1's `tools/release_pr.py --check` and `--version`.
- Produces: required check names for Task 4's ruleset: job `check` in workflow `CI`.

- [ ] **Step 1: `ci.yml`** — trigger `pull_request` on branches `[develop, main]`, `paths-ignore: ["docs/**", "**/*.md"]`; `concurrency: ci-${{ github.event.pull_request.number }}`, cancel in progress. One job `check`, `timeout-minutes: 30`, `runs-on: ${{ github.event.pull_request.head.repo.full_name == github.repository && fromJSON('["self-hosted","maison"]') || 'ubuntu-latest' }}`. Steps: checkout (`fetch-depth: 0` for tags), setup-python 3.12 with pip cache, install `.[dev]`, ruff check + format check, `pytest -q -n auto`, screenshot tour + artifact (`retention-days: 7`), and **only if `github.base_ref == 'main'`**: `python tools/release_pr.py --check`. Env as today (`SDL_*` dummy, `PYGAME_HIDE_SUPPORT_PROMPT`).

- [ ] **Step 2: `release.yml`** — trigger `push` on `main` (+ `workflow_dispatch`); `permissions: contents: write`. Job `linux` on `[self-hosted, maison]`: tests with coverage (`COVERAGE_CORE: sysmon`) and the coverage summary. Job `windows` (`needs: linux`, `windows-latest`): reads the version (`--version`), and **if `git rev-parse -q --verify refs/tags/v$version` succeeds, writes a `::notice::` "v$version already published" and stops with success** (release skips an existing tag); otherwise tests, `tools/build_exe.py`, smoke test (`--demo --frames 600`), `tools/release_notes.py`, then `gh release create v$version dist/JoJoArena.exe --target $GITHUB_SHA --title "JoJo Arena v$version" --notes-file release-notes.md`.

- [ ] **Step 3: `balance.yml`** — `runs-on: [self-hosted, maison]`; job-level `if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository`.

- [ ] **Step 4: Docs** — INFRA.md: the table of the spec ("Ce qui tourne"), the server-off limit and the admin bypass, the runner's guard in one paragraph pointing to `maison/jojo-runner/`. CONTRIBUTING: base branch `develop`. cut-release skill: `make release-pr VERSION=X.Y.Z`, review the PR, merge, nothing else to push. README: the "Release" lines say the same.

- [ ] **Step 5: Verify** — `.venv/Scripts/python.exe -m pytest -q -n auto` → all green (`test_docs.py` included). The project has no YAML linter: the workflows are validated by their first run in Task 4.

- [ ] **Step 6: Commit** — `ci: pull requests on develop, a release on every merge into main`.

### Task 3: The runner and its guard (maison)

**Files (in `C:/Users/tasda/Documents/Projets/Perso/maison`):**
- Create: `src/garde-runner.js` (pure), `jojo-runner/garde-runner.mjs` (effects), `jojo-runner/garde.sh`, `jojo-runner/entree.sh`, `jojo-runner/Dockerfile`, `jojo-runner/README.md`
- Modify: `docker-compose.yml` (service `jojo-runner`, profile `jojo-runner`), `inventaire/conteneurs.json`, `inventaire/secrets.json`, `README.md` (one row in "Où est quoi"), `docs/journal-de-construction.md` (one entry)
- Test: `test/garde-runner.test.js`

**Interfaces:**
- `jobAutorise({ evenement, depot, charge, depotAttendu }) -> { ok: boolean, raison: string }` in `src/garde-runner.js`. `evenement` = `GITHUB_EVENT_NAME`, `depot` = `GITHUB_REPOSITORY`, `charge` = parsed event JSON (may be `null`).

- [ ] **Step 1: Write the failing tests** (`test/garde-runner.test.js`), each a `jobAutorise` call with `depotAttendu: "CodeByHaamza/jojo-arena"`:
  - `push`, `schedule`, `workflow_dispatch` on the right repo → `ok: true`;
  - `pull_request` whose `charge.pull_request.head.repo.full_name` is the repo → `ok: true`;
  - `pull_request` from `"intrus/jojo-arena"` → `ok: false`, `raison` contains `fork`;
  - `pull_request` with `head.repo: null` → `ok: false`;
  - `pull_request_target`, `workflow_run`, `issue_comment` → `ok: false`;
  - any event with `depot` ≠ `depotAttendu` → `ok: false`;
  - `charge: null` on a `pull_request` → `ok: false`.

- [ ] **Step 2: Run** `npm run test:run -- garde-runner` → FAIL (module missing).

- [ ] **Step 3: Implement** `jobAutorise` (allow-list of events; for `pull_request`, compare `charge?.pull_request?.head?.repo?.full_name` to `depotAttendu`). `garde-runner.mjs`: reads `GITHUB_EVENT_NAME`, `GITHUB_REPOSITORY`, the JSON at `GITHUB_EVENT_PATH` (unreadable → `null`), prints `garde : ok` or `garde : refusé — <raison>`, exits 0 or 1. `garde.sh`: `exec /usr/bin/node /opt/garde/garde-runner.mjs`.

- [ ] **Step 4: Run** `npm run test:run` → all PASS.

- [ ] **Step 5: Image and entry** — `Dockerfile`: `FROM ghcr.io/actions/actions-runner:2.338.2`, `USER root`, `apt-get install -y --no-install-recommends nodejs`, **remove sudo rights** (`gpasswd -d runner sudo` and rewrite `/etc/sudoers` without the `%sudo` NOPASSWD line), copy `src/garde-runner.js` + `jojo-runner/garde-runner.mjs` + `garde.sh` to `/opt/garde` (root-owned, 755), copy `entree.sh` to `/usr/local/bin/entree.sh`, `ENTRYPOINT ["/usr/local/bin/entree.sh"]`. `entree.sh` (runs as root, `set -euo pipefail`): read `JOJO_RUNNER_PAT` from `/run/secrets/jojo-runner.env` **without echoing it**; `curl -fsS -X POST` `https://api.github.com/repos/CodeByHaamza/jojo-arena/actions/runners/registration-token` → registration token (`jq -r .token`); `rm -rf /home/runner/_work/* .runner .credentials .credentials_rsaparams`; `chown -R runner` the tool cache and pip cache; then `exec runuser -u runner -- env -i` with only `HOME`, `PATH`, `RUNNER_TOOL_CACHE=/opt/hostedtoolcache`, `AGENT_TOOLSDIRECTORY=/opt/hostedtoolcache`, `PYTEST_XDIST_AUTO_NUM_WORKERS=3`, `ACTIONS_RUNNER_HOOK_JOB_STARTED=/opt/garde/garde.sh`, `ACTIONS_RUNNER_PRINT_LOG_TO_STDOUT=1`, `RUNNER_MANUALLY_TRAP_SIG=1`, `ImageOS=ubuntu24`, running `./config.sh --unattended --ephemeral --replace --url https://github.com/CodeByHaamza/jojo-arena --token "$TOKEN" --name maison-jojo --labels maison && ./run.sh`.

- [ ] **Step 6: Compose, inventory, docs** — service `jojo-runner`: `profiles: ["jojo-runner"]`, `build: { context: ., dockerfile: jojo-runner/Dockerfile }`, `image: maison-jojo-runner:latest`, `container_name: maison-jojo-runner`, `restart: always`, `cpus: "3"`, `mem_limit: 2g`, `environment: { TZ: Europe/Paris }`, volumes `${HOME}/.secrets/jojo-runner.env:/run/secrets/jojo-runner.env:ro`, `jojo-outils:/opt/hostedtoolcache`, `jojo-pip:/home/runner/.cache/pip`, logging as the others; **no docker.sock**. Inventory: container `maison-jojo-runner` (projet `jojo-arena`, dossier `/home/hamza/maison`, ports `[]`, rôle "runner GitHub éphémère de jojo-arena, sans socket Docker"), secret file entry (`mode 600`, `lu_par maison-jojo-runner`, clés `["JOJO_RUNNER_PAT"]`). Journal entry: why root then `runuser`, why no sudo, why the hook.

- [ ] **Step 7: Build check on the server** — push nothing yet: `scp`-free check by building from the PC is not possible (no Docker daemon here), so after Task 4's push: `ssh maison 'cd ~/maison && docker compose --profile jojo-runner build jojo-runner && docker run --rm --entrypoint sh maison-jojo-runner -c "id runner; sudo -n true 2>&1 | head -1; node --version; ls -l /opt/garde"'` → `runner` has no sudo (error line), node prints a version, `/opt/garde` root-owned.

- [ ] **Step 8: Commit** (maison) — `feat: un runner GitHub pour jojo-arena, qui refuse ce qui ne vient pas du dépôt`.

### Task 4: Switch-over (GitHub, server, first runs)

**Interfaces:**
- Consumes: Tasks 1–3.

- [ ] **Step 1: Push and settings** — `git push -u origin develop`; `gh api -X PATCH repos/CodeByHaamza/jojo-arena -f default_branch=develop`; ruleset on `main` via `gh api -X POST repos/CodeByHaamza/jojo-arena/rulesets --input <json>`: target `branch`, include `refs/heads/main`, rules `deletion`, `non_fast_forward`, `pull_request` (0 approvals), `required_status_checks` (`check`), bypass actor `RepositoryRole` 5 (admin) `always`; fork approval `gh api -X PUT repos/CodeByHaamza/jojo-arena/actions/permissions/fork-pr-contributor-approval -f approval_policy=all_external_contributors`. Check each with a `gh api` GET.

- [ ] **Step 2: Old PRs and branches** — for #2, #3, #4, #5, #7: verify `git merge-base --is-ancestor origin/<head> origin/develop`, then `gh pr close <n> --comment "Intégrée dans develop (fusion du 14/11/2026)."` and `git push origin --delete <head>`. Same for `ci/parallel-tests-and-release-notes` and the closed Dependabot branch (ancestor check first for the former).

- [ ] **Step 3: maison** — push `maison` (its `deploy.sh` requires the commit on GitHub), then on the server: `git -C ~/maison pull --ff-only`, Task 3 Step 7's build check.

- [ ] **Step 4: The owner writes the secret** (only the owner): fine-grained PAT, repository `jojo-arena` only, permission "Administration: Read and write", then on the server `umask 077; read -rs PAT; printf 'JOJO_RUNNER_PAT=%s\n' "$PAT" > ~/.secrets/jojo-runner.env`. Then `docker compose --profile jojo-runner up -d jojo-runner`; `gh api repos/CodeByHaamza/jojo-arena/actions/runners --jq '.runners[] | .name + " " + .status'` → `maison-jojo online`; `node inventaire/verifier.mjs` → no gap.

- [ ] **Step 5: First run** — open the PR of this branch's docs+CI changes from a branch to `develop` (title `ci: …`): job `check` runs on `maison-jojo`, its "Set up runner" step shows `garde : ok`, all green. Then simulate a fork event inside the container: `docker exec maison-jojo-runner sh -c 'echo "{\"pull_request\":{\"head\":{\"repo\":{\"full_name\":\"intrus/x\"}}}}" > /tmp/e.json; GITHUB_EVENT_NAME=pull_request GITHUB_REPOSITORY=CodeByHaamza/jojo-arena GITHUB_EVENT_PATH=/tmp/e.json /opt/garde/garde.sh; echo $?'` → `refusé`, `1`.

- [ ] **Step 6: Report** to the owner: what runs where, the times measured on the first run, and what is left (Discord, first release `make release-pr VERSION=0.1.0`).
