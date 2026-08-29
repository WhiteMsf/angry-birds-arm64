#!/usr/bin/env python3
"""Stage 24.39.0: Mighty Hoax 4-1..4-5 transport + Theme4 generic renderer contract."""
import sys
from pathlib import Path
if len(sys.argv) != 3:
    print('usage: stage24390_mighty_hoax_theme4_contract.py <build.ps1> <stage24_live_surface.cpp>')
    raise SystemExit(2)
build = Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp = Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
levels = [('4-1','LevelP2_103'),('4-2','LevelP2_91'),('4-3','LevelP2_65'),('4-4','LevelP2_96'),('4-5','LevelP2_69')]
checks = {}
for human, lv in levels:
    checks[f'{human}_{lv}_source'] = f"levels\\pack4\\{lv}.lua" in build
    checks[f'{human}_{lv}_apk_stage'] = f"$assetsLevelPack4 '{lv}.lua'" in build
    checks[f'{human}_{lv}_runtime_extract'] = f'stage24/data/levels/pack4/{lv}.lua' in cpp and f'data/levels/pack4/{lv}.lua' in cpp
checks.update({
    'pack4_directory': "$assetsLevelPack4 = Join-Path $assetsStage 'data\\levels\\pack4'" in build,
    'parallax4_meta_transport': 'INGAME_PARALLAX_4.dat' in build,
    'parallax4_texture_transport': 'INGAME_PARALLAX_4.pvr' in build,
    'parallax4_runtime_meta_load': '"INGAME_PARALLAX_4.dat"' in cpp,
    'parallax4_runtime_extract': 'stage24/scene-meta/INGAME_PARALLAX_4.dat' in cpp,
    'theme4_ground_source': 'INGAME_THEME_GROUND_4.pvr' in build,
    'theme4_ground_stage': "INGAME_THEME_GROUND_4.pvr') -Force" in build,
    'theme4_ground_runtime_extract': 'stage24/INGAME_THEME_GROUND_4.pvr' in cpp,
    'theme4_ground_parse': 'stage24.39.0-mask] fill texture contract PASS logical=INGAME_THEME_GROUND_4' in cpp,
    'theme4_ground_upload': 'uploadTerrainFill(themeGround4, "INGAME_THEME_GROUND_4")' in cpp,
    'theme4_ground_select': 'fillName == "INGAME_THEME_GROUND_4"' in cpp and 'fillAtlas = &themeGround4' in cpp,
    'extra_map_observer': '[stage24.39.0-mighty] MAP_SUMMARY' in cpp and 'levelSelectionPagesExtra' in cpp,
    'map_exact_sequence': "expected='LevelP2_103,LevelP2_91,LevelP2_65,LevelP2_96,LevelP2_69'" in cpp,
    'context_exact': 'themeIndex != 4 || worldNumber != 4 || pageIndex != 1' in cpp,
    'next_probe': 'stage24.39.0-mighty-theme4-chain' in cpp,
    'no_level_specific_gameplay': all(f'if (levelName == "{lv}")' not in cpp and f'if(levelName=="{lv}")' not in cpp for _,lv in levels),
    'no_forced_theme4_complete': 'theme4Completed = true' not in cpp and 'theme4Completed=true' not in cpp,
    'no_pack4_alias_copy': 'LevelP2_103.lua", "data/levels/pack4/LevelP2_91.lua' not in cpp,
})
print('ANGRY_STAGE24_39_0_MIGHTY_HOAX_THEME4_CONTRACT 1')
print('map=4-1:LevelP2_103,4-2:LevelP2_91,4-3:LevelP2_65,4-4:LevelP2_96,4-5:LevelP2_69')
print('menu_source=untouched levelSelectionPagesExtra / levelOrder.pack4; folder=data/levels/pack4/; themeIndex=4 worldNumber=4 pageIndex=1')
print('theme4_scene=SKIES_1 + PARALLAX_4 + GROUNDS_1; terrain_fill=INGAME_THEME_GROUND_4')
print('authority=untouched Lua selection/progression/theme tables; native changes are original-asset transport + generic existing renderer consumers only')
failed=[]
for k,v in checks.items():
    print(f'{k}={"PASS" if v else "FAIL"}')
    if not v: failed.append(k)
if failed:
    print('verdict=FAIL missing=' + ','.join(failed))
    raise SystemExit(3)
print('verdict=PASS')
