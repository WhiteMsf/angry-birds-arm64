#!/usr/bin/env python3
"""Stage 24.35.0 Poached Eggs theme2 2-1..2-5 + untouched Bomb/BOMB contract."""
from pathlib import Path
import hashlib, sys
if len(sys.argv) != 4:
    raise SystemExit("usage: stage24350_pack2_bomb_contract.py <build.ps1> <stage24.cpp> <scripts-dir>")
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
expected=[('2-1','Level52'),('2-2','Level34'),('2-3','Level42'),('2-4','Level24'),('2-5','Level88')]
errors=[]
print('ANGRY_STAGE24_35_0_PACK2_BOMB_CONTRACT 1')
print('mapping_source=untouched levelSelectionPagesBasic + levelOrder.pack2 runtime tables captured by Stage24.28.0')
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
checks={
    'pack2_asset_dir':"$assetsLevelPack2 = Join-Path $assetsStage 'data\\levels\\pack2'" in build,
    'theme2_parallax_meta':"'INGAME_PARALLAX_2.dat'" in build,
    'theme2_parallax_texture':"'INGAME_PARALLAX_2.pvr'" in build,
    'pack2_map_observer':'[stage24.35.0-pack2] MAP_SUMMARY' in cpp,
    'pack2_map_range':'levelIndex >= 22 && levelIndex <= 26' in cpp,
    'pack2_expected_sequence':'Level52,Level34,Level42,Level24,Level88' in cpp,
    'pack2_exact_folder':'data/levels/pack2/' in cpp,
    'pack2_next_probe':'stage24.35.0-pack2-chain' in cpp,
    'stock_specialty_observer':'[stage24.32.1-specialty] STATE' in cpp,
    'no_native_bomb_sprite_case':'BIRD_BLACK' not in cpp,
    'no_native_make_explosion':'makeExplosion' not in cpp,
    'no_native_bomb_specialty_assignment':'birdSpecialty = "BOMB"' not in cpp and "birdSpecialty='BOMB'" not in cpp,
}
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')
    if not v: errors.append(k)
for tok in ('birdSpecialtyAvailable','birdSpecialty','specialty','BOMB','makeExplosion','removeBird','specialSound','special_explosion'):
    ok=tok in joined
    print(f'ORIGINAL_GAMELOGIC_TOKEN token={tok!r} present={"PASS" if ok else "FAIL"}')
    if not ok: errors.append('gamelogic token '+tok)
print(f'ORIGINAL_GAMELOGIC sha256={hashlib.sha256(raw).hexdigest()} bytes={len(raw)} copied_into_project=NO')
print('bomb_runtime_authority=untouched updateGame BOMB branch -> makeExplosion/removeBird')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
