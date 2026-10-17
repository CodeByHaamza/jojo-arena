"""The animated PNG written for the README: a real PNG, and a real animation."""

import io
import struct
import zlib

import pygame
import pytest

from tools.make_apng import SIGNATURE, encode_apng, write_apng

SIZE = (8, 6)


def frames(count: int) -> list[pygame.Surface]:
    out = []
    for i in range(count):
        surface = pygame.Surface(SIZE, pygame.SRCALPHA)
        surface.fill((30 * i, 100, 200, 255))
        out.append(surface)
    return out


def chunks(data: bytes) -> list[tuple[str, bytes]]:
    """Every chunk of the file, checking its CRC on the way through."""
    out, pos = [], len(SIGNATURE)
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        kind, body = data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length : pos + 12 + length])[0]
        assert crc == zlib.crc32(kind + body), kind
        out.append((kind.decode(), body))
        pos += 12 + length
    return out


def test_it_is_a_png_any_viewer_can_open():
    data = encode_apng(frames(3), SIZE, delay_ms=50)
    assert data.startswith(SIGNATURE)
    kinds = [kind for kind, _ in chunks(data)]
    assert kinds[0] == "IHDR" and kinds[-1] == "IEND"
    assert kinds.index("acTL") < kinds.index("IDAT")  # the animation is declared first
    picture = pygame.image.load(io.BytesIO(data), "clip.png")
    assert picture.get_size() == SIZE  # and the first frame still loads as a picture


def test_every_frame_is_there_and_numbered_in_order():
    count = 5
    data = encode_apng(frames(count), SIZE, delay_ms=40)
    parts = chunks(data)
    controls = [body for kind, body in parts if kind == "fcTL"]
    assert len(controls) == count  # one control chunk per frame
    assert len([1 for kind, _ in parts if kind == "fdAT"]) == count - 1  # the first is the IDAT
    numbers = [struct.unpack(">I", body[:4])[0] for kind, body in parts if kind in ("fcTL", "fdAT")]
    assert numbers == list(range(len(numbers)))  # APNG refuses a sequence with a gap
    total, loops = struct.unpack(">II", dict(parts)["acTL"])
    assert total == count and loops == 0  # 0: forever


def test_the_delay_is_the_one_asked_for():
    body = [b for kind, b in chunks(encode_apng(frames(2), SIZE, delay_ms=125)) if kind == "fcTL"]
    numerator, denominator = struct.unpack(">HH", body[0][20:24])
    assert (numerator, denominator) == (125, 1000)


def test_an_animation_needs_a_frame():
    with pytest.raises(ValueError):
        encode_apng([], SIZE)


def test_it_writes_the_file_and_takes_the_size_from_the_first_frame(tmp_path):
    path = write_apng(tmp_path / "clip.png", frames(2))
    assert path.exists()
    assert pygame.image.load(str(path)).get_size() == SIZE
