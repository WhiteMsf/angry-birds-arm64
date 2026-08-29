#!/usr/bin/env python3
"""Stage 24.42.0: Danger Above page-1/theme6 transport + Boomerang passive audit."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    print('usage: stage24420_danger_above_theme6_boomerang_contract.py <build.ps1> <stage24_live_surface.cpp>')
    raise SystemExit(2)

build=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')

levels=[
('6-1','LevelP3_212'),('6-2','LevelP3_134'),('6-3','LevelP3_162'),('6-4','LevelP3_271'),('6-5','LevelP3_224'),
('6-6','LevelP3_253'),('6-7','LevelP3_225'),('6-8','LevelP3_232'),('6-9','LevelP3_150'),('6-10','LevelP3_211'),
('6-11','LevelP3_223'),('6-12','LevelP3_226'),('6-13','LevelP3_215'),('6-14','LevelP3_220'),('6-15','LevelP3_231')]
seq=','.join(x for _,x in levels)
checks={}
for human, phys in levels:
    var=f"$level{phys.replace('Level','')}p6"
    checks[f'transport_{human}']=(f"levels\\pack6\\{phys}.lua" in build and
                                  f"Copy-Item {var}" in build and
                                  f'{{"stage24/data/levels/pack6/{phys}.lua", "data/levels/pack6/{phys}.lua"}}' in cpp)

checks.update({
 'pack6_map_observer':'stage24420_dump_pack6_map' in cpp and '[stage24.42.0-danger] MAP_SUMMARY' in cpp,
 'pack6_sequence':seq in cpp,
 'pack6_folder':'data/levels/pack6/' in cpp,
 'pack6_context':'themeIndex == 6 && pageIndex == 1' in cpp and 'worldNumber != 6' in cpp,
 'pack6_page_range':'pageLevelIndex >= 1 && pageLevelIndex <= 15' in cpp,
 'skies2_meta':"'INGAME_SKIES_2.dat'" in build and '"INGAME_SKIES_2.dat"' in cpp,
 'skies2_texture':"'INGAME_SKIES_2.pvr'" in build,
 'parallax6_meta':"'INGAME_PARALLAX_6.dat'" in build and '"INGAME_PARALLAX_6.dat"' in cpp,
 'parallax6_texture':"'INGAME_PARALLAX_6.pvr'" in build,
 'ground6_transport':'INGAME_THEME_GROUND_6.pvr' in build and 'themeGround6' in cpp,
 'ground6_upload':'uploadTerrainFill(themeGround6, "INGAME_THEME_GROUND_6")' in cpp,
 'ground6_generic_selector':'fillName == "INGAME_THEME_GROUND_6"' in cpp and 'fillAtlas = &themeGround6' in cpp,
 'boomerang_lua_owner_tokens':all(tok in cpp for tok in ['birdSpecialty', 'BOOMERANG', 'boomerangActive', 'boomerangXForce', 'boomerangYForce']),
 'boomerang_observer':'[stage24.42.0-boomerang] STATE' in cpp and 'action=OBSERVE_ONLY' in cpp,
 'generic_apply_force':'static int l_applyForce(lua_State* L)' in cpp and 'b->ApplyForce(force, point)' in cpp,
 'no_level_specific_branch':all(f'if ({phys}' not in cpp for _,phys in levels),
 'no_forced_boomerang_assignment':'birdSpecialty = "BOOMERANG"' not in cpp and "birdSpecialty='BOOMERANG'" not in cpp,
 'no_forced_theme6_complete':'theme6Completed = true' not in cpp and 'theme6Completed=true' not in cpp,
})

failed=[k for k,v in checks.items() if not v]
print('ANGRY_STAGE24_42_0_DANGER_ABOVE_THEME6_BOOMERANG_CONTRACT 1')
print('map=' + ','.join(f'{h}:{p}' for h,p in levels))
print('scene=INGAME_SKIES_2+INGAME_PARALLAX_6+INGAME_GROUNDS_1')
print('terrain=INGAME_THEME_GROUND_6')
print('specialty=BOOMERANG_LUA_OWNER_NATIVE_OBSERVER_ONLY')
for k,v in checks.items():
    print(f'{k}={"PASS" if v else "FAIL"}')
print('verdict=' + ('PASS' if not failed else 'FAIL'))
if failed:
    print('failed=' + ','.join(failed))
    raise SystemExit(3)
