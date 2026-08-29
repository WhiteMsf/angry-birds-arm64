#!/usr/bin/env python3
"""Stage 24.45.1: Danger Above page/theme8 exact transport + untouched completion ownership."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    print('usage: stage24451_danger_above_theme8_contract.py <build.ps1> <stage24_live_surface.cpp>')
    raise SystemExit(2)

build=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
levels=[
('8-1', 'LevelP3_297'),('8-2', 'LevelP3_221'),('8-3', 'LevelP3_306'),('8-4', 'LevelP3_301'),('8-5', 'LevelP3_312'),('8-6', 'LevelP3_309'),('8-7', 'LevelP3_168'),('8-8', 'LevelP3_311'),('8-9', 'LevelP3_308'),('8-10', 'LevelP3_310'),('8-11', 'LevelP3_217'),('8-12', 'LevelP3_307'),('8-13', 'LevelP3_296'),('8-14', 'LevelP3_149'),('8-15', 'LevelP3_313')]
seq=','.join(x for _,x in levels)
checks={}
for human, phys in levels:
    var=f"$level{phys.replace('Level','')}p8"
    checks[f'transport_{human}']=(f"levels\\pack8\\{phys}.lua" in build and
                                  f"Copy-Item {var}" in build and
                                  f'{{"stage24/data/levels/pack8/{phys}.lua", "data/levels/pack8/{phys}.lua"}}' in cpp)
checks.update({
 'pack8_map_observer':'stage24451_dump_pack8_map' in cpp and '[stage24.45.1-danger] MAP_SUMMARY' in cpp,
 'pack8_sequence':seq in cpp,
 'pack8_folder':'data/levels/pack8/' in cpp,
 'pack8_context':'themeIndex == 8 && pageIndex == 3' in cpp and 'worldNumber != 8' in cpp,
 'pack8_page_range':'pageLevelIndex >= 1 && pageLevelIndex <= 15' in cpp,
 'skies2_retained':"'INGAME_SKIES_2.dat'" in build and '"INGAME_SKIES_2.dat"' in cpp,
 'parallax8_meta':"'INGAME_PARALLAX_8.dat'" in build and '"INGAME_PARALLAX_8.dat"' in cpp,
 'parallax8_texture':"'INGAME_PARALLAX_8.pvr'" in build,
 'ground8_transport':'INGAME_THEME_GROUND_8.pvr' in build and 'themeGround8' in cpp,
 'ground8_source_gate':'Required original theme8 MaskedImage fill texture not found' in build,
 'ground8_upload':'uploadTerrainFill(themeGround8, "INGAME_THEME_GROUND_8")' in cpp,
 'ground8_generic_selector':'fillName == "INGAME_THEME_GROUND_8"' in cpp and 'fillAtlas = &themeGround8' in cpp,
 'stock_completion_retained':'theme8Completed = true' not in cpp and 'theme8Completed=true' not in cpp,
 'no_level_specific_hacks':all(f'if ({phys}' not in cpp for _,phys in levels),
 'theme7_closure_retained':'stage24450_dump_pack7_map' in cpp and 'INGAME_THEME_GROUND_7' in cpp,
 'existing_level_limit_consumer_retained':'FROZEN_WRITE' in cpp and 'reasonMaxX' in cpp,
 'existing_setgameon_android_closure_retained':'ORIGINAL_ANDROID_NOOP' in cpp,
})
failed=[k for k,v in checks.items() if not v]
print('ANGRY_STAGE24_45_1_DANGER_ABOVE_THEME8_CONTRACT 1')
print('map=' + ','.join(f'{h}:{p}' for h,p in levels))
print('scene=INGAME_SKIES_2+INGAME_PARALLAX_8+INGAME_GROUNDS_1')
print('terrain=INGAME_THEME_GROUND_8')
print('progression=UNTOUCHED_LUA_OWNER')
print('boundary=DANGER_ABOVE_PAGE3_FINAL')
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
print('verdict=' + ('PASS' if not failed else 'FAIL'))
if failed:
    print('failed=' + ','.join(failed))
    raise SystemExit(3)
