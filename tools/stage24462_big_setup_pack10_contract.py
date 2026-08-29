#!/usr/bin/env python3
"""Stage 24.46.2: The Big Setup page2/pack10 exact transport + ownership contract."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    print('usage: stage24462_big_setup_pack10_contract.py <build.ps1> <stage24_live_surface.cpp>')
    raise SystemExit(2)

build=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
levels=[
('10-1','LevelP4_442'),('10-2','LevelP4_443'),('10-3','LevelP4_444'),('10-4','LevelP4_445'),('10-5','LevelP4_448'),
('10-6','LevelP4_449'),('10-7','LevelP4_451'),('10-8','LevelP4_452'),('10-9','LevelP4_453'),('10-10','LevelP4_454'),
('10-11','LevelP4_455'),('10-12','LevelP4_457'),('10-13','LevelP4_458'),('10-14','LevelP4_459'),('10-15','LevelP4_462')]
seq=','.join(x for _,x in levels)
checks={}
for human, phys in levels:
    var=f"$level{phys.replace('Level','')}p10"
    checks[f'transport_{human}']=(f"levels\\pack10\\{phys}.lua" in build and
                                  f"Copy-Item {var}" in build and
                                  f'{{"stage24/data/levels/pack10/{phys}.lua", "data/levels/pack10/{phys}.lua"}}' in cpp)
checks.update({
 'pack10_map_observer':'stage24462_dump_pack10_map' in cpp and '[stage24.46.2-bigsetup] MAP_SUMMARY' in cpp,
 'pack10_sequence':seq in cpp,
 'pack10_folder':'data/levels/pack10/' in cpp,
 'pack10_context':'themeIndex == 10 && pageIndex == 2' in cpp and 'worldNumber != 10' in cpp,
 'pack10_page_range':'pageLevelIndex >= 1 && pageLevelIndex <= 15' in cpp,
 'generic_theme_parser_retained':'stage24153_parse_theme_scene' in cpp and 'setTheme: exact original scene contract unavailable' in cpp,
 'nonrepeat_armv7_branch_retained':'ARMV7_DRAWBACKGROUND_NONREPEAT' in cpp and 'NONREPEAT_DRAW' in cpp,
 'crane_discovery_sheet_retained':'INGAME_PARALLAX_CRANES.dat' in cpp,
 'stock_completion_retained':'theme10Completed = true' not in cpp and 'theme10Completed=true' not in cpp,
 'no_level_specific_hacks':all(f'if ({phys}' not in cpp for _,phys in levels),
 'pack9_closure_retained':'stage24460_dump_pack9_map' in cpp and 'theme9Completed = true' not in cpp,
 'existing_level_limit_consumer_retained':'FROZEN_WRITE' in cpp and 'reasonMaxX' in cpp,
 'existing_setgameon_android_closure_retained':'ORIGINAL_ANDROID_NOOP' in cpp,
})
failed=[k for k,v in checks.items() if not v]
print('ANGRY_STAGE24_46_2_BIG_SETUP_PACK10_CONTRACT 1')
print('map=' + ','.join(f'{h}:{p}' for h,p in levels))
print('context=levelSelectionPagesPack4/pack10/themeIndex10/world10/page2')
print('scenePolicy=UNTOUCHED_LEVEL_THEME + PROVEN_GENERIC_THEME_RENDERER')
print('progression=UNTOUCHED_LUA_OWNER')
print('boundary=THE_BIG_SETUP_PAGE2')
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
print('verdict=' + ('PASS' if not failed else 'FAIL'))
if failed:
    print('failed=' + ','.join(failed))
    raise SystemExit(3)
