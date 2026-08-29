#!/usr/bin/env python3
"""Stage 24.46.0: The Big Setup page1/pack9 exact transport + Theme9 live discovery contract."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    print('usage: stage24460_big_setup_theme9_contract.py <build.ps1> <stage24_live_surface.cpp>')
    raise SystemExit(2)

build=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
levels=[
('9-1','LevelP4_421'),('9-2','LevelP4_423'),('9-3','LevelP4_424'),('9-4','LevelP4_425'),('9-5','LevelP4_426'),
('9-6','LevelP4_427'),('9-7','LevelP4_428'),('9-8','LevelP4_429'),('9-9','LevelP4_431'),('9-10','LevelP4_432'),
('9-11','LevelP4_433'),('9-12','LevelP4_436'),('9-13','LevelP4_439'),('9-14','LevelP4_440'),('9-15','LevelP4_441')]
seq=','.join(x for _,x in levels)
checks={}
for human, phys in levels:
    var=f"$level{phys.replace('Level','')}p9"
    checks[f'transport_{human}']=(f"levels\\pack9\\{phys}.lua" in build and
                                  f"Copy-Item {var}" in build and
                                  f'{{"stage24/data/levels/pack9/{phys}.lua", "data/levels/pack9/{phys}.lua"}}' in cpp)
checks.update({
 'pack9_map_observer':'stage24460_dump_pack9_map' in cpp and '[stage24.46.0-bigsetup] MAP_SUMMARY' in cpp,
 'pack9_sequence':seq in cpp,
 'pack9_folder':'data/levels/pack9/' in cpp,
 'pack9_context':'themeIndex == 9 && pageIndex == 1' in cpp and 'worldNumber != 9' in cpp,
 'pack9_page_range':'pageLevelIndex >= 1 && pageLevelIndex <= 15' in cpp,
 # This sheet exists in the untouched 1.4.2 asset inventory and has never been
 # transported by earlier stages. We stage it as discovery coverage only; the
 # live Theme9 table remains authoritative about whether/how it is consumed.
 'cranes_meta_discovery_transport':"'INGAME_PARALLAX_CRANES.dat'" in build and '"INGAME_PARALLAX_CRANES.dat"' in cpp,
 'cranes_texture_discovery_transport':"'INGAME_PARALLAX_CRANES.pvr'" in build,
 'generic_theme_parser_retained':'stage24153_parse_theme_scene' in cpp and 'setTheme: exact original scene contract unavailable' in cpp,
 'theme9_scene_not_hardcoded':'INGAME_PARALLAX_CRANES' not in cpp[cpp.find('static int l_stage24152_setTheme_audit'):cpp.find('// Stage 24.13.1')],
 'stock_completion_retained':'theme9Completed = true' not in cpp and 'theme9Completed=true' not in cpp,
 'no_level_specific_hacks':all(f'if ({phys}' not in cpp for _,phys in levels),
 'theme8_closure_retained':'stage24451_dump_pack8_map' in cpp and 'theme8Completed' not in cpp,
 'existing_level_limit_consumer_retained':'FROZEN_WRITE' in cpp and 'reasonMaxX' in cpp,
 'existing_setgameon_android_closure_retained':'ORIGINAL_ANDROID_NOOP' in cpp,
})
failed=[k for k,v in checks.items() if not v]
print('ANGRY_STAGE24_46_0_BIG_SETUP_THEME9_CONTRACT 1')
print('map=' + ','.join(f'{h}:{p}' for h,p in levels))
print('context=levelSelectionPagesPack4/pack9/themeIndex9/world9/page1')
print('scenePolicy=LIVE_ORIGINAL_THEME9_TABLE_AUTHORITATIVE')
print('discoveryAsset=INGAME_PARALLAX_CRANES(.dat/.pvr)')
print('progression=UNTOUCHED_LUA_OWNER')
print('boundary=THE_BIG_SETUP_PAGE1')
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
print('verdict=' + ('PASS' if not failed else 'FAIL'))
if failed:
    print('failed=' + ','.join(failed))
    raise SystemExit(3)
