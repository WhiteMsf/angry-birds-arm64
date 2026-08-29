#!/usr/bin/env python3
import argparse, binascii, struct, zlib
from pathlib import Path

PVR2_TAG = 0x21525650
RGBA4444 = 0x10


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (struct.pack('>I', len(payload)) + kind + payload +
            struct.pack('>I', binascii.crc32(kind + payload) & 0xffffffff))


def decode(src: Path, dst: Path):
    data = src.read_bytes()
    if len(data) < 52:
        raise SystemExit(f"PVR too small: {src}")
    (header_len, height, width, mip_count, flags, data_len, bpp,
     rmask, gmask, bmask, amask, tag, surfaces) = struct.unpack_from('<13I', data, 0)
    pixel_type = flags & 0xff
    if header_len != 52 or tag != PVR2_TAG:
        raise SystemExit(f"Unsupported/non-v2 PVR: header={header_len} tag=0x{tag:08X}")
    if pixel_type != RGBA4444:
        raise SystemExit(f"Expected GL_RGBA_4444 pixelType 0x10, got 0x{pixel_type:02X}")
    if bpp != 16 or (rmask,gmask,bmask,amask) != (0xF000,0x0F00,0x00F0,0x000F):
        raise SystemExit(
            f"Unexpected RGBA4444 layout: bpp={bpp} masks="
            f"{rmask:08X},{gmask:08X},{bmask:08X},{amask:08X}")
    if mip_count != 0 or surfaces != 1:
        raise SystemExit(f"Unexpected topology: mipField={mip_count} surfaces={surfaces}")

    payload = data[header_len:]
    expected = width * height * 2
    if data_len != expected or len(payload) != expected:
        raise SystemExit(
            f"Payload mismatch: header={data_len} actual={len(payload)} expected={expected}")

    # Preserve PVR payload row order as PNG top-to-bottom row order. We do not
    # silently choose KA3D's SPRT Y-origin; Stage23.2 exposes that as a toggle.
    scan = bytearray()
    nonzero_alpha = 0
    opaque = 0
    for y in range(height):
        scan.append(0)  # PNG filter type 0
        row = y * width
        for x in range(width):
            i = row + x
            v = payload[2*i] | (payload[2*i+1] << 8)
            r = ((v >> 12) & 0xF) * 17
            g = ((v >> 8) & 0xF) * 17
            b = ((v >> 4) & 0xF) * 17
            a = (v & 0xF) * 17
            if a: nonzero_alpha += 1
            if a == 255: opaque += 1
            scan += bytes((r,g,b,a))

    signature = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    png = signature + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(bytes(scan), 6)) + chunk(b'IEND', b'')
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(png)
    print(
        f"[stage23.2-atlas] {src.name} -> {dst.name} size={width}x{height} "
        f"pixels={width*height} nonzeroAlpha={nonzero_alpha} opaque={opaque} pngBytes={len(png)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    a = ap.parse_args()
    decode(Path(a.src), Path(a.dst))

if __name__ == '__main__':
    main()
