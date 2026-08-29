#!/usr/bin/env python3
"""Stage 24.36.1 Poached Eggs Pack2 page closure through 2-21."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    raise SystemExit("usage: stage24361_pack2_chapter2_closure_contract.py <build.ps1> <stage24.cpp>")
build=Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
expected=[
 ('2-15','Level66'),('2-16','Level85'),('2-17','Level27'),
 ('2-18','Level32'),('2-19','Level72'),('2-20','Level90'),('2-21','Level96')
]
errors=[]
print('ANGRY_STAGE24_36_1_PACK2_CHAPTER2_CLOSURE_CONTRACT 1')
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
full='Level52,Level34,Level42,Level24,Level88,Level36,Level31,Level21,Level41,Level76,Level38,Level35,Level20,Level26,Level66,Level85,Level27,Level32,Level72,Level90,Level96'
checks={
    'pack2_map_observer':'[stage24.36.1-chapter2] MAP_SUMMARY' in cpp,
    'pack2_map_range':'levelIndex >= 22 && levelIndex <= 42' in cpp,
    'pack2_expected_sequence':full in cpp,
    'pack2_exact_folder':'data/levels/pack2/' in cpp,
    'pack2_next_probe':'stage24.36.1-chapter2-chain' in cpp,
    'no_forced_theme2_complete':'theme2Completed = true' not in cpp and 'theme2Completed=true' not in cpp,
    'no_forced_level96_next':'if (levelName == "Level96")' not in cpp and "if(levelName==\"Level96\")" not in cpp,
    'no_level_copy_alias':'Level90.lua", "data/levels/pack2/Level96.lua' not in cpp,
}
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')
    if not v: errors.append(k)
print('chapter2_runtime_authority=untouched getNextLevel/theme2Complete/settings/save')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
