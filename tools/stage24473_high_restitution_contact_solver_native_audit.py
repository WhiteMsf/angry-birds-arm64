#!/usr/bin/env python3
"""Stage 24.47.3: ARMv7 high-restitution contact-solver cross-proof.

Read-only acquisition. Dumps Rovio's b2ContactSolver constructor,
InitVelocityConstraints and SolveVelocityConstraints beside the pinned Box2D
2.1.2 implementation. Focus is the restitution velocityBias path and the
one-/two-point normal-impulse solver used by rubber fixtures with e > 1.
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

def dump_source(path:Path|None, lo:int, hi:int):
    if path is None:
        print('source=NOT_FOUND')
        return False
    print(f'source={path}')
    for i,line in enumerate(path.read_text(errors='replace').splitlines(),1):
        if lo <= i <= hi:
            print(f'{i:05d}: {line}')
    return True

def decode_literals(lines):
    rx=re.compile(r'^\s*([0-9a-fA-F]+):.*?\.word\s+0x([0-9a-fA-F]{8})\s*$')
    found=False
    for line in lines:
        m=rx.match(line)
        if not m: continue
        found=True
        u=int(m.group(2),16)
        f=struct.unpack('<f', struct.pack('<I',u))[0]
        marker=''
        if f == f and abs(f) != float('inf') and 0.0 < abs(f) <= 128.0:
            marker=' candidateFloat=yes'
        print(f'0x{int(m.group(1),16):08x} word=0x{u:08x} float={f:.12g}{marker}')
    if not found:
        print('NO_LITERAL_WORDS_DECODED')

TARGETS={
    'ctor': re.compile(r'b2ContactSolver::b2ContactSolver\('),
    'init': re.compile(r'b2ContactSolver::InitVelocityConstraints\('),
    'solve_velocity': re.compile(r'b2ContactSolver::SolveVelocityConstraints\('),
}

def main():
    if len(sys.argv)!=5:
        print('usage: stage24473_high_restitution_contact_solver_native_audit.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <box2d-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,boxroot=sys.argv[1:]
    print('ANGRY_STAGE24_47_3_HIGH_RESTITUTION_CONTACT_SOLVER_NATIVE_AUDIT 1')
    print('policy=DIAGNOSTIC_ONLY; no Box2D/Lua/gameplay mutation')
    print('question=does the original Rovio contact velocityBias/normal-impulse path differ from pinned Box2D 2.1.2 for rubber restitution > 1?')
    print('runtimeIsolation=LevelGE_2 free ExtraRubberBall contacts isolate contact response from the distance-joint network; LevelP3_306 remains the network cross-check')
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
        if s.typ not in 'TtWw': continue
        for key,rx in TARGETS.items():
            if rx.search(s.name): found[key].append(s)

    print('\n--- ARMV7_CONTACT_SOLVER_SYMBOLS ---')
    for key in TARGETS:
        if not found[key]: print(f'{key}=NOT_FOUND')
        for s in found[key]:
            print(f'{key} {s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    all_body=[]
    seen=set()
    for key in TARGETS:
        for s in found[key]:
            start=s.addr & ~1
            if start in seen: continue
            seen.add(start)
            stop=start+(s.size or 0x1400)
            print(f'\n--- ARMV7_BODY key={key} name={s.name} start=0x{start:x} size=0x{s.size:x} stop=0x{stop:x} ---')
            drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
            print(f'objdumpExit={drc} lines={len(body)}')
            all_body += body
            for line in body: print(line)
            print('--- DECODED_LITERAL_POOL ---')
            decode_literals(body)

    src=find_source(Path(boxroot),'b2ContactSolver.cpp')
    settings=find_source(Path(boxroot),'b2Settings.h')
    print('\n--- PINNED_2_1_2_CONTACT_SOLVER_SOURCE ---')
    source_ok=dump_source(src, 1, 470)
    print('\n--- PINNED_2_1_2_SETTINGS_RESTITUTION_THRESHOLD ---')
    settings_ok=False
    if settings:
        lines=settings.read_text(errors='replace').splitlines()
        print(f'source={settings}')
        for i,line in enumerate(lines,1):
            if 'velocityThreshold' in line or (75 <= i <= 90):
                print(f'{i:05d}: {line}')
        settings_ok=any('b2_velocityThreshold' in x and '1.0f' in x for x in lines)
    else:
        print('source=NOT_FOUND')

    body_text='\n'.join(all_body)
    # Evidence gates only.  #1065353216 is IEEE754 1.0f synthesized as an ARM
    # immediate and appears in the constructor arithmetic.  It is not by itself
    # called a threshold proof; the full dataflow remains in this report.
    checks={
        'armv7_ctor_found': bool(found['ctor']),
        'armv7_init_velocity_found': bool(found['init']),
        'armv7_solve_velocity_found': bool(found['solve_velocity']),
        'pinned_contact_source_found': source_ok,
        'pinned_threshold_1_found': settings_ok,
        'armv7_one_float_immediate_present': '#1065353216' in body_text,
        'armv7_float_multiply_present': '__mulsf3' in body_text,
        'armv7_float_compare_present': ('__aeabi_fcmplt' in body_text or '__aeabi_fcmpgt' in body_text),
    }
    print('\n--- ACQUISITION_GATES ---')
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
    ok=all(checks.values())
    print('interpretationRule=do not clamp restitution 5.5 or tune rubber/joints; first resolve the ARMv7 constructor velocityBias and SolveVelocityConstraints dataflow, using LevelGE_2 isolated contacts as runtime cross-proof')
    print('verdict=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 5

if __name__=='__main__':
    raise SystemExit(main())
