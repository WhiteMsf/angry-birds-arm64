#!/usr/bin/env python3
"""Stage 24.38.1 Poached Eggs Pack3/page3 closure through 3-21."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    raise SystemExit("usage: stage24381_pack3_chapter3_closure_contract.py <build.ps1> <stage24.cpp>")
build=Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
expected=[
 ('3-6','Level18'),('3-7','Level91'),('3-8','Level49'),('3-9','Level45'),
 ('3-10','Level75'),('3-11','Level51'),('3-12','Level30'),('3-13','Level79'),
 ('3-14','Level40'),('3-15','Level59'),('3-16','Level58'),('3-17','Level95'),
 ('3-18','Level82'),('3-19','Level22'),('3-20','Level89'),('3-21','Level81')
]
errors=[]
print('ANGRY_STAGE24_38_1_PACK3_CHAPTER3_CLOSURE_CONTRACT 1')
print('mapping_source=untouched levelOrder.pack3 runtime table captured by Stage24.28.0/24.38.0 diagnostics')
for human,phys in expected:
    stem=phys[5:]
    checks=[
        f"$level{stem}p3" in build,
        f"levels\\pack3\\{phys}.lua" in build,
        f"'{phys}.lua') -Force" in build,
        f'{{"stage24/data/levels/pack3/{phys}.lua", "data/levels/pack3/{phys}.lua"}}' in cpp,
    ]
    ok=all(checks)
    print(f'LEVEL human={human} physical={phys} transport={"PASS" if ok else "FAIL"}')
    if not ok: errors.append(f'transport {human}={phys}')
full='Level43,Level77,Level28,Level29,Level87,Level18,Level91,Level49,Level45,Level75,Level51,Level30,Level79,Level40,Level59,Level58,Level95,Level82,Level22,Level89,Level81'
checks={
    'pack3_map_observer':'[stage24.38.1-chapter3] MAP_SUMMARY' in cpp,
    'pack3_map_range':'levelIndex >= 43 && levelIndex <= 63' in cpp,
    'pack3_expected_sequence':full in cpp,
    'pack3_exact_folder':'data/levels/pack3/' in cpp,
    'pack3_context_guard':'themeIndex != 3 || worldNumber != 3 || pageIndex != 3' in cpp,
    'pack3_next_probe':'stage24.38.1-chapter3-chain' in cpp,
    'no_forced_theme3_complete':'theme3Completed = true' not in cpp and 'theme3Completed=true' not in cpp,
    'no_forced_level81_next':'if (levelName == "Level81")' not in cpp and 'if(levelName=="Level81")' not in cpp,
}
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')
    if not v: errors.append(k)
print('chapter3_runtime_authority=untouched getNextLevel/theme3Complete/settings/save')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
