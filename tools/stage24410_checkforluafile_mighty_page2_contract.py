#!/usr/bin/env python3
"""Stage 24.41.0: generic checkForLuaFile restoration + Mighty Hoax page2/theme5."""
from pathlib import Path
import re, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: stage24410_checkforluafile_mighty_page2_contract.py <build.ps1> <stage24.cpp>")

build = Path(sys.argv[1]).read_text(encoding="utf-8-sig", errors="replace")
cpp = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")
errors = []

print("ANGRY_STAGE24_41_0_CHECKFORLUAFILE_MIGHTY_PAGE2_CONTRACT 1")
print("authority=untouched hasLevelPack2/prepareMenuPage owns episode-card appStore/score visibility; native checkForLuaFile is read-only existence only")

m = re.search(r"static int l_stage24310_checkForLuaFile\(lua_State\* L\) \{(.*?)\n\}", cpp, re.S)
fn = m.group(1) if m else ""
checks = {
    "checklua_function_found": bool(m),
    "checklua_uses_generic_resolver": "stage24128_resolve_lua_resource_path(logical)" in fn,
    "checklua_regular_file_query": "stage24128_regular_file_exists(resolved)" in fn,
    "checklua_returns_boolean": "lua_pushboolean" in fn and "return 1;" in fn,
    "checklua_no_nil_stub": "AUDIT_PRESERVE_NIL_STUB" not in fn,
    "checklua_read_only": all(tok not in fn for tok in ("std::ofstream", "mkdir(", "remove(", "unlink(", "rename(")),
    "checklua_no_episode_specific_branch": all(tok not in fn for tok in ("episodeSelectionPage", "Mighty Hoax", "AVAILABLE_ON_APP_STORE", "gotoOviStore")),
    "stock_binding_retained": 'setfn(L, "checkForLuaFile", l_stage24310_checkForLuaFile);' in cpp,
}
for k,v in checks.items():
    print(f"CHECK {k}={'PASS' if v else 'FAIL'}")
    if not v: errors.append(k)

levels = [
    ("5-1","LevelP2_78"),("5-2","LevelP2_100"),("5-3","LevelP2_92"),("5-4","LevelP2_94"),("5-5","LevelP2_89"),
    ("5-6","LevelP2_73"),("5-7","LevelP2_76"),("5-8","LevelP2_122"),("5-9","LevelP2_99"),("5-10","LevelP2_84"),
]
for human, phys in levels:
    var = "$level" + phys.replace("Level","") + "p5"
    ok = (
        var in build and
        f"levels\\pack5\\{phys}.lua" in build and
        f"'{phys}.lua') -Force" in build and
        f'{{"stage24/data/levels/pack5/{phys}.lua", "data/levels/pack5/{phys}.lua"}}' in cpp
    )
    print(f"LEVEL human={human} physical={phys} transport={'PASS' if ok else 'FAIL'}")
    if not ok: errors.append(f"transport {human}={phys}")

scene_checks = {
    "pack5_directory": "$assetsLevelPack5 = Join-Path $assetsStage 'data\\levels\\pack5'" in build,
    "parallax5_meta_transport": "INGAME_PARALLAX_5.dat" in build,
    "parallax5_texture_transport": "INGAME_PARALLAX_5.pvr" in build,
    "parallax5_runtime_load": '"INGAME_PARALLAX_5.dat"' in cpp,
    "parallax5_runtime_extract": "stage24/scene-meta/INGAME_PARALLAX_5.dat" in cpp,
    "ground5_source": "INGAME_THEME_GROUND_5.pvr" in build,
    "ground5_runtime_extract": "stage24/INGAME_THEME_GROUND_5.pvr" in cpp,
    "ground5_parse": "stage24.41.0-mask] fill texture contract PASS logical=INGAME_THEME_GROUND_5" in cpp,
    "ground5_upload": 'uploadTerrainFill(themeGround5, "INGAME_THEME_GROUND_5")' in cpp,
    "ground5_select": 'fillName == "INGAME_THEME_GROUND_5"' in cpp and "fillAtlas = &themeGround5" in cpp,
    "pack5_map_observer": "[stage24.41.0-mighty] MAP_SUMMARY" in cpp,
    "pack5_map_range": "levelIndex >= 22 && levelIndex <= 31" in cpp,
    "pack5_folder": "data/levels/pack5/" in cpp,
    "pack5_context": "themeIndex != 5 || worldNumber != 5 || pageIndex != 2" in cpp,
    "pack5_exact_first10": "LevelP2_78,LevelP2_100,LevelP2_92,LevelP2_94,LevelP2_89,LevelP2_73,LevelP2_76,LevelP2_122,LevelP2_99,LevelP2_84" in cpp,
    "next_probe": "stage24.41.0-mighty-5-10-chain" in cpp,
    "no_direct_ovi_visual_fix": "AVAILABLE_ON_APP_STORE" not in fn,
    "no_forced_theme5_complete": "theme5Completed = true" not in cpp and "theme5Completed=true" not in cpp,
}
for k,v in scene_checks.items():
    print(f"CHECK {k}={'PASS' if v else 'FAIL'}")
    if not v: errors.append(k)

print("map=5-1:LevelP2_78,5-2:LevelP2_100,5-3:LevelP2_92,5-4:LevelP2_94,5-5:LevelP2_89,5-6:LevelP2_73,5-7:LevelP2_76,5-8:LevelP2_122,5-9:LevelP2_99,5-10:LevelP2_84")
print("context=folder=data/levels/pack5/ themeIndex=5 worldNumber=5 pageIndex=2")
print("theme5_scene=SKIES_1 + PARALLAX_5 + GROUNDS_1; terrain_fill=INGAME_THEME_GROUND_5")
print("RESULT=" + ("FAIL" if errors else "PASS"))
if errors:
    for e in errors:
        print("ERROR " + e)
    raise SystemExit(1)
