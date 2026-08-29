#!/usr/bin/env python3
"""Stage 24.45.0: Danger Above page/theme7 exact transport + untouched progression ownership."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    print('usage: stage24450_danger_above_theme7_contract.py <build.ps1> <stage24_live_surface.cpp>')
    raise SystemExit(2)

build=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
levels=[
('7-1','LevelP3_166'),('7-2','LevelP3_237'),('7-3','LevelP3_216'),('7-4','LevelP3_298'),('7-5','LevelP3_303'),
('7-6','LevelP3_214'),('7-7','LevelP3_159'),('7-8','LevelP3_164'),('7-9','LevelP3_299'),('7-10','LevelP3_302'),
('7-11','LevelP3_219'),('7-12','LevelP3_163'),('7-13','LevelP3_160'),('7-14','LevelP3_161'),('7-15','LevelP3_304')]
seq=','.join(x for _,x in levels)
checks={}
for human, phys in levels:
    var=f"$level{phys.replace('Level','')}p7"
    checks[f'transport_{human}']=(f"levels\\pack7\\{phys}.lua" in build and
                                  f"Copy-Item {var}" in build and
                                  f'{{"stage24/data/levels/pack7/{phys}.lua", "data/levels/pack7/{phys}.lua"}}' in cpp)
checks.update({
 'pack7_map_observer':'stage24450_dump_pack7_map' in cpp and '[stage24.45.0-danger] MAP_SUMMARY' in cpp,
 'pack7_sequence':seq in cpp,
 'pack7_folder':'data/levels/pack7/' in cpp,
 'pack7_context':'themeIndex == 7 && pageIndex == 2' in cpp and 'worldNumber != 7' in cpp,
 'pack7_page_range':'pageLevelIndex >= 1 && pageLevelIndex <= 15' in cpp,
 'skies2_retained':"'INGAME_SKIES_2.dat'" in build and '"INGAME_SKIES_2.dat"' in cpp,
 'parallax7_meta':"'INGAME_PARALLAX_7.dat'" in build and '"INGAME_PARALLAX_7.dat"' in cpp,
 'parallax7_texture':"'INGAME_PARALLAX_7.pvr'" in build,
 'ground7_transport':'INGAME_THEME_GROUND_7.pvr' in build and 'themeGround7' in cpp,
 'ground7_source_gate':'Required original theme7 MaskedImage fill texture not found' in build,
 'ground7_upload':'uploadTerrainFill(themeGround7, "INGAME_THEME_GROUND_7")' in cpp,
 'ground7_generic_selector':'fillName == "INGAME_THEME_GROUND_7"' in cpp and 'fillAtlas = &themeGround7' in cpp,
 'stock_completion_retained':'theme7Completed = true' not in cpp and 'theme7Completed=true' not in cpp,
 'no_level_specific_hacks':all(f'if ({phys}' not in cpp for _,phys in levels),
 'existing_level_limit_consumer_retained':'FROZEN_WRITE' in cpp and 'reasonMaxX' in cpp,
 'existing_setgameon_android_closure_retained':'ORIGINAL_ANDROID_NOOP' in cpp,
})
failed=[k for k,v in checks.items() if not v]
print('ANGRY_STAGE24_45_0_DANGER_ABOVE_THEME7_CONTRACT 1')
print('map=' + ','.join(f'{h}:{p}' for h,p in levels))
print('scene=INGAME_SKIES_2+INGAME_PARALLAX_7+INGAME_GROUNDS_1')
print('terrain=INGAME_THEME_GROUND_7')
print('progression=UNTOUCHED_LUA_OWNER')
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
print('verdict=' + ('PASS' if not failed else 'FAIL'))
if failed:
    print('failed=' + ','.join(failed))
    raise SystemExit(3)
