#!/usr/bin/env python3
"""Stage 24.47.0A: Golden Eggs data-root resource search reconstruction contract."""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    print("usage: stage24470a_golden_eggs_resource_root_contract.py <build.ps1> <cpp>")
    raise SystemExit(2)

build = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
cpp = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")

checks = {
    "golden_source_under_original_data_root": "$levelGE_7 = Join-Path $dataRoot 'levels\\goldeneggs1\\LevelGE_7.lua'" in build,
    "golden_apk_under_stage24_data_root": 'stage24/data/levels/goldeneggs1/LevelGE_7.lua' in cpp,
    "resolver_detects_data_relative_levels": 'logical.rfind("levels/", 0) == 0' in cpp,
    "resolver_searches_data_root": 'gStage24Root + "/data/" + logical' in cpp,
    "resolver_keeps_plain_root_candidate": 'candidates.push_back(gStage24Root + "/" + logical);' in cpp,
    "deterministic_missing_path_uses_data_root": 'if (dataRelativeLevel)' in cpp and 'return gStage24Root + "/data/" + logical +' in cpp,
    "no_levelge7_special_case": 'logical.find("LevelGE_7")' not in cpp and 'logical == "LevelGE_7"' not in cpp,
    "no_levelge_filename_special_case": 'logical.find("LevelGE_")' not in cpp and 'logical.rfind("LevelGE_", 0)' not in cpp,
    "golden_47_0_contract_retained": 'stage24470_dump_golden_eggs_map' in cpp,
}

print("ANGRY_STAGE24_47_0A_GOLDEN_EGGS_RESOURCE_ROOT_CONTRACT 1")
print("witness=untouched Golden Eggs folder levels/goldeneggs1/ + original physical data/levels/goldeneggs1/")
print("ownership=GENERIC_NATIVE_RESOURCE_SEARCH_ROOT_RECONSTRUCTION")
for k, v in checks.items():
    print(f"{k}={'PASS' if v else 'FAIL'}")
verdict = all(checks.values())
print(f"verdict={'PASS' if verdict else 'FAIL'}")
raise SystemExit(0 if verdict else 1)
