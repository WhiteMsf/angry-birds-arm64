#!/usr/bin/env python3
"""Stage 24.47.0: Golden Eggs exact menu/map transport + ownership contract."""
import sys
from pathlib import Path

if len(sys.argv) != 3:
    print("usage: stage24470_golden_eggs_contract.py <build.ps1> <stage24_live_surface.cpp>")
    raise SystemExit(2)

build = Path(sys.argv[1]).read_text(encoding="utf-8-sig")
cpp = Path(sys.argv[2]).read_text(encoding="utf-8")

playable = [f"LevelGE_{i}" for i in range(1, 16)]
slot_sequence = [
    "LevelGE_4","LevelGE_3","LevelGE_2","SOUNDBOARD1","LevelGE_14",
    "LevelGE_15","RADIO","LevelGE_1","LevelGE_5","LevelGE_6",
    "LevelGE_7","KEYBOARD","LevelGE_8","LevelGE_9","LevelGE_10",
    "LevelGE_11","SEQUENCER","LevelGE_12","LevelGE_13",
]
order_sequence = [
    "LevelGE_4","LevelGE_3","LevelGE_2","LevelGE_1","LevelGE_5",
    "LevelGE_6","LevelGE_7","LevelGE_8","LevelGE_9","LevelGE_10",
    "LevelGE_11","LevelGE_12","LevelGE_13","LevelGE_14","LevelGE_15",
]

checks = {}
norm_cpp = "".join(cpp.split())
expected_slots_literal = 'constchar*expectedSlots[20]={"",' + ",".join(f'"{x}"' for x in slot_sequence) + '};'
expected_order_literal = 'constchar*expectedOrder[16]={"",' + ",".join(f'"{x}"' for x in order_sequence) + '};'
for name in playable:
    i = name.split("_")[-1]
    checks[f"transport_{name}"] = (
        f"$levelGE_{i} = Join-Path $dataRoot 'levels\\goldeneggs1\\{name}.lua'" in build
        and f"Copy-Item $levelGE_{i} (Join-Path $assetsLevelGoldenEggs1 '{name}.lua') -Force" in build
        and f'{{"stage24/data/levels/goldeneggs1/{name}.lua", "data/levels/goldeneggs1/{name}.lua"}}' in cpp
    )

checks.update({
    "golden_assets_dir": "$assetsLevelGoldenEggs1 = Join-Path $assetsStage 'data\\levels\\goldeneggs1'" in build,
    "golden_map_observer": "stage24470_dump_golden_eggs_map" in cpp and "[stage24.47.0-golden] MAP_SUMMARY" in cpp,
    "slot_sequence": expected_slots_literal in norm_cpp,
    "level_order": expected_order_literal in norm_cpp,
    "slot_count": "pageLevelIndex >= 1 && pageLevelIndex <= 19" in cpp,
    "gameplay_count": "expectedGameplay=15" in cpp,
    "soundboard_count": "expectedSoundboards=4" in cpp,
    "soundboard_owners": all(x in cpp for x in ("SOUNDBOARD1","RADIO","KEYBOARD","SEQUENCER")),
    "exact_folder": 'folder != "levels/goldeneggs1/"' in cpp,
    "untouched_unlock_owner": "settings.openGoldenEggLevels" in build and 'lua_setfield(L, -1, "openGoldenEggLevels"' not in cpp,
    "no_levelge2_hack": 'filename == "LevelGE_2"' not in cpp and 'levelName == "LevelGE_2"' not in cpp,
    "campaign_completion_retained": "stage24463_dump_pack11_map" in cpp,
    "nonrepeat_renderer_retained": "NONREPEAT_DRAW" in cpp,
})

print("ANGRY_STAGE24_47_0_GOLDEN_EGGS_CONTRACT 1")
print("page=levelSelectionPagesGoldenEggs[1]")
print("slots=19")
print("gameplay=15")
print("soundboards=SOUNDBOARD1,RADIO,KEYBOARD,SEQUENCER")
print("slotMap=" + ",".join(f"{i+1}:{v}" for i,v in enumerate(slot_sequence)))
print("levelOrder=" + ",".join(order_sequence))
print("folder=levels/goldeneggs1/")
print("unlock=UNTOUCHED_settings.openGoldenEggLevels_OWNER")
print("completion=UNTOUCHED_goldenEggStarAchieved/highscores_OWNER")
for key, ok in checks.items():
    print(f"{key}={'PASS' if ok else 'FAIL'}")

verdict = all(checks.values())
print(f"verdict={'PASS' if verdict else 'FAIL'}")
raise SystemExit(0 if verdict else 1)
