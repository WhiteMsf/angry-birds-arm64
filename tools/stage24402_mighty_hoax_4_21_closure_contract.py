#!/usr/bin/env python3
"""Stage 24.40.2 Mighty Hoax Pack4 page-1 closure through 4-21."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    raise SystemExit("usage: stage24402_mighty_hoax_4_21_closure_contract.py <build.ps1> <stage24.cpp>")
build=Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
expected=[('11','LevelP2_82'),('12','LevelP2_66'),('13','LevelP2_104'),('14','LevelP2_210'),('15','LevelP2_83'),('16','LevelP2_79'),('17','LevelP2_77'),('18','LevelP2_114'),('19','LevelP2_81'),('20','LevelP2_68'),('21','LevelP2_95')]
errors=[]
print('ANGRY_STAGE24_40_2_MIGHTY_HOAX_4_21_CLOSURE_CONTRACT 1')
print('mapping_source=untouched levelOrder.pack4 runtime inventory captured from Stage24.28.0/v0.26.127 stdout')
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
full='LevelP2_103,LevelP2_91,LevelP2_65,LevelP2_96,LevelP2_69,LevelP2_88,LevelP2_64,LevelP2_80,LevelP2_108,LevelP2_85,LevelP2_82,LevelP2_66,LevelP2_104,LevelP2_210,LevelP2_83,LevelP2_79,LevelP2_77,LevelP2_114,LevelP2_81,LevelP2_68,LevelP2_95'
checks={
    'pack4_full_map_observer':'[stage24.40.2-mighty] MAP_SUMMARY' in cpp,
    'pack4_map_range':'levelIndex >= 1 && levelIndex <= 21' in cpp,
    'pack4_full_expected_sequence':full in cpp,
    'pack4_exact_folder':'data/levels/pack4/' in cpp,
    'pack4_context_theme4':'themeIndex != 4 || worldNumber != 4 || pageIndex != 1' in cpp,
    'pack4_next_probe':'stage24.40.2-mighty-4-21-closure-chain' in cpp,
    'polygon_contract_retained':'[stage24.40.0-polygon] CREATE' in cpp,
    'no_forced_theme4_complete':'theme4Completed = true' not in cpp and 'theme4Completed=true' not in cpp,
    'no_forced_levelp2_95_next':'if (levelName == "LevelP2_95")' not in cpp and "if(levelName==\"LevelP2_95\")" not in cpp,
    'no_pack4_alias_copy':'LevelP2_85.lua", "data/levels/pack4/LevelP2_82.lua' not in cpp,
}
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')
    if not v: errors.append(k)
print('runtime_authority=untouched getNextLevel/loadLevelInternal/page-completion logic')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
