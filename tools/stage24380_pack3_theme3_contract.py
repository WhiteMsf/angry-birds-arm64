#!/usr/bin/env python3
"""Stage 24.38.0: Poached Eggs Pack3/theme3 3-1..3-5 transport + render-family contract."""
import sys
from pathlib import Path
if len(sys.argv) != 3:
    print('usage: stage24380_pack3_theme3_contract.py <build.ps1> <stage24_live_surface.cpp>')
    raise SystemExit(2)
build = Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp = Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
levels = [('3-1','Level43'),('3-2','Level77'),('3-3','Level28'),('3-4','Level29'),('3-5','Level87')]
checks = {}
for human, lv in levels:
    checks[f'{human}_{lv}_source'] = f"levels\\pack3\\{lv}.lua" in build
    checks[f'{human}_{lv}_apk_stage'] = f"$assetsLevelPack3 '{lv}.lua'" in build
    checks[f'{human}_{lv}_runtime_extract'] = f'stage24/data/levels/pack3/{lv}.lua' in cpp and f'data/levels/pack3/{lv}.lua' in cpp
checks.update({
    'pack3_directory': "$assetsLevelPack3 = Join-Path $assetsStage 'data\\levels\\pack3'" in build,
    'parallax3_meta_transport': 'INGAME_PARALLAX_3.dat' in build,
    'parallax3_texture_transport': 'INGAME_PARALLAX_3.pvr' in build,
    'parallax3_runtime_meta_load': '"INGAME_PARALLAX_3.dat"' in cpp,
    'parallax3_runtime_extract': 'stage24/scene-meta/INGAME_PARALLAX_3.dat' in cpp,
    'theme3_ground_source': 'INGAME_THEME_GROUND_3.pvr' in build,
    'theme3_ground_stage': "INGAME_THEME_GROUND_3.pvr') -Force" in build,
    'theme3_ground_runtime_extract': 'stage24/INGAME_THEME_GROUND_3.pvr' in cpp,
    'theme3_ground_parse': 'stage24.38.0-mask] fill texture contract PASS logical=INGAME_THEME_GROUND_3' in cpp,
    'theme3_ground_upload': 'uploadTerrainFill(themeGround3, "INGAME_THEME_GROUND_3")' in cpp,
    'theme3_ground_select': 'fillName == "INGAME_THEME_GROUND_3"' in cpp and 'fillAtlas = &themeGround3' in cpp,
    'map_observer': '[stage24.38.0-theme3] MAP_SUMMARY' in cpp,
    'map_exact_sequence': "expected='Level43,Level77,Level28,Level29,Level87'" in cpp,
    'next_probe': 'stage24.38.0-theme3-chain' in cpp,
    'no_level43_special_case': 'if (levelName == "Level43")' not in cpp and 'if(levelName=="Level43")' not in cpp,
    'no_forced_theme3': 'theme3Completed = true' not in cpp and 'theme3Completed=true' not in cpp,
    'no_pack3_alias_copy': 'Level43.lua", "data/levels/pack3/Level77.lua' not in cpp,
})
print('ANGRY_STAGE24_38_0_PACK3_THEME3_CONTRACT 1')
print('map=3-1:Level43,3-2:Level77,3-3:Level28,3-4:Level29,3-5:Level87')
print('theme3_scene=SKIES_1 + PARALLAX_3 + GROUNDS_1; terrain_fill=INGAME_THEME_GROUND_3')
print('authority=untouched levelOrder.pack3/getNextLevel/theme3/render metadata; native changes are transport + generic existing consumers only')
failed=[]
for k,v in checks.items():
    print(f'{k}={"PASS" if v else "FAIL"}')
    if not v: failed.append(k)
if failed:
    print('verdict=FAIL missing=' + ','.join(failed))
    raise SystemExit(3)
print('verdict=PASS')
