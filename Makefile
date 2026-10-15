# JoJo Arena - shortcuts for everyday tasks. Type `make` to list them.
#
# Needs GNU make: already there on Linux and macOS. On Windows, any GNU make works
# (`winget install ezwinports.make`, `choco install make`, or mingw32-make).
# Every command only calls Python, so it works the same from PowerShell, cmd or Git Bash.
#
# Variables you can override: make training P1=dio_p3 P2=polnareff
#                             make install PYTHON=py   (the Python that creates .venv)
#                             make run ARGS="--scene select --mode training"

VENV ?= .venv
ifeq ($(OS),Windows_NT)
    PYTHON ?= python
    VENV_PY := $(VENV)/Scripts/python.exe
else
    PYTHON ?= python3
    VENV_PY := $(VENV)/bin/python
endif

PY := "$(VENV_PY)"
EMPTY :=
INDENT := $(EMPTY)  $(EMPTY)
P1 ?= jotaro_p3
P2 ?= dio_p3
ROUNDS ?= 3
SCENE ?= title
ARGS ?=

.DEFAULT_GOAL := help
.PHONY: help install run menu training fight versus demo test test-fast lint format check \
        screens screenshot sprites exe clean

help:
	$(info JoJo Arena - make targets)
	$(info )
	$(info Setup)
	$(info $(INDENT)make install      create .venv and install the game with its dev tools)
	$(info )
	$(info Play)
	$(info $(INDENT)make run          start the game on the title screen (ARGS=... for options))
	$(info $(INDENT)make menu         start on the main menu)
	$(info $(INDENT)make training     training mode with P1 against the dummy P2)
	$(info $(INDENT)make fight        straight into a local fight P1 against P2)
	$(info $(INDENT)make versus       VS screen P1 against P2 (rounds and controls))
	$(info $(INDENT)make demo         computer against computer)
	$(info )
	$(info Check)
	$(info $(INDENT)make test         all the tests)
	$(info $(INDENT)make test-fast    tests without the slow whole-game smoke tests)
	$(info $(INDENT)make lint         ruff lint and format check (same as the CI))
	$(info $(INDENT)make format       fix the formatting and the lint issues that can be fixed)
	$(info $(INDENT)make check        lint then tests: run this before a commit)
	$(info $(INDENT)make screens      screenshot tour of every screen into screenshots/tour/)
	$(info $(INDENT)make screenshot   picture of one screen: SCENE=menu or select or options...)
	$(info )
	$(info Build)
	$(info $(INDENT)make sprites      regenerate the character sprite sheets from their looks)
	$(info $(INDENT)make exe          build dist/JoJoArena.exe)
	$(info $(INDENT)make clean        delete build/ dist/ and the caches)
	$(info )
	$(info Now: P1=$(P1) P2=$(P2) ROUNDS=$(ROUNDS) SCENE=$(SCENE))
	@exit 0

# The virtual environment is created on first use by any target that needs it.
$(VENV_PY):
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -e ".[dev]"

install: $(VENV_PY)
	$(PY) -m pip install -e ".[dev]"

# Play -----------------------------------------------------------------------------------

run: $(VENV_PY)
	$(PY) -m jojo_arena $(ARGS)

menu: $(VENV_PY)
	$(PY) -m jojo_arena --scene menu $(ARGS)

training: $(VENV_PY)
	$(PY) -m jojo_arena --scene training --p1 $(P1) --p2 $(P2) $(ARGS)

fight: $(VENV_PY)
	$(PY) -m jojo_arena --scene fight --p1 $(P1) --p2 $(P2) --rounds $(ROUNDS) $(ARGS)

versus: $(VENV_PY)
	$(PY) -m jojo_arena --scene setup --p1 $(P1) --p2 $(P2) --rounds $(ROUNDS) $(ARGS)

demo: $(VENV_PY)
	$(PY) -m jojo_arena --demo --p1 $(P1) --p2 $(P2) $(ARGS)

# Check ----------------------------------------------------------------------------------

test: $(VENV_PY)
	$(PY) -m pytest -q

test-fast: $(VENV_PY)
	$(PY) -m pytest -q --ignore=tests/test_app.py

lint: $(VENV_PY)
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

format: $(VENV_PY)
	$(PY) -m ruff format .
	$(PY) -m ruff check --fix .

check: lint test

screens: $(VENV_PY)
	$(PY) tools/screenshot_tour.py screenshots/tour

screenshot: $(VENV_PY)
	$(PY) -m jojo_arena --scene $(SCENE) --p1 $(P1) --p2 $(P2) --frames 90 --screenshot screenshots/$(SCENE).png

# Build ----------------------------------------------------------------------------------

sprites: $(VENV_PY)
	$(PY) tools/make_sprites.py

exe: $(VENV_PY)
	$(PY) tools/build_exe.py

clean:
	$(PY) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', '.pytest_cache', '.ruff_cache', *pathlib.Path('.').glob('[jt]*/**/__pycache__')]]"
