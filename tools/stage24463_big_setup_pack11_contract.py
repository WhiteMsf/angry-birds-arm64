#!/usr/bin/env python3
"""Stage 24.46.3: The Big Setup page3/pack11 exact transport + final chapter ownership contract."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    print('usage: stage24463_big_setup_pack11_contract.py <build.ps1> <stage24_live_surface.cpp>')
    raise SystemExit(2)

build=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
levels=[
('11-1', 'LevelP4_463'),('11-2', 'LevelP4_464'),('11-3', 'LevelP4_465'),('11-4', 'LevelP4_466'),('11-5', 'LevelP4_467'),('11-6', 'LevelP4_468'),('11-7', 'LevelP4_469'),('11-8', 'LevelP4_470'),('11-9', 'LevelP4_471'),('11-10', 'LevelP4_472'),('11-11', 'LevelP4_473'),('11-12', 'LevelP4_474'),('11-13', 'LevelP4_475'),('11-14', 'LevelP4_477'),('11-15', 'LevelP4_478')
]
seq=','.join(x for _,x in levels)
checks={}
for human, phys in levels:
    var=f"$level{phys.replace('Level','')}p11"
    checks[f'transport_{human}']=(f"levels\\pack11\\{phys}.lua" in build and
                                  f"Copy-Item {var}" in build and
                                  f'{{"stage24/data/levels/pack11/{phys}.lua", "data/levels/pack11/{phys}.lua"}}' in cpp)
checks.update({
 'pack11_map_observer':'stage24463_dump_pack11_map' in cpp and '[stage24.46.3-bigsetup] MAP_SUMMARY' in cpp,
 'pack11_sequence':seq in cpp,
 'pack11_folder':'data/levels/pack11/' in cpp,
 'pack11_context':'themeIndex == 11 && pageIndex == 3' in cpp and 'worldNumber != 11' in cpp,
 'pack11_page_range':'pageLevelIndex >= 1 && pageLevelIndex <= 15' in cpp,
 'pack11_asset_dir':'$assetsLevelPack11 = Join-Path $assetsStage \'data\\levels\\pack11\'' in build and '$assetsLevelPack11,$assetsMenuTextures' in build,
 'generic_theme_parser_retained':'stage24153_parse_theme_scene' in cpp and 'setTheme: exact original scene contract unavailable' in cpp,
 'nonrepeat_armv7_branch_retained':'ARMV7_DRAWBACKGROUND_NONREPEAT' in cpp and 'NONREPEAT_DRAW' in cpp,
 'crane_sheet_retained':'INGAME_PARALLAX_CRANES.dat' in cpp,
 'stock_theme_completion_retained':'theme11Completed = true' not in cpp and 'theme11Completed=true' not in cpp,
 'stock_episode_finish_retained':'gameFinishedLP4 =' not in cpp and 'gameFinishedLP4=' not in cpp,
 'no_level_specific_hacks':all(f'if ({phys}' not in cpp for _,phys in levels),
 'pack10_closure_retained':'stage24462_dump_pack10_map' in cpp and 'theme10Completed = true' not in cpp,
 'existing_level_limit_consumer_retained':'FROZEN_WRITE' in cpp and 'reasonMaxX' in cpp,
 'existing_setgameon_android_closure_retained':'ORIGINAL_ANDROID_NOOP' in cpp,
})
failed=[k for k,v in checks.items() if not v]
print('ANGRY_STAGE24_46_3_BIG_SETUP_PACK11_CONTRACT 1')
print('map=' + ','.join(f'{h}:{p}' for h,p in levels))
print('context=levelSelectionPagesPack4/pack11/themeIndex11/world11/page3')
print('scenePolicy=UNTOUCHED_LEVEL_THEME + PROVEN_GENERIC_THEME_RENDERER')
print('progression=UNTOUCHED_LUA_OWNER')
print('completion=UNTOUCHED_theme11Complete/gameFinishedLP4_OWNER')
print('boundary=THE_BIG_SETUP_FINAL_PAGE')
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
print('verdict=' + ('PASS' if not failed else 'FAIL'))
if failed:
    print('failed=' + ','.join(failed))
    raise SystemExit(3)
