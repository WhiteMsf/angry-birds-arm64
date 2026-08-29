#!/usr/bin/env python3
"""Stage 24.32.1 static transport/input/specialty contract.

Read-only build preflight. It proves that the project transports the original
Pack1 level files through human 1-10, that Android multi-pointer state feeds the
existing Lua zoom producer without directly owning camera/worldScale, and that
the untouched 1.4.2 gamelogic payload still contains the specialty vocabulary
needed by the CLUSTER_BOMB branch. It does not claim to reconstruct the exact
legacy Java/NDK gesture producer.
"""
from pathlib import Path
import re, sys, hashlib

if len(sys.argv) != 4:
    raise SystemExit("usage: stage24321_pack1_multitouch_specialty_contract.py <build.ps1> <stage24.cpp> <scripts-dir>")
build=Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
scripts=Path(sys.argv[3])
game=scripts/'gamelogic.lua'
if not game.is_file():
    raise SystemExit(f"missing untouched gamelogic.lua: {game}")
raw=game.read_bytes()

def printable_strings(data, n=4):
    out=[]; cur=bytearray()
    for b in data:
        if 32 <= b <= 126:
            cur.append(b)
        else:
            if len(cur)>=n: out.append(cur.decode('ascii','ignore'))
            cur.clear()
    if len(cur)>=n: out.append(cur.decode('ascii','ignore'))
    return out
strings=printable_strings(raw)
joined='\n'.join(strings)
expected=[
 ('1-1','Level1'),('1-2','Level57'),('1-3','Level53'),('1-4','Level3'),
 ('1-5','Level6'),('1-6','Level2'),('1-7','Level4'),('1-8','Level5'),
 ('1-9','Level7'),('1-10','Level8')]
errors=[]
print('ANGRY_STAGE24_32_1_PACK1_MULTITOUCH_SPECIALTY_CONTRACT 1')
print('policy=transport-original-levels; stock-lua-progression; evidence-derived-android-pinch; specialty-observe-only')
print('mapping_source=untouched levelSelectionPagesBasic runtime inventory recovered in prior diagnostic')
for human,phys in expected:
    var='$level'+phys.removeprefix('Level') if phys!='Level1' else '$level1'
    # physical filenames must be copied to staged pack1 tree
    copy_pat=f"'{phys}.lua') -Force"
    ok=(f"{phys}.lua" in build and copy_pat in build)
    print(f"LEVEL human={human} physical={phys} staged={'PASS' if ok else 'FAIL'}")
    if not ok: errors.append(f'missing transport for {human}={phys}')

checks={
 'android_pointer_count':'AMotionEvent_getPointerCount' in cpp and 'pointerCount' in cpp,
 'secondary_coords':'x2' in cpp and 'y2' in cpp,
 'lua_touchcount_actual':'lua_setglobal(L, "touchcount")' in cpp and 'touch.pointerCount' in cpp,
 'pinch_logs':'[stage24.32.1-multitouch] PINCH' in cpp,
 'zoomlevel_bridge':'get_global_number(L, "zoomLevel")' in cpp and 'spanDelta * 0.00124999997' in cpp and 'lua_setglobal(L, "zoomLevel")' in cpp,
 'evidence_scalar':'0.00124999997' in cpp,
 'gameplay_only':'!stage24133MenuMode && touch.pointerCount >= 2' in cpp,
 'specialty_observer':'[stage24.32.1-specialty] STATE' in cpp,
 'stock_progression_map':'Level1,Level57,Level53,Level3,Level6,Level2,Level4,Level5,Level7,Level8' in cpp,
}
# In the pinch implementation block, direct setWorldScale would violate ownership.
start=cpp.find('// Two-finger pinch:')
end=cpp.find('        if (touch.pressed)', start)
pinch_block=cpp[start:end] if start >= 0 and end > start else ''
checks['pinch_does_not_call_setWorldScale']='setWorldScale' not in pinch_block
checks['no_blue_name_special_case']=not re.search(r'if\s*\([^\n]*(?:Blue|BLUE)', cpp)
for name,ok in checks.items():
    print(f"CHECK {name}={'PASS' if ok else 'FAIL'}")
    if not ok: errors.append(name)

# These symbols are fingerprints in the user's untouched compiled gamelogic.
# Exact opcode ownership is diagnosed at runtime; this is only a byte-payload
# presence check so no proprietary script bytes are copied into the project.
specialty_tokens=['birdSpecialtyAvailable','birdSpecialty','CLUSTER_BOMB','createCircle','setVelocity','setRotation','setSprite','parentName','specialty']
for tok in specialty_tokens:
    ok=tok in joined
    print(f"ORIGINAL_GAMELOGIC_TOKEN token={tok!r} present={'PASS' if ok else 'FAIL'}")
    if not ok: errors.append('gamelogic token '+tok)
print(f"ORIGINAL_GAMELOGIC sha256={hashlib.sha256(raw).hexdigest()} bytes={len(raw)} copied_into_project=NO")
print('specialty_runtime_authority=untouched updateGame closure; native bridge does not synthesize CLUSTER_BOMB clones')
print('pinch_exactness=COMPATIBILITY_BRIDGE_NOT_LEGACY_PRODUCER_CLAIM')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
