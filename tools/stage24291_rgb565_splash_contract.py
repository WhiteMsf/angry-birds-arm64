#!/usr/bin/env python3
import struct, sys, zipfile
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: stage24291_rgb565_splash_contract.py <imageRoot> <stage24_live_surface.cpp>")

image_root = Path(sys.argv[1])
source = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")

def get_bytes(name):
    direct = image_root / name
    if direct.is_file():
        return direct.read_bytes(), str(direct)
    zpath = image_root / (name + ".zip")
    if zpath.is_file():
        with zipfile.ZipFile(zpath, "r") as z:
            members = [m for m in z.namelist() if not m.endswith("/") and Path(m).name.lower() == name.lower()]
            if len(members) != 1:
                raise RuntimeError(f"{zpath}: expected exactly one {name} member, got {members}")
            return z.read(members[0]), f"{zpath}!{members[0]}"
    raise FileNotFoundError(f"missing original texture: {direct} or {zpath}")

def le32(b, off):
    return struct.unpack_from("<I", b, off)[0]

def audit(name, required=True):
    try:
        b, origin = get_bytes(name)
    except FileNotFoundError:
        if required:
            raise
        print(f"texture={name} present=no")
        return
    if len(b) < 52:
        raise RuntimeError(f"{name}: shorter than PVR v2 header")
    h = dict(
        header=le32(b,0), height=le32(b,4), width=le32(b,8), mip=le32(b,12),
        flags=le32(b,16), data=le32(b,20), bpp=le32(b,24),
        r=le32(b,28), g=le32(b,32), bl=le32(b,36), a=le32(b,40),
        tag=le32(b,44), surfaces=le32(b,48))
    typ = h["flags"] & 0xff
    w,hgt = h["width"],h["height"]
    expected = 0
    mw,mh=w,hgt
    valid = w>0 and hgt>0 and h["mip"] <= 31
    if valid:
        for level in range(h["mip"]+1):
            expected += mw*mh*2
            if level != h["mip"]:
                if mw == mh == 1:
                    valid=False
                    break
                mw=max(1,mw>>1); mh=max(1,mh>>1)
    exact = (
        h["header"] == 52 and h["tag"] == 0x21525650 and typ == 0x13 and
        h["bpp"] == 16 and h["surfaces"] == 1 and
        h["r"] == 0x0000f800 and h["g"] == 0x000007e0 and
        h["bl"] == 0x0000001f and h["a"] == 0 and valid and
        expected == h["data"] and len(b) == h["header"] + h["data"])
    print(
        f"texture={name} origin={origin} size={w}x{hgt} mipAdditional={h['mip']} "
        f"type=0x{typ:02x} bpp={h['bpp']} masks={h['r']:08x}/{h['g']:08x}/{h['bl']:08x}/{h['a']:08x} "
        f"payload={h['data']} expectedRGB565={expected} exactRGB565={'yes' if exact else 'no'}")
    if not exact:
        raise RuntimeError(f"{name}: not the exact proven PVR v2 GL_RGB_565 contract")

print("ANGRY_STAGE24_29_1_RGB565_SPLASH_CONTRACT 1")
audit("SPLASHES_SHEET_1.pvr", True)
audit("SPLASHES_SHEET_2.pvr", True)
audit("BACKGROUNDS_GE_1.pvr", False)
audit("BACKGROUNDS_MAIN_1.pvr", False)

checks = {
    "source_rgb565_flag": "bool rgb565 = false;" in source,
    "source_pixel_type_13": "pixelType == 0x13u" in source,
    "source_masks_565": "rMask == 0x0000f800u" in source and "gMask == 0x000007e0u" in source and "bMask == 0x0000001fu" in source,
    "source_gl_rgb": "GL_UNSIGNED_SHORT_5_6_5" in source and "pixelFormat = a.rgb565 ? GL_RGB : GL_RGBA" in source,
    "source_no_conversion": "a.bytes.data() + offset" in source,
}
for k,v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
if not all(checks.values()):
    raise SystemExit(2)
print("VERDICT=PASS exact original PVR v2 RGB565 splash payload accepted byte-identically; GLES upload uses GL_RGB/GL_UNSIGNED_SHORT_5_6_5")
