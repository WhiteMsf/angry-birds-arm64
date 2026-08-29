#!/usr/bin/env python3
import struct, sys
from pathlib import Path

if len(sys.argv) != 2:
    print('usage: pvr_v2_rgba4444_audit.py <file.pvr>', file=sys.stderr)
    raise SystemExit(2)

path = Path(sys.argv[1])
data = path.read_bytes()
if len(data) < 52:
    print(f'[stage24.14.4-pvr] header audit FAIL short file={path} bytes={len(data)}', file=sys.stderr)
    raise SystemExit(1)
(header, height, width, mip, flags, data_len, bpp,
 rmask, gmask, bmask, amask, tag, surfaces) = struct.unpack_from('<13I', data, 0)

def etc1_level_bytes(w, h):
    bw = (max(4, w) + 3) // 4
    bh = (max(4, h) + 3) // 4
    return bw * bh * 8

mw, mh = width, height
expected4444 = 0
expected_etc1 = 0
valid_dims = width > 0 and height > 0 and mip <= 31
if valid_dims:
    for level in range(mip + 1):
        expected4444 += mw * mh * 2
        expected_etc1 += etc1_level_bytes(mw, mh)
        if level != mip:
            if mw == 1 and mh == 1:
                valid_dims = False
                break
            mw = max(1, mw // 2)
            mh = max(1, mh // 2)
ptype = flags & 0xff
common = header == 52 and tag == 0x21525650 and surfaces == 1 and valid_dims and len(data) == header + data_len
rgba4444 = (
    common and ptype == 0x10 and bpp == 16 and
    rmask == 0x0000f000 and gmask == 0x00000f00 and
    bmask == 0x000000f0 and amask == 0x0000000f and
    expected4444 == data_len
)
etc1 = (
    common and ptype == 0x36 and bpp == 4 and
    rmask == 0xffffffff and gmask == 0xffffffff and
    bmask == 0xffffffff and amask == 0x00000000 and
    expected_etc1 == data_len
)
contract = 'RGBA4444-v2-mipchain-PASS' if rgba4444 else ('ETC1-v2-mipchain-PASS' if etc1 else 'UNSUPPORTED')
print(
    f'[stage24.14.4-pvr] header audit file={path.name} bytes={len(data)} '
    f'header={header} size={width}x{height} mipAdditional={mip} levels={mip+1} '
    f'flags=0x{flags:08x} type=0x{ptype:02x} data={data_len} bpp={bpp} '
    f'masks={rmask:08x}/{gmask:08x}/{bmask:08x}/{amask:08x} '
    f'tag=0x{tag:08x} surfaces={surfaces} expected4444={expected4444} '
    f'expectedETC1={expected_etc1} contract={contract}'
)
# Diagnostic only; runtime remains the strict final gate.
raise SystemExit(0)
