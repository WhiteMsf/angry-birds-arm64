#!/usr/bin/env python3
"""Stage 24.28.1 startup branding / splash asset provenance audit.

Read-only. Finds the exact original splash symbols named by gamelogic.lua and
reports which untouched image metadata containers own them. It does not infer
screen timing/order from byte offsets; the live Lua Proto dump is the authority
for execution flow.
"""
from __future__ import annotations
import os, sys
from pathlib import Path

HEADER = "ANGRY_STAGE24_28_1_STARTUP_BRANDING_ASSET_CONTRACT 1"
NEEDLES = (
    "createStartUpAssets", "updateSplashes", "SPLASHES", "splashes", "splashTimer",
    "SPLASH_CLICKGAMER", "SPLASH_ROVIO", "SPLASH_ANGRY_BIRDS", "SPLASH_LOADING",
    "LITE_SPLASH", "TEXT_SPLASH_LOADING_SPRITE", "mainMenu", "currentMainMenuTheme",
)
SPLASH_SPRITES = (
    "SPLASH_CLICKGAMER", "SPLASH_ROVIO", "SPLASH_ANGRY_BIRDS", "SPLASH_LOADING",
)

def hits(data: bytes, needle: str):
    n = needle.encode("ascii")
    start = 0
    out=[]
    while True:
        i=data.find(n,start)
        if i<0: break
        out.append(i); start=i+max(1,len(n))
    return out

def ascii_context(data: bytes, off: int, radius: int=96) -> str:
    lo=max(0,off-radius); hi=min(len(data),off+radius)
    b=data[lo:hi]
    return ''.join(chr(x) if 32<=x<127 else '.' for x in b)

def main() -> int:
    if len(sys.argv) != 4:
        print("usage: stage24281_startup_branding_contract.py <scripts-dir> <image-root> <localization-root>", file=sys.stderr)
        return 2
    scripts=Path(sys.argv[1]); image=Path(sys.argv[2]); loc=Path(sys.argv[3])
    game=scripts/'gamelogic.lua'
    print(HEADER)
    print("policy=READ_ONLY; branding is inventoried but NOT displayed by Stage24.28.1")
    print("authority=Lua runtime Proto dump determines execution flow; binary offsets below are provenance only")
    print(f"gamelogic={game}")
    print(f"imageRoot={image}")
    print(f"localizationRoot={loc}")
    if not game.is_file():
        print(f"ERROR missing={game}"); return 3
    data=game.read_bytes()
    print("\n--- GAMELOGIC_SYMBOL_PROVENANCE ---")
    missing=[]
    for n in NEEDLES:
        hs=hits(data,n)
        print(f"needle={n!r} hits={len(hs)} offsets={','.join(hex(x) for x in hs[:12]) or '-'}")
        for off in hs[:3]: print(f"  context@0x{off:x}={ascii_context(data,off)}")
        if n in ("createStartUpAssets","updateSplashes","SPLASH_ROVIO","SPLASH_ANGRY_BIRDS","SPLASH_LOADING") and not hs:
            missing.append(n)

    print("\n--- SPLASH_SPRITE_OWNERS ---")
    dats=sorted(image.glob('*.dat')) if image.is_dir() else []
    owners={n:[] for n in SPLASH_SPRITES}
    for p in dats:
        try: b=p.read_bytes()
        except OSError: continue
        for n in SPLASH_SPRITES:
            hs=hits(b,n)
            if hs: owners[n].append((p.name,hs))
    for n in SPLASH_SPRITES:
        rows=owners[n]
        print(f"sprite={n!r} owners={len(rows)}")
        for fn,hs in rows:
            print(f"  file={fn!r} offsets={','.join(hex(x) for x in hs[:12])}")

    print("\n--- SPLASH_TEXTURE_REFERENCES ---")
    for p in dats:
        try: b=p.read_bytes()
        except OSError: continue
        if not any(p.name==fn for n in SPLASH_SPRITES for fn,_ in owners[n]):
            continue
        # Extract printable texture-like runs.
        runs=[]; start=None
        for i,x in enumerate(b+b'\x00'):
            if 32<=x<127:
                if start is None: start=i
            else:
                if start is not None and i-start>=4:
                    t=b[start:i].decode('ascii','replace')
                    if t.lower().endswith(('.pvr','.png')): runs.append(t)
                start=None
        print(f"meta={p.name!r} textures={','.join(dict.fromkeys(runs)) or '-'}")

    print("\n--- LOCALIZATION_PROVENANCE ---")
    if loc.is_dir():
        for needle in ("TEXT_SPLASH_LOADING_SPRITE", "CLICKGAMER", "ROVIO", "ANGRY_BIRDS"):
            rows=[]
            nb=needle.lower().encode('ascii')
            for p in sorted(loc.glob('*.dat')):
                try: b=p.read_bytes().lower()
                except OSError: continue
                i=b.find(nb)
                if i>=0: rows.append((p.name,i))
            print(f"needle={needle!r} files={len(rows)} " + ' '.join(f"{fn}@0x{off:x}" for fn,off in rows[:20]))

    required_owner_missing=[n for n in ("SPLASH_ROVIO","SPLASH_ANGRY_BIRDS","SPLASH_LOADING") if not owners[n]]
    print("\n--- VERDICT ---")
    print(f"requiredLuaSymbolsMissing={len(missing)} values={','.join(missing) or '-'}")
    print(f"requiredSpriteOwnersMissing={len(required_owner_missing)} values={','.join(required_owner_missing) or '-'}")
    # Clickgamer is edition/distribution dependent; never make it a hard requirement.
    print(f"clickgamerPresentInLua={'yes' if hits(data,'SPLASH_CLICKGAMER') else 'no'} ownerCount={len(owners['SPLASH_CLICKGAMER'])} policy=OPTIONAL_EDITION_DEPENDENT")
    if missing:
        print("verdict=FAIL_REQUIRED_LUA_SYMBOLS_MISSING")
        return 4
    if required_owner_missing:
        print("verdict=PASS_WITH_UNRESOLVED_SPRITE_OWNERS")
        return 0
    print("verdict=PASS")
    return 0

if __name__=='__main__':
    raise SystemExit(main())
