#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) not in (3, 4):
    print('usage: stage24442_level_limit_frozen_contract.py <stage441-report> <cpp> [stage22-runtime-report]')
    raise SystemExit(2)

rep = Path(sys.argv[1]).read_text(errors='ignore')
cpp = Path(sys.argv[2]).read_text(errors='ignore')
stage22_path = Path(sys.argv[3]) if len(sys.argv) == 4 else None
lua = ''
stage22_present = bool(stage22_path and stage22_path.is_file())
if stage22_present:
    lua = stage22_path.read_text(errors='ignore')

checks=[]
def ck(name, cond):
    checks.append((name,bool(cond)))
    print(f'{name}={"PASS" if cond else "FAIL"}')

print('ANGRY_STAGE24_44_2_LEVEL_LIMIT_FROZEN_CONTRACT 2')
print('policy=clean-build-safe; Stage24.22.0 report is runtime-generated evidence and is optional before APK installation')
print('stage22RuntimeEvidence=' + ('PRESENT' if stage22_present else 'ABSENT_CLEAN_BUILD'))

ck('armv7_update_reads_minx', 'ldr\tr0, [r4, #0x24c]' in rep)
ck('armv7_update_reads_maxx', 'ldr\tr0, [r4, #0x250]' in rep)
ck('armv7_bounds_all_set_same_boolean', rep.count("LuaTable::setBoolean(char const*, bool)") >= 3 and '0x56564' in rep)
ck('armv7_hard_y20_literal', '0x41a00000' in rep or ('1090519040' in rep and '10485760' in rep))
ck('native_key_resolved_frozen', 'set_bool_field(L, "frozen", true)' in cpp)
ck('positive_mass_gate', 'body->GetMass() > 0.0f' in cpp)
ck('minx_exact_compare', 'renderX < (float)gStage24440LevelLimitMinX' in cpp)
ck('maxx_exact_compare', '(float)gStage24440LevelLimitMaxX < renderX' in cpp)
ck('y20_exact_compare', 'renderY > 20.0f' in cpp)

# Stage24.22.0's report is created by pull-stage24-live-log.ps1 after a device
# run, so a clean build cannot require it.  If an old report is present, retain
# the strong historical check; otherwise verify that the untouched-Lua evidence
# dumper/owners are still wired in source and allow the clean build to proceed.
if stage22_present:
    ck('lua_frozen_consumer_prior_runtime', "K[376]='frozen'" in lua and "K[349]='removeObject'" in lua)
else:
    ck('lua_consumer_evidence_dumper_retained', all(x in cpp for x in (
        'stage24220_dump_failure_contract',
        '"updateGame"',
        '"removeBird"',
        '[stage24.22.0-failure-lua]'
    )))
    print('lua_frozen_consumer_prior_runtime=SKIP_CLEAN_BUILD (report is generated only after live capture)')

start = cpp.find('// Stage 24.44.2: exact ARMv7 level-limit consumer reconstruction')
end = cpp.find('if (body->GetType() == b2_dynamicBody) {', start)
region = cpp[start:end] if start >= 0 and end > start else ''
ck('no_direct_body_enforcement', bool(region) and all(x not in region for x in (
    'DestroyBody(', 'SetActive(', 'SetAwake(', 'SetLinearVelocity(', 'SetTransform('
)))

print('verdict=' + ('PASS' if all(v for _,v in checks) else 'FAIL'))
raise SystemExit(0 if all(v for _,v in checks) else 6)
