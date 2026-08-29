#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: stage24311_real_persistence_contract.py <stage24_live_surface.cpp>')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8', errors='replace')

checks = {
    'real_binding': 'setfn(L, "saveLuaFile", l_stage24311_saveLuaFile);' in s,
    'app_private_dir': 'return gStage24Root + "/appdata";' in s,
    'settings_load': 'stage24311LoadNamedTable(L, "settings.lua", "settings")' in s,
    'highscores_load': 'stage24311LoadNamedTable(L, "highscores.lua", "highscores")' in s,
    'disk_marker': 'PASS_FROM_DISK' in s,
    'atomic_tmp': 'const std::string tmpPath = finalPath + ".tmp";' in s,
    'fsync_before_rename': '::fsync(::fileno(f))' in s and 'std::rename(tmpPath.c_str(), finalPath.c_str())' in s,
    'fresh_env_write_validation': 'stage24311ValidateEnvironmentChunk(L, tmpPath)' in s and 'PASS_FRESH_ENV' in s,
    'fresh_table_loader': 'exec_file_into_global_table_env(L, path, fileName, tableName)' in s,
    'identifier_top_level_guard': 'stage24311Identifier(key, keyLen)' in s,
    'non_appdata_not_redirected': 'NO_WRITE_UNEXERCISED_NON_APPDATA' in s,
}

try:
    load_pos = s.index('stage24311LoadProfile(L);')
    init_pos = s.index('// Stage 24.9 / 24.12.4:', load_pos)
    checks['profile_load_before_menu_audio_bootstrap'] = load_pos < init_pos
except ValueError:
    checks['profile_load_before_menu_audio_bootstrap'] = False

for k, v in checks.items():
    print(f'{k}={str(v).lower()}')
if not all(checks.values()):
    raise SystemExit('FAIL_STAGE24_31_1_REAL_PERSISTENCE_CONTRACT')
print('verdict=PASS_REAL_APPDATA_RESTART_PERSISTENCE_WIRING')
