#!/usr/bin/env python3
"""Stage24.47.5: cross-architecture floating-point contraction audit.

The ARMv7 oracle visibly routes scalar float multiply/add/subtract through
soft-float helper calls in the recovered Box2D paths.  That establishes
separate float-rounding boundaries.  The ARM64 reconstruction therefore builds
Box2D and the live bridge with -ffp-contract=off and this tool verifies that no
AArch64 fused multiply-add/subtract instructions survive in relevant physics
functions.
"""
from __future__ import annotations
import os,re,subprocess,sys
from pathlib import Path

def run(args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
    return p.returncode,p.stdout.splitlines()

def section(lines, rx):
    out=[]; active=False
    label_re=re.compile(r'^\s*[0-9a-fA-F]+\s+<(.+)>:\s*$')
    for ln in lines:
        m=label_re.match(ln)
        if m:
            active=bool(rx.search(m.group(1)))
            if active: out.append(ln)
            continue
        if active: out.append(ln)
    return out

def main():
    if len(sys.argv)!=6:
        print('usage: stage24475_fp_contraction_binary_audit.py <llvm-objdump> <armv7-lib> <arm64-so> <box2d-root> <cmakelists>',file=sys.stderr)
        return 2
    objdump,armv7,arm64,boxroot,cmake=sys.argv[1:]
    print('ANGRY_STAGE24_47_5_FP_CONTRACTION_BINARY_AUDIT 1')
    print('policy=NUMERICAL_FIDELITY; generic Box2D/live-bridge compiler policy, no level/material special case')
    for x in (objdump,armv7,arm64,boxroot,cmake):
        if not os.path.exists(x):
            print('ERROR missing='+x); return 3

    rc7,a7=run([objdump,'-d','--demangle',armv7])
    rc64,a64=run([objdump,'-d','--demangle',arm64])
    print(f'armv7ObjdumpExit={rc7} lines={len(a7)}')
    print(f'arm64ObjdumpExit={rc64} lines={len(a64)}')

    target_rx=re.compile(r'(b2DistanceJoint::|b2ContactSolver::|b2Island::Solve|b2World::Step|PhysicsBridge::stepFixed)')
    t7=section(a7,target_rx)
    t64=section(a64,target_rx)
    helper_rx=re.compile(r'(__mulsf3|__aeabi_fmul|__aeabi_fadd|__aeabi_fsub|__addsf3|__subsf3)')
    fused_rx=re.compile(r'\b(fmadd|fmsub|fnmadd|fnmsub)\b',re.I)
    helpers=[ln for ln in t7 if helper_rx.search(ln)]
    fused=[ln for ln in t64 if fused_rx.search(ln)]

    print('\n--- ARMV7_SEPARATE_FLOAT_ROUNDING_WITNESS ---')
    for ln in helpers[:120]: print(ln)
    print(f'helperCallLines={len(helpers)}')
    print('\n--- ARM64_FUSED_INSTRUCTION_SCAN_RELEVANT_PHYSICS ---')
    for ln in fused[:120]: print(ln)
    print(f'fusedInstructionLines={len(fused)}')

    ctext=Path(cmake).read_text(encoding='utf-8-sig',errors='replace')
    btext='\n'.join(Path(boxroot).rglob('b2DistanceJoint.cpp').__iter__().__next__().read_text(errors='replace').splitlines()) if list(Path(boxroot).rglob('b2DistanceJoint.cpp')) else ''
    checks={
        'armv7_objdump': rc7==0 and bool(a7),
        'arm64_objdump': rc64==0 and bool(a64),
        'armv7_relevant_physics_found': bool(t7),
        'arm64_relevant_physics_found': bool(t64),
        'armv7_separate_float_helpers_present': len(helpers)>0,
        'box2d_ffp_contract_off': 'target_compile_options(box2d212 PRIVATE' in ctext and '-ffp-contract=off' in ctext,
        'live_bridge_ffp_contract_off': 'target_compile_options(stage24_live_surface PRIVATE -ffp-contract=off)' in ctext,
        'arm64_no_fmadd_fmsub_in_relevant_physics': len(fused)==0,
        'pinned_distance_joint_source_present': bool(btext),
    }
    print('\n--- GATES ---')
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
    ok=all(checks.values())
    print('interpretation=if runtime changes materially with contraction disabled, preserve the oracle-compatible separate-rounding build policy; if not, continue to joint/island ordering without tuning recovered constants')
    print('verdict='+('PASS' if ok else 'FAIL'))
    return 0 if ok else 5

if __name__=='__main__':
    raise SystemExit(main())
