#!/usr/bin/env python3
"""Stage 24.35.1: theme2 scene metadata bootstrap/extraction closure."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    raise SystemExit("usage: stage24351_theme2_scene_metadata_contract.py <build.ps1> <stage24.cpp>")
build=Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp=Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')
errors=[]
checks={
    'build_stages_parallax2_meta': "'INGAME_PARALLAX_2.dat'" in build and '$themeSceneMetaNames' in build,
    'build_stages_parallax2_texture': "'INGAME_PARALLAX_2.pvr'" in build and '$themeSceneTextureNames' in build,
    'runtime_metadata_loader_includes_parallax2': all(x in cpp for x in ['"INGAME_PARALLAX_1.dat"','"INGAME_PARALLAX_2.dat"','"INGAME_GROUNDS_1.dat"']),
    'android_asset_extraction_includes_parallax2': '{"stage24/scene-meta/INGAME_PARALLAX_2.dat", "scene-meta/INGAME_PARALLAX_2.dat"}' in cpp,
    'theme2_contract_still_uses_parallax2': "INGAME_PARALLAX_2" in cpp,
}
print('ANGRY_STAGE24_35_1_THEME2_SCENE_METADATA_CONTRACT 1')
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')
    if not v: errors.append(k)
print('cause=v0.26.115 transported/uploaded INGAME_PARALLAX_2 PVR and APK DAT but omitted DAT from native extraction + SpriteDB bootstrap lists')
print('fix=register original INGAME_PARALLAX_2.dat through same generic scene metadata path as skies/parallax1/grounds')
print('runtime_behavior_change=scene metadata availability only; no Level52/theme2 layer values/render math/physics/progression/Bomb changes')
print('RESULT='+('FAIL' if errors else 'PASS'))
if errors:
    for e in errors: print('ERROR '+e)
    raise SystemExit(1)
