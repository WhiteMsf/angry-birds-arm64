#!/usr/bin/env python3
"""Stage 24.47.4: ARMv7 rubber warm-start / island-integration audit.

Read-only acquisition.  The previous stages closed the obvious rubber
restitution, contact normal-solver, distance-joint spring and fixed-timestep
branches.  This audit dumps the remaining Box2D paths that can materially
change the visible high-energy response without changing those constants:

* b2Contact::Update -- manifold ID matching / warm-start impulse carryover
* b2ContactSolver::FinalizeVelocityConstraints -- writes solved impulses back
* b2Island::Solve -- velocity integration, joint/contact ordering, linear and
  angular clamps, position solve
* b2Island::Report -- PostSolve callback timing
* b2World::Step -- step flags / island dispatch

No value is inferred or patched by this tool.
"""
from __future__ import annotations
import os, re, struct, subprocess, sys
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Sym:
    addr:int; size:int; typ:str; name:str

def run(args):
    p=subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     text=True, errors='replace')
    return p.returncode, p.stdout.splitlines()

def parse_nm(lines):
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    out=[]
    for line in lines:
        m=rx.match(line)
        if m:
            out.append(Sym(int(m.group(1),16), int(m.group(2),16), m.group(3), m.group(4)))
    return out

def find_source(root:Path, basename:str):
    hits=list(root.rglob(basename))
    return hits[0] if hits else None

def print_source_focus(path:Path|None, patterns:list[str], radius:int=8):
    if path is None:
        print('source=NOT_FOUND')
        return False
    print(f'source={path}')
    lines=path.read_text(errors='replace').splitlines()
    wanted=set()
    for i,line in enumerate(lines):
        if any(re.search(p,line,re.I) for p in patterns):
            for j in range(max(0,i-radius), min(len(lines),i+radius+1)):
                wanted.add(j)
    last=-2
    for j in sorted(wanted):
        if last >= 0 and j != last+1:
            print('...')
        print(f'{j+1:05d}: {lines[j]}')
        last=j
    return bool(wanted)

def decode_literals(lines):
    rx=re.compile(r'^\s*([0-9a-fA-F]+):.*?\.word\s+0x([0-9a-fA-F]{8})\s*$')
    found=False
    for line in lines:
        m=rx.match(line)
        if not m:
            continue
        found=True
        u=int(m.group(2),16)
        f=struct.unpack('<f', struct.pack('<I',u))[0]
        marker=''
        if f == f and abs(f) != float('inf') and 0.0 < abs(f) <= 256.0:
            marker=' candidateFloat=yes'
        print(f'0x{int(m.group(1),16):08x} word=0x{u:08x} float={f:.12g}{marker}')
    if not found:
        print('NO_LITERAL_WORDS_DECODED')

TARGETS={
    'contact_update': re.compile(r'b2Contact::Update\('),
    'circle_evaluate': re.compile(r'b2CircleContact::Evaluate\('),
    'finalize_velocity': re.compile(r'b2ContactSolver::FinalizeVelocityConstraints\('),
    'island_solve': re.compile(r'b2Island::Solve\('),
    'island_report': re.compile(r'b2Island::Report\('),
    'world_step': re.compile(r'b2World::Step\('),
}

REQUIRED=('contact_update','finalize_velocity','island_solve','island_report','world_step')

