#!/usr/bin/env python3
"""Stage 24.38.2 regression contract for startup handoff vs levelFailed menu table.

The live Pack3 stress run exposed a long-latent Stage24.29.0 regression: the
startup handoff assigned `levelFailed = false`, but untouched initializeMenu()
owns `levelFailed` as the failure-menu page table.  Original failure state is
tracked by levelFailedTimer.  This contract rejects any boot-time overwrite of
the menu table and keeps terminal failure/menu ownership in untouched Lua.
"""
from pathlib import Path
import re, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: stage24382_level_failed_menu_boot_regression_contract.py <build.ps1> <stage24.cpp>")
build = Path(sys.argv[1]).read_text(encoding='utf-8-sig', errors='replace')
cpp = Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace')

print('ANGRY_STAGE24_38_2_LEVEL_FAILED_MENU_BOOT_REGRESSION_CONTRACT 1')
print('runtimeTrigger=Pack3 Level22 terminal failure after prolonged Stage24.38.1 stress run')
print('observedFault=attempt to index global levelFailed (a boolean value)')
print('originalOwnership=initializeMenu owns levelFailed page table; initLevelFailed owns levelFailedTimer')

# Isolate only the boot handoff raw Lua literal so unrelated historical text
# cannot accidentally satisfy/reject the contract.
needle='static bool stage24290FinishBoot(lua_State* L)'
pos=cpp.find(needle)
end=cpp.find('static bool stage24290AdvanceBoot', pos)
boot=cpp[pos:end] if pos >= 0 and end > pos else ''

checks={
    'bootFunctionFound': bool(boot),
    'mainMenuHandoffRetained': 'newMenuPage = mainMenu' in boot and 'setGameMode(updateMenu)' in boot,
    'levelCompletedResetRetained': 'levelCompleted = false' in boot,
    'badLevelFailedBooleanAssignmentRemoved': not re.search(r'\blevelFailed\s*=\s*(?:false|true|nil)\b', boot),
    'failureStateTimerDocumented': 'levelFailedTimer' in boot,
    'menuBootstrapStillAuditsLevelFailedTable': 'nested_table_count(L, "levelFailed", "items")' in cpp,
    'terminalMenuVisibilityRetained': 'page == "levelComplete" || page == "levelFailed"' in cpp,
    'noSyntheticFailureState': 'set_global' not in boot and 'lua_setglobal' not in boot,
    'pack3ClosureStillPresent': 'stage24.38.1-chapter3-chain' in cpp and 'Level81' in cpp,
}
for k,v in checks.items():
    print(f'CHECK {k}={"PASS" if v else "FAIL"}')

# Guard against "fixing" the symptom by turning the page into a C++ table or
# by suppressing the terminal branch.  We only remove the corrupting handoff.
anti_hacks={
    'noLevel22SpecialCase': 'if (levelName == "Level22")' not in cpp and 'if(levelName=="Level22")' not in cpp,
    'noForcedLevelFailedPage': 'newMenuPage = levelFailed' not in boot,
    'noFailureTimerOverride': not re.search(r'levelFailedTimer\s*=\s*0', boot),
}
for k,v in anti_hacks.items():
    print(f'ANTI_HACK {k}={"PASS" if v else "FAIL"}')

ok=all(checks.values()) and all(anti_hacks.values())
print('RESULT='+('PASS' if ok else 'FAIL'))
raise SystemExit(0 if ok else 3)
