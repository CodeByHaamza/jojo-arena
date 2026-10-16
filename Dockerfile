# A reproducible "make check" box: lint, format and the whole test suite, with no screen.
#
# The game itself ships as a Windows .exe (PyInstaller); this image is NOT for playing,
# it is for checking the code the same way everywhere - handy on Linux and macOS, and to
# reproduce a CI failure locally.
#
#   docker build -t jojo-arena .
#   docker run --rm jojo-arena                 # lint + format + tests
#   docker run --rm jojo-arena pytest -q tests/test_dummy.py
#   docker run --rm -v "$PWD/screenshots:/app/screenshots" jojo-arena \
#       python tools/screenshot_tour.py screenshots/tour
FROM python:3.12-slim

# SDL needs these shared libraries even with the dummy video and audio drivers.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libsdl2-2.0-0 \
        libsdl2-image-2.0-0 \
        libsdl2-mixer-2.0-0 \
        libsdl2-ttf-2.0-0 \
        libfreetype6 \
        libjpeg62-turbo \
        libportmidi0 \
    && rm -rf /var/lib/apt/lists/*

ENV SDL_VIDEODRIVER=dummy \
    SDL_AUDIODRIVER=dummy \
    PYGAME_HIDE_SUPPORT_PROMPT=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# The heavy dependencies first, so editing the game does not reinstall them. They are
# kept in step with pyproject.toml by the `pip install -e .` below, which is the source
# of truth: this layer is only a cache.
RUN pip install "pygame-ce>=2.5.8" "pytest>=8" "pytest-cov>=5" "ruff>=0.6"

COPY . .
RUN pip install --no-deps -e .

CMD ["sh", "-c", "ruff check . && ruff format --check . && pytest -q"]
