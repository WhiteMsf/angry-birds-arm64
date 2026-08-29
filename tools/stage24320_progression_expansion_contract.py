#!/usr/bin/env python3
"""Stage 24.32.0 Pack1 progression expansion static contract.

This does not invent the 1-3 mapping. Runtime telemetry reads the authoritative
levelSelectionPagesBasic table. The static gate only ensures the implementation
transports Level53 and leaves next-level/unlock ownership in original Lua.
"""
import sys
import re
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: stage24320_progression_expansion_contract.py <build.ps1> <stage24_live_surface.cpp>')

build = Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp = Path(sys.argv[2]).read_text(encoding='utf-8-sig', errors='replace')

required_loop = re.search(
    r'foreach\s*\(\$required\s+in\s+@\((.*?)\)\s*\+\s*\$menuMetaFiles',
    build,
    re.S,
)
required_body = required_loop.group(1) if required_loop else ''

checks = {
    'level53BuildInput': "$level53 = Join-Path $dataRoot 'levels\\pack1\\Level53.lua'" in build,
    # Stage 24.32.1 legitimately widens the required-level list beyond Level53.
    # Check semantic membership instead of freezing the exact v0.26.109 array order.
    'level53RequiredPreflight': all(tok in required_body for tok in ('$scripts', '$level1', '$level57', '$level53', '$blocksDat')),
    'level53Packaged': "Copy-Item $level53 (Join-Path $assetsLevelPack1 'Level53.lua') -Force" in build,
    'level53Materialized': '{"stage24/data/levels/pack1/Level53.lua", "data/levels/pack1/Level53.lua"}' in cpp,
    'runtimeMapReader': 'stage24320_dump_progression_map' in cpp,
    'runtimeMapLevelIndex': 'stage2411_table_int_field(L, -1, "levelIndex"' in cpp,
    'runtimeMapFilename': 'stage2411_table_string_field(L, -1, "filename"' in cpp,
    'runtimeMapExpectedObservedSequence': (
        'byLevel[1] == "Level1" && byLevel[2] == "Level57" && byLevel[3] == "Level53"' in cpp
        or (re.search(r'const\s+char\*\s+expected\[[^]]+\]\s*=\s*\{.*?"Level1"\s*,\s*"Level57"\s*,\s*"Level53"', cpp, re.S) is not None
            and 'byLevel[i] != expected[i]' in cpp)
    ),
    'stockNextLevelProbe': (
        'stage24129_probe_next_level(L, "Level57", "stage24.32-progression-map")' in cpp
        or (re.search(r'stage24321ProgressionChain\[\].*?"Level57".*?stage24129_probe_next_level\(L,\s*stage24321From', cpp, re.S) is not None)
    ),
    'liveLevelObserver': '[stage24.32-progression] LEVEL_ACTIVE' in cpp,
    'scoreObserverRetained': '[stage24.31.5-score-passive]' in cpp,
}

# Anti-hack checks: the new stage may name the expected mapping in diagnostics,
# but must not assign levelName=Level53 or branch on Level57 in the transport.
anti = {
    'noForcedLevel53Global': 'lua_pushstring(L, "Level53"); lua_setglobal(L, "levelName")' not in cpp,
    'noForcedLevel57To53If': 'if (stage24320ActiveLevel == "Level57")' not in cpp and 'if (levelName == "Level57")' not in cpp,
    'noLevel53AliasCopy': "Copy-Item $level57 (Join-Path $assetsLevelPack1 'Level53.lua')" not in build,
}

print('ANGRY_STAGE24_32_0_PROGRESSION_EXPANSION_CONTRACT 1')
print('policy=TRANSPORT_ORIGINAL_LEVEL_ONLY; progression/unlock/save remains untouched Lua')
for k,v in checks.items():
    print(f'{k}={"PASS" if v else "FAIL"}')
for k,v in anti.items():
    print(f'{k}={"PASS" if v else "FAIL"}')

ok = all(checks.values()) and all(anti.values())
print('expectedRuntimeMap=1:Level1,2:Level57,3:Level53')
print('expectedNextLevelProbe=getNextLevel(Level57)->Level53')
print('VERDICT=' + ('PASS' if ok else 'FAIL'))
raise SystemExit(0 if ok else 2)
