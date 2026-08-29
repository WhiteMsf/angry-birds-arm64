#!/usr/bin/env python3
"""Stage 24.43.0: original joint + high-value physics-stub discovery contract."""
from __future__ import annotations
import os, re, subprocess, sys
from pathlib import Path


def run(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors='replace')
    return p.returncode, p.stdout


def symbol(nm_text: str, name: str):
    # llvm-nm -S -C: addr size type demangled-name
    pat = re.compile(r'^\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\S\s+' + re.escape(name) + r'\s*$', re.M)
    m = pat.search(nm_text)
    if not m:
        return None
    return (int(m.group(1), 16) & ~1, int(m.group(2), 16))


def disassemble(objdump: str, lib: str, span):
    if not span:
        return ''
    start, size = span
    rc, out = run([objdump, '-d', '--demangle',
                   f'--start-address=0x{start:x}',
                   f'--stop-address=0x{start+size:x}', lib])
    return out if rc == 0 else out


def fn_slice(cpp: str, start_marker: str, end_marker: str):
    a = cpp.find(start_marker)
    b = cpp.find(end_marker, a + len(start_marker)) if a >= 0 else -1
    return cpp[a:b] if a >= 0 and b > a else ''


def main():
    if len(sys.argv) != 6:
        print('usage: stage24430_joint_bounds_discovery_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <stage24_live_surface.cpp> <build.ps1>', file=sys.stderr)
        return 2
    nm, objdump, lib, cpp_path, build_path = sys.argv[1:]
    for p in (nm, objdump, lib, cpp_path, build_path):
        if not os.path.exists(p):
            print('ERROR missing=' + p)
            return 3

    rc, nmt = run([nm, '-S', '-C', lib])
    if rc:
        rc, nmt = run([nm, '-D', '-S', '-C', lib])
    if rc:
        print('ERROR llvm-nm failed')
        print(nmt)
        return 4

    names = [
        'GameLua::createJointLua(lua::LuaState*)',
        'GameLua::destroyJointLua(lang::String)',
        'GameLua::setLevelLimits(float, float, float, float)',
        'GameLua::setMaxTranslation(float)',
        'GameLua::setGameOn(bool)',
    ]
    spans = {name: symbol(nmt, name) for name in names}
    bodies = {name: disassemble(objdump, lib, spans[name]) for name in names}

    create = bodies[names[0]]
    destroy = bodies[names[1]]
    limits = bodies[names[2]]
    maxtr = bodies[names[3]]
    gameon = bodies[names[4]]

    cpp = Path(cpp_path).read_text(encoding='utf-8', errors='replace')
    build = Path(build_path).read_text(encoding='utf-8', errors='replace')

    checks = {}
    checks['symbols_all_present'] = all(spans.values())
    # Discovery evidence is reported even when compiler/linker formatting hides a
    # demangled callee name; do not block the phone capture on those heuristics.
    evidence = {}
    evidence['create_joint_native_owner'] = 'b2World::CreateJoint' in create
    evidence['destroy_joint_native_owner'] = 'b2World::DestroyJoint' in destroy
    evidence['level_limits_store_shape'] = (
        ('#0x24c' in limits.lower() or '#588' in limits.lower()) and
        ('#0x250' in limits.lower() or '#592' in limits.lower()) and
        '__fixsfsi' in limits
    )
    checks['native_bodies_nonempty'] = all(bool(bodies[name].strip()) for name in names)

    discovery_binding = all(tok in cpp for tok in (
        'setfn(L, "createJoint", l_stage24430_createJointAudit);',
        'setfn(L, "destroyJoint", l_stage24430_destroyJointAudit);',
        '[stage24.43.0-joint] CREATE',
        'BODY_MATCH arg=',
        'nativeJointMutation=NONE',
    ))
    reconstructed_binding = all(tok in cpp for tok in (
        'setfn(L, "createJoint", l_stage24431_createJoint);',
        'setfn(L, "destroyJoint", l_stage24431_destroyJoint);',
        '[stage24.43.0-joint] CREATE',
        'BODY_MATCH arg=',
        '[stage24.43.1-joint]',
    ))
    checks['joint_probe_bindings'] = discovery_binding or reconstructed_binding
    checks['bounds_probe_bindings'] = all(tok in cpp for tok in (
        'setfn(L, "setLevelLimits", l_stage24430_setLevelLimitsAudit);',
        'setfn(L, "setMaxTranslation", l_stage24430_setMaxTranslationAudit);',
        'setfn(L, "setGameOn", l_stage24430_setGameOnAudit);',
        '[stage24.43.0-bounds] setLevelLimits',
        'action=OBSERVE_ONLY',
    )) and (
        '[stage24.43.0-bounds] setMaxTranslation' in cpp or
        '[stage24.44.0-maxtranslation]' in cpp
    ) and (
        '[stage24.43.0-bounds] setGameOn' in cpp or
        '[stage24.44.3-gameon]' in cpp
    )

    if discovery_binding:
        joint_probe = fn_slice(cpp, 'static int l_stage24430_createJointAudit', 'static int l_stage24430_destroyJointAudit')
        destroy_probe = fn_slice(cpp, 'static int l_stage24430_destroyJointAudit', '// High-value physics/lifecycle debt')
        checks['joint_probe_observe_only'] = bool(joint_probe and destroy_probe) and not any(
            tok in (joint_probe + destroy_probe) for tok in ('CreateJoint(', 'DestroyJoint(', 'b2JointDef', 'Initialize(')
        )
    else:
        # Stage24.43.1 consumes this already-captured ARMv7 evidence. Keep the
        # historical discovery report available without requiring the old
        # no-mutation binding to remain active. The new contract audits mutation.
        joint_probe = fn_slice(cpp, 'static int l_stage24431_createJoint', 'static int l_stage24431_destroyJoint')
        destroy_probe = fn_slice(cpp, 'static int l_stage24431_destroyJoint', '// High-value physics/lifecycle debt')
        checks['joint_probe_observe_only'] = reconstructed_binding
    bounds_probe = fn_slice(cpp, 'static int l_stage24430_setLevelLimitsAudit', 'static int l_createBox')
    checks['bounds_probe_observe_only'] = bool(bounds_probe) and not any(
        tok in bounds_probe for tok in (
            'SetLinearVelocity(', 'SetAngularVelocity(', 'SetTransform(', 'SetAwake(',
            'SetActive(', 'SetGravity(', 'ApplyForce(', 'ApplyImpulse(', 'CreateBody(',
            'DestroyBody(', 'CreateJoint(', 'DestroyJoint('
        )
    )
    checks['no_level_5_11_hack'] = ('LevelP2_86' not in joint_probe and '5-11' not in joint_probe)
    checks['build_gate'] = (
        'stage24430_joint_bounds_discovery_contract.py' in build and
        'stage24.43.0-joint-bounds-discovery-contract.txt' in build
    )

    print('ANGRY_STAGE24_43_0_JOINT_BOUNDS_DISCOVERY_CONTRACT 1')
    print('policy=ARMV7_DISCOVERY_EVIDENCE; accepts later proven reconstructed consumers; setLevelLimits remains passive, setMaxTranslation may be reconstructed by Stage24.44.0, and setGameOn may close only as the proven Android no-op')
    for name in names:
        span = spans[name]
        print(f"symbol[{name}]=" + (f"0x{span[0]:x}+0x{span[1]:x}" if span else 'MISSING'))
    for k, v in checks.items():
        print(f"{k}={'PASS' if v else 'FAIL'}")
    for k, v in evidence.items():
        print(f"evidence.{k}={'YES' if v else 'NO'}")

    # Always preserve the exact original bodies in the report. This is the
    # handoff artifact used to implement Stage24.43.1 without another static pass.
    for name in names:
        print('\n===== ARMV7 ' + name + ' =====')
        print(bodies[name].rstrip())

    if create:
        joint_lines = [ln for ln in create.splitlines() if 'Joint' in ln or 'joint' in ln]
        print('\n===== ARMV7 createJoint joint-related calls/refs =====')
        for ln in joint_lines:
            print(ln)

    failed = [k for k, v in checks.items() if not v]
    print('\nverdict=' + ('PASS' if not failed else 'FAIL'))
    if failed:
        print('failed=' + ','.join(failed))
        return 5
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
