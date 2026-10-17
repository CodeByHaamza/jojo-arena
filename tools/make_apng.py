"""Write an animated PNG from a list of frames, with nothing but the standard library.

An APNG is a PNG with three extra chunk types: `acTL` before the image data says how
many frames there are, `fcTL` describes one frame, and `fdAT` carries the pixels of
every frame after the first. The first frame stays in the usual `IDAT`, so any viewer
that knows nothing about APNG still shows a picture - which is what we want for a
README on a platform that may or may not animate it.

    from tools.make_apng import write_apng
    write_apng(Path("clip.png"), frames, delay_ms=50)   # frames: pygame Surfaces

Kept dependency-free on purpose: the sprites, the sounds and the icons of this project
are all generated in code, and so is this.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Protocol

SIGNATURE = b"\x89PNG\r\n\x1a\n"


class Frame(Protocol):
    """What this module needs of a frame: its size, and its pixels as RGBA bytes."""

    def get_size(self) -> tuple[int, int]: ...


def _chunk(kind: bytes, data: bytes) -> bytes:
    """One PNG chunk: length, type, data, CRC of type and data."""
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def _raw(pixels: bytes, width: int, height: int) -> bytes:
    """Scanlines with a filter byte each (0: no filter), as PNG stores them."""
    stride = width * 4
    rows = [b"\x00" + pixels[y * stride : (y + 1) * stride] for y in range(height)]
    return zlib.compress(b"".join(rows), 9)


def _pixels_of(frame) -> bytes:
    """The frame's pixels as RGBA, whether it is a pygame Surface or raw bytes."""
    if isinstance(frame, bytes | bytearray):
        return bytes(frame)
    import pygame

    return pygame.image.tobytes(frame, "RGBA")


def encode_apng(frames: list, size: tuple[int, int], delay_ms: int = 50, loops: int = 0) -> bytes:
    """The bytes of an animated PNG: every frame the same size, shown `delay_ms` each."""
    if not frames:
        raise ValueError("an animation needs at least one frame")
    width, height = size
    out = [SIGNATURE]
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    out.append(_chunk(b"IHDR", header))
    out.append(_chunk(b"acTL", struct.pack(">II", len(frames), loops)))
    # Delays are a fraction: milliseconds are a numerator over 1000.
    control = struct.pack(">IIIIIHHBB", 0, width, height, 0, 0, delay_ms, 1000, 0, 0)
    out.append(_chunk(b"fcTL", control))
    out.append(_chunk(b"IDAT", _raw(_pixels_of(frames[0]), width, height)))
    sequence = 1
    for frame in frames[1:]:
        control = struct.pack(">IIIIIHHBB", sequence, width, height, 0, 0, delay_ms, 1000, 0, 0)
        out.append(_chunk(b"fcTL", control))
        sequence += 1
        data = struct.pack(">I", sequence) + _raw(_pixels_of(frame), width, height)
        out.append(_chunk(b"fdAT", data))
        sequence += 1
    out.append(_chunk(b"IEND", b""))
    return b"".join(out)


def write_apng(path: Path, frames: list, delay_ms: int = 50, loops: int = 0) -> Path:
    """Write the animation to `path`; the size is taken from the first frame."""
    first = frames[0]
    size = first.get_size() if hasattr(first, "get_size") else None
    if size is None:
        raise ValueError("pass pygame Surfaces, or call encode_apng with a size")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_apng(frames, size, delay_ms, loops))
    return path
