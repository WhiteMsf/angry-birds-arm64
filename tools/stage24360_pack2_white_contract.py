#!/usr/bin/env python3
"""Stage 24.36.0 Poached Eggs theme2 2-6..2-14 + untouched White/DROPPABLE_EGG contract."""
from pathlib import Path
import hashlib, sys
if len(sys.argv) != 4:
    raise SystemExit("usage: stage24360_pack2_white_contract.py <build.ps1> <stage24.cpp> <scripts-dir>")
build=Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
game=Path(sys.argv[3])/'gamelogic.lua'
if not game.is_file(): raise SystemExit(f'missing untouched gamelogic.lua: {game}')
raw=game.read_bytes()
def strings(data,n=4):
    out=[]; cur=bytearray()
    for b in data:
        if 32 <= b <= 126: cur.append(b)
        else:
            if len(cur)>=n: out.append(cur.decode('ascii','ignore'))
            cur.clear()
    if len(cur)>=n: out.append(cur.decode('ascii','ignore'))
    return out
joined='\n'.join(strings(raw))
expected=[
 ('2-6','Level36'),('2-7','Level31'),('2-8','Level21'),
 ('2-9','Level41'),('2-10','Level76'),('2-11','Level38'),
 ('2-12','Level35'),('2-13','Level20'),('2-14','Level26')
]
errors=[]
print('ANGRY_STAGE24_36_0_PACK2_WHITE_CONTRACT 1')
print('mapping_source=untouched levelOrder.pack2 runtime table captured by Stage24.28.0')
for human,phys in expected:
    stem=phys[5:]
    checks=[
        f"$level{stem}p2" in build,
        f"levels\\pack2\\{phys}.lua" in build,
        f"'{phys}.lua') -Force" in build,
        f'{{"stage24/data/levels/pack2/{phys}.lua", "data/levels/pack2/{phys}.lua"}}' in cpp,
    ]
    ok=all(checks)
    print(f'LEVEL human={human} physical={phys} transport={"PASS" if ok else "FAIL"}')
    if not ok: errors.append(f'transport {human}={phys}')
full='Level52,Level34,Level42,Level24,Level88,Level36,Level31,Level21,Level41,Level76,Level38,Level35,Level20,Level26'
checks={
    'pack2_map_observer':'[stage24.36.0-white] MAP_SUMMARY' in cpp,
    'pack2_map_range':'levelIndex >= 22 && levelIndex <= 35' in cpp,
    'pack2_expected_sequence':full in cpp,
    'pack2_exact_folder':'data/levels/pack2/' in cpp,
    'pack2_next_probe':'stage24.36.0-white-chain' in cpp,
    'generic_specialty_observer':'[stage24.32.1-specialty] STATE' in cpp,
    'white_create_observer':'[stage24.36.0-white] EGG_CREATE' in cpp,
    'no_native_white_sprite_case':'BIRD_WHITE' not in cpp,
    'no_native_drop_assignment':'birdSpecialty = "DROPPABLE_EGG"' not in cpp and "birdSpecialty='DROPPABLE_EGG'" not in cpp,
    'no_native_flying_grenade_mutation':'flyingGrenades' not in cpp,
}
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')
    if not v: errors.append(k)
for tok in ('birdSpecialtyAvailable','birdSpecialty','specialty','DROPPABLE_EGG','createCircle','flyingGrenades','setVelocity','setRotation','setSprite','specialSound'):
    ok=tok in joined
    print(f'ORIGINAL_GAMELOGIC_TOKEN token={tok!r} present={"PASS" if ok else "FAIL"}')
    if not ok: errors.append('gamelogic token '+tok)
print(f'ORIGINAL_GAMELOGIC sha256={hashlib.sha256(raw).hexdigest()} bytes={len(raw)} copied_into_project=NO')
print('white_runtime_authority=untouched updateGame DROPPABLE_EGG branch -> createCircle/setVelocity/flyingGrenades')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
