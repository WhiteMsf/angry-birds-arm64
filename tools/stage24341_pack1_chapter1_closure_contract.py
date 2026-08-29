#!/usr/bin/env python3
"""Stage 24.34.1 Pack1 human 1-21 chapter closure static contract."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    raise SystemExit("usage: stage24341_pack1_chapter1_closure_contract.py <build.ps1> <stage24.cpp>")
build=Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
expected=[
 ('1-17','Level17'),('1-18','Level14'),('1-19','Level16'),
 ('1-20','Level23'),('1-21','Level44')
]
errors=[]
print('ANGRY_STAGE24_34_1_PACK1_CHAPTER1_CLOSURE_CONTRACT 1')
print('mapping_source=untouched levelOrder.pack1 runtime table captured by Stage24.28.0')
for human,phys in expected:
    var=phys.lower()
    checks=[
        f"$level{phys[5:]}" in build,
        f"levels\\pack1\\{phys}.lua" in build,
        f"'{phys}.lua') -Force" in build,
        f'{{"stage24/data/levels/pack1/{phys}.lua", "data/levels/pack1/{phys}.lua"}}' in cpp,
    ]
    ok=all(checks)
    print(f'LEVEL human={human} physical={phys} transport={"PASS" if ok else "FAIL"}')
    if not ok: errors.append(f'transport {human}={phys}')
expected_seq='Level1,Level57,Level53,Level3,Level6,Level2,Level4,Level5,Level7,Level8,Level9,Level13,Level10,Level39,Level12,Level15,Level17,Level14,Level16,Level23,Level44'
checks={
 'map_range_21':'levelIndex >= 1 && levelIndex <= 21' in cpp,
 'map_array_22':'std::string byLevel[22]' in cpp,
 'map_loop_21':'for (int i=1; i<=21; ++i)' in cpp,
 'map_expected_sequence':expected_seq in cpp,
 'active_level_observer':'[stage24.32-progression] LEVEL_ACTIVE' in cpp,
 'stock_next_claim':'Stock getNextLevel/unlock/save remains authoritative' in build,
 'no_level44_forced_assignment':('levelName = "Level44"' not in cpp and "levelName='Level44'" not in cpp),
}
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')
    if not v: errors.append(k)
print('runtime_authority=untouched getNextLevel + levelOrder.pack1 + unlock/highscore/save')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
