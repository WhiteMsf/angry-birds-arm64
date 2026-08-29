#!/usr/bin/env python3
"""Stage 24.40.1 Mighty Hoax Pack4 page-1 expansion through 4-10."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    raise SystemExit("usage: stage24401_mighty_hoax_4_10_contract.py <build.ps1> <stage24.cpp>")
build=Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
expected=[('4-6','LevelP2_88'),('4-7','LevelP2_64'),('4-8','LevelP2_80'),('4-9','LevelP2_108'),('4-10','LevelP2_85')]
errors=[]
print('ANGRY_STAGE24_40_1_MIGHTY_HOAX_4_10_CONTRACT 1')
print('mapping_source=untouched levelOrder.pack4 runtime inventory retained from Stage24.28.0')
for human,phys in expected:
    var='$level'+phys.replace('Level','')+'p4'
    checks=[
        var in build,
        f"levels\\pack4\\{phys}.lua" in build,
        f"'{phys}.lua') -Force" in build,
        f'{{"stage24/data/levels/pack4/{phys}.lua", "data/levels/pack4/{phys}.lua"}}' in cpp,
    ]
    ok=all(checks)
    print(f'LEVEL human={human} physical={phys} transport={"PASS" if ok else "FAIL"}')
    if not ok: errors.append(f'transport {human}={phys}')
full='LevelP2_103,LevelP2_91,LevelP2_65,LevelP2_96,LevelP2_69,LevelP2_88,LevelP2_64,LevelP2_80,LevelP2_108,LevelP2_85'
checks={
    'pack4_map_observer':'[stage24.40.1-mighty] MAP_SUMMARY' in cpp,
    'pack4_map_range':'levelIndex >= 1 && levelIndex <= 10' in cpp,
    'pack4_expected_sequence':full in cpp,
    'pack4_exact_folder':'data/levels/pack4/' in cpp,
    'pack4_next_probe':'stage24.40.1-mighty-4-10-chain' in cpp,
    'polygon_contract_retained':'[stage24.40.0-polygon] CREATE' in cpp,
    'no_levelp2_88_special_case':'if (levelName == "LevelP2_88")' not in cpp and "if(levelName==\"LevelP2_88\")" not in cpp,
    'no_pack4_alias_copy':'LevelP2_69.lua", "data/levels/pack4/LevelP2_88.lua' not in cpp,
}
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')
    if not v: errors.append(k)
print('runtime_authority=untouched getNextLevel/loadLevelInternal')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
