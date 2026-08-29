#!/usr/bin/env python3
"""Stage 24.47.2: ARMv7 b2DistanceJoint spring-solver acquisition audit.

Read-only. Dumps the original Rovio ARMv7 distance-joint constructor and the
three solver methods beside the pinned Box2D 2.1.2 source used by the port.
No compatibility constant is inferred or patched by this tool.
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

def dump_source(path:Path|None):
    if path is None:
        print('source=NOT_FOUND')
        return False
    print(f'source={path}')
    for i,line in enumerate(path.read_text(errors='replace').splitlines(),1):
        if 45 <= i <= 176:
            print(f'{i:05d}: {line}')
    return True

def decode_literals(lines):
    # llvm-objdump may print literal pools as .word. Decode plausible floats;
    # this is evidence only, not an automatic semantic conclusion.
    rx=re.compile(r'^\s*([0-9a-fA-F]+):.*?\.word\s+0x([0-9a-fA-F]{8})\s*$')
    any_found=False
    for line in lines:
        m=rx.match(line)
        if not m:
            continue
        any_found=True
        u=int(m.group(2),16)
        f=struct.unpack('<f', struct.pack('<I',u))[0]
        marker=''
        if f == f and abs(f) != float('inf') and 0.0 < abs(f) <= 128.0:
            marker=' candidateFloat=yes'
        print(f'0x{int(m.group(1),16):08x} word=0x{u:08x} float={f:.12g}{marker}')
    if not any_found:
        print('NO_LITERAL_WORDS_DECODED')

TARGETS={
    'ctor': re.compile(r'b2DistanceJoint::b2DistanceJoint\('),
    'init': re.compile(r'b2DistanceJoint::InitVelocityConstraints\('),
    'solve_velocity': re.compile(r'b2DistanceJoint::SolveVelocityConstraints\('),
    'solve_position': re.compile(r'b2DistanceJoint::SolvePositionConstraints\('),
}

def main():
    if len(sys.argv)!=5:
        print('usage: stage24472_distance_joint_solver_native_audit.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <box2d-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,boxroot=sys.argv[1:]
    print('ANGRY_STAGE24_47_2_DISTANCE_JOINT_SOLVER_NATIVE_AUDIT 1')
    print('policy=DIAGNOSTIC_ONLY; compare untouched ARMv7 spring solver against pinned Box2D 2.1.2; no physics mutation')
    print('question=does Rovio b2DistanceJoint spring math/warm-start/position-correction differ from the pinned solver enough to explain the visibly softer rubber network?')
    print('focus=constructor + InitVelocityConstraints + SolveVelocityConstraints + SolvePositionConstraints')
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
    for sym in syms:
        if sym.typ not in 'TtWw':
            continue
        for key,rx in TARGETS.items():
            if rx.search(sym.name):
                found[key].append(sym)

    print('\n--- ARMV7_DISTANCE_JOINT_SYMBOLS ---')
    for key in TARGETS:
        if not found[key]:
            print(f'{key}=NOT_FOUND')
        for s in found[key]:
            print(f'{key} {s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    seen=set()
    for key in TARGETS:
        for sym in found[key]:
            start=sym.addr & ~1
            if start in seen:
                continue
            seen.add(start)
            size=sym.size or 0x1000
            stop=start+size
            print(f'\n--- ARMV7_BODY key={key} name={sym.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
            drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
            print(f'objdumpExit={drc} lines={len(body)}')
            for line in body:
                print(line)
            print('--- DECODED_LITERAL_POOL ---')
            decode_literals(body)

    src=find_source(Path(boxroot),'b2DistanceJoint.cpp')
    print('\n--- PINNED_2_1_2_DISTANCE_JOINT_SOURCE ---')
    source_ok=dump_source(src)

    checks={
        'armv7_ctor_found': bool(found['ctor']),
        'armv7_init_velocity_found': bool(found['init']),
        'armv7_solve_velocity_found': bool(found['solve_velocity']),
        'armv7_solve_position_found': bool(found['solve_position']),
        'pinned_source_found': source_ok,
    }
    print('\n--- ACQUISITION_GATES ---')
    for k,v in checks.items():
        print(f'{k}={"PASS" if v else "FAIL"}')
    ok=all(checks.values())
    print('interpretationRule=do not tune frequencyHz, dampingRatio, restitution, joint length or solver constants until the ARMv7 instruction/dataflow comparison is resolved from this report')
    print('verdict=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 5

if __name__=='__main__':
    raise SystemExit(main())