def main():
    if len(sys.argv)!=5:
        print('usage: stage24474_rubber_warmstart_integration_native_audit.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <box2d-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,boxroot=sys.argv[1:]
    print('ANGRY_STAGE24_47_4_RUBBER_WARMSTART_INTEGRATION_NATIVE_AUDIT 1')
    print('policy=DIAGNOSTIC_ONLY; no Box2D/Lua/gameplay mutation')
    print('question=after restitution/contact-normal/distance-joint/fixed-dt closure, do Rovio manifold warm-start carryover or island integration/clamps differ from pinned Box2D 2.1.2?')
    print('runtimeGoal=separate manifold impulses carried into a Step from impulses finalized by that Step and identify bodies hitting linear/angular integration caps')
    print(f'lib={lib}')
    print(f'box2dRoot={boxroot}')
    for x in (nm,objdump,lib,boxroot):
        if not os.path.exists(x):
            print(f'ERROR missing={x}')
            return 3

    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml:
        rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')
    found={k:[] for k in TARGETS}
    for s in syms:
        if s.typ not in 'TtWw':
            continue
        for key,rx in TARGETS.items():
            if rx.search(s.name):
                found[key].append(s)

    print('\n--- ARMV7_WARMSTART_INTEGRATION_SYMBOLS ---')
    for key in TARGETS:
        if not found[key]:
            print(f'{key}=NOT_FOUND')
        for s in found[key]:
            print(f'{key} {s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    all_body=[]
    seen=set()
    for key in TARGETS:
        for s in found[key]:
            start=s.addr & ~1
            if start in seen:
                continue
            seen.add(start)
            size=s.size or 0x1800
            stop=start+size
            print(f'\n--- ARMV7_BODY key={key} name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
            drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
            print(f'objdumpExit={drc} lines={len(body)}')
            all_body.extend(body)
            for line in body:
                print(line)
            print('--- DECODED_LITERAL_POOL ---')
            decode_literals(body)

    root=Path(boxroot)
    print('\n--- PINNED_2_1_2_CONTACT_UPDATE_SOURCE ---')
    contact_ok=print_source_focus(find_source(root,'b2Contact.cpp'), [
        r'void\s+b2Contact::Update', r'oldManifold', r'normalImpulse',
        r'tangentImpulse', r'IsEqual', r'Warm',
    ], 10)
    print('\n--- PINNED_2_1_2_CONTACT_FINALIZE_SOURCE ---')
    finalize_ok=print_source_focus(find_source(root,'b2ContactSolver.cpp'), [
        r'FinalizeVelocityConstraints', r'normalImpulse', r'tangentImpulse',
    ], 10)
    print('\n--- PINNED_2_1_2_ISLAND_INTEGRATION_SOURCE ---')
    island_ok=print_source_focus(find_source(root,'b2Island.cpp'), [
        r'void\s+b2Island::Solve', r'FinalizeVelocityConstraints', r'maxTranslation',
        r'maxRotation', r'SolvePositionConstraints', r'Report\(',
    ], 12)
    print('\n--- PINNED_2_1_2_WORLD_STEP_SOURCE ---')
    world_ok=print_source_focus(find_source(root,'b2World.cpp'), [
        r'void\s+b2World::Step', r'warmStarting', r'dtRatio', r'continuousPhysics',
    ], 10)
    print('\n--- PINNED_2_1_2_SETTINGS_CAPS ---')
    settings_ok=print_source_focus(find_source(root,'b2Settings.h'), [
        r'maxTranslation', r'maxRotation', r'velocityThreshold',
    ], 4)

    text='\n'.join(all_body)
    checks={
        **{f'armv7_{k}_found': bool(found[k]) for k in REQUIRED},
        'contact_source_found': contact_ok,
        'finalize_source_found': finalize_ok,
        'island_source_found': island_ok,
        'world_source_found': world_ok,
        'settings_caps_found': settings_ok,
        'armv7_float_compare_present': ('__aeabi_fcmpgt' in text or '__aeabi_fcmplt' in text),
        'armv7_float_multiply_present': '__mulsf3' in text,
    }
    print('\n--- ACQUISITION_GATES ---')
    for k,v in checks.items():
        print(f'{k}={"PASS" if v else "FAIL"}')
    ok=all(checks.values())
    print('interpretationRule=do not tune restitution=5.5, frequency=4, damping=.5, maxTranslation, maxRotation, or warm-start behavior until this report and Stage24.47.4 runtime witnesses are compared')
    print('verdict=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 5

if __name__=='__main__':
    raise SystemExit(main())
