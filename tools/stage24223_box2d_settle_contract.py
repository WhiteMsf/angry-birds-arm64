#!/usr/bin/env python3
"""Stage 24.22.3: untouched ARMv7 Box2D settling/contact-threshold audit.

Diagnostic only. Compares the Rovio binary's relevant Box2D solver/island bodies
with the pinned public 2.1.2 candidate source used by the port. It does not patch
physics or infer a compatibility value on its own.
"""
from __future__ import annotations
import os, re, subprocess, sys
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

def print_source_focus(path:Path|None, patterns:list[str], radius:int=5):
    if path is None:
        print('source=NOT_FOUND')
        return
    print(f'source={path}')
    lines=path.read_text(errors='replace').splitlines()
    wanted=set()
    for i,line in enumerate(lines):
        if any(re.search(p,line,re.I) for p in patterns):
            for j in range(max(0,i-radius), min(len(lines),i+radius+1)):
                wanted.add(j)
    last=-2
    for j in sorted(wanted):
        if j != last+1 and last >= 0:
            print('...')
        print(f'{j+1:05d}: {lines[j]}')
        last=j

TARGETS=[
    r'b2ContactSolver::InitializeVelocityConstraints\(',
    r'b2ContactSolver::SolveVelocityConstraints\(',
    r'b2Island::Solve\(',
    r'b2Body::SetAwake\(',
    r'b2World::Step\(',
]

def main():
    if len(sys.argv)!=5:
        print('usage: stage24223_box2d_settle_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <stock-box2d-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,stock=sys.argv[1:]
    print('ANGRY_STAGE24_22_3_BOX2D_SETTLE_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; no sleep/restitution/velocity/timer mutation')
    print('question=does the Rovio Box2D solver use settling thresholds/constants different from the pinned 2.1.2 candidate?')
    print('runtimeFinding=stale shot birds can enter a ~4-render-frame ground-contact limit cycle: incoming yVel about +1.198, then rebound/flight, preventing updateGame speed<0.05 removal timer')
    print(f'lib={lib}')
    print(f'stockBox2D={stock}')
    for p in (nm,objdump,lib,stock):
        if not os.path.exists(p):
            print(f'ERROR missing={p}')
            return 3

    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml:
        rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')
    print()
    print('--- ARMV7_RELEVANT_SYMBOLS ---')
    matched=[]
    for s in syms:
        if s.typ not in 'TtWw':
            continue
        if any(re.search(p,s.name) for p in TARGETS):
            matched.append(s)
            print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not matched:
        print('NO_MATCHING_SOLVER_SYMBOLS')

    seen=set()
    for s in matched:
        start=s.addr & ~1
        if start in seen: continue
        seen.add(start)
        size=s.size or 0x1800
        stop=start+size
        print()
        print(f'--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body:
            print(line)

    root=Path(stock)
    print()
    print('--- PINNED_2_1_2_SETTINGS_SOURCE ---')
    print_source_focus(find_source(root,'b2Settings.h'), [
        r'velocityThreshold', r'timeToSleep', r'linearSleepTolerance',
        r'angularSleepTolerance', r'contactBaumgarte', r'maxTranslation',
    ], radius=3)
    print()
    print('--- PINNED_2_1_2_CONTACT_SOLVER_SOURCE ---')
    print_source_focus(find_source(root,'b2ContactSolver.cpp'), [
        r'velocityThreshold', r'velocityBias', r'restitution', r'InitializeVelocityConstraints'
    ], radius=7)
    print()
    print('--- PINNED_2_1_2_ISLAND_SLEEP_SOURCE ---')
    print_source_focus(find_source(root,'b2Island.cpp'), [
        r'timeToSleep', r'linearSleepTolerance', r'angularSleepTolerance', r'SetAwake'
    ], radius=7)

    print()
    print('interpretationRule=do not change bird restitution, updateGame 0.05 removal gate, or sleep state until the ARMv7 solver/island constants are resolved from this report')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
