from __future__ import annotations
import hashlib
import struct
import zlib
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"

def sha256_file(path: str | Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

def write_fake_rgb_png(path: str | Path, width: int, height: int) -> None:
    # Dependency-free deterministic RGB image used ONLY by fake/unit tests.
    row = bytes([32, 96, 48]) * width
    raw = b"".join(b"\x00" + row for _ in range(height))
    data = PNG_SIG + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + _chunk(b"IDAT", zlib.compress(raw, 6)) + _chunk(b"IEND", b"")
    Path(path).write_bytes(data)

def inspect_png(path: str | Path, expected_width: int | None = None, expected_height: int | None = None) -> dict:
    p = Path(path)
    raw = p.read_bytes()
    if len(raw) < 33 or not raw.startswith(PNG_SIG):
        raise ValueError("invalid PNG signature")
    width, height, bit_depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", raw[16:29])
    if bit_depth != 8 or color_type not in (2, 6):
        raise ValueError("expected 8-bit RGB/RGBA PNG")
    if expected_width is not None and width != expected_width:
        raise ValueError(f"unexpected PNG width {width}")
    if expected_height is not None and height != expected_height:
        raise ValueError(f"unexpected PNG height {height}")
    return {"filename": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p), "format": "PNG", "mode": "RGB" if color_type == 2 else "RGBA", "width": width, "height": height}
