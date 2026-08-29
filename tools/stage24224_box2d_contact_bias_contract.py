#!/usr/bin/env python3
"""Stage 24.22.4: untouched ARMv7 Box2D restitution velocity-bias audit.

Diagnostic only. Stage 24.22.3 proved Rovio's island sleep constants are not
stock 2.1.2 (linear sleep tolerance and time-to-sleep differ), but those values
cannot explain the observed ~1.198 m/s bird/ground rebound loop by themselves.
This audit resolves the contact-solver construction path where restitution's
velocityBias and b2_velocityThreshold are compiled into the ARMv7 binary.
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

def print_source_focus(path:Path|None, patterns:list[str], radius:int=9):
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

def decode_word_lines(lines):
    """Print .word literal-pool entries as IEEE754 floats where plausible."""
    rx=re.compile(r'^\s*([0-9a-fA-F]+):.*?\.word\s+0x([0-9a-fA-F]{8})\s*$')
    found=[]
    for line in lines:
        m=rx.match(line)
        if not m:
            continue
        u=int(m.group(2),16)
        f=struct.unpack('<f', struct.pack('<I', u))[0]
        if f == f and abs(f) != float('inf'):
            found.append((int(m.group(1),16),u,f))
    if not found:
        print('NO_LITERAL_WORDS_DECODED')
        return
    for addr,u,f in found:
        # Keep everything: even odd-looking values help distinguish pointers from constants.
        marker=''
        if 0.0 < abs(f) <= 16.0:
            marker=' candidateFloat=yes'
        print(f'0x{addr:08x} word=0x{u:08x} float={f:.12g}{marker}')

def print_cmp_context(lines, radius=14):
    """Show compare-call neighborhoods; velocity-threshold test compiles here on soft-float ARM."""
    hits=[]
    for i,line in enumerate(lines):
        if re.search(r'__aeabi_fcmp(?:lt|le|gt|ge)|__aeabi_fsub|__subsf3', line):
            hits.append(i)
    if not hits:
        print('NO_SOFTFLOAT_COMPARE_CONTEXT')
        return
    # Coalesce overlapping windows.
    spans=[]
    for i in hits:
        a=max(0,i-radius); b=min(len(lines),i+radius+1)
        if spans and a <= spans[-1][1]:
            spans[-1]=(spans[-1][0], max(spans[-1][1],b))
        else:
            spans.append((a,b))
    for n,(a,b) in enumerate(spans,1):
        print(f'--- compareWindow={n} lines={a+1}-{b} ---')
        for line in lines[a:b]:
            print(line)

TARGET_PATTERNS=[
    r'b2ContactSolver::b2ContactSolver\(',
    r'b2ContactSolver::InitVelocityConstraints\(',
]

# Extra functions are useful context but are not sufficient to resolve the threshold alone.
CONTEXT_PATTERNS=[
    r'b2ContactSolver::SolveVelocityConstraints\(',
    r'b2Island::Solve\(',
]

def main():
    if len(sys.argv)!=5:
        print('usage: stage24224_box2d_contact_bias_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <stock-box2d-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,stock=sys.argv[1:]
    print('ANGRY_STAGE24_22_4_BOX2D_CONTACT_BIAS_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; no physics/gameplay mutation')
    print('question=what exact ARMv7 restitution velocity threshold gates contact velocityBias, and does it differ from stock Box2D 2.1.2 b2_velocityThreshold=1.0f?')
    print('priorProof=Rovio b2Island::Solve compares linear-speed-squared against 0.01 (=> linearSleepTolerance=0.1) and minSleepTime against 0.25; stock 2.1.2 uses 0.01 and 0.5 respectively')
    print('runtimeRelevance=stuck birds hit ground near relative speed ~1.198; stock threshold 1.0 permits restitution at that speed, so an original threshold above ~1.198 would suppress the observed micro-bounce')
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

    targets=[]; contexts=[]
    for s in syms:
        if s.typ not in 'TtWw':
            continue
        if any(re.search(p,s.name) for p in TARGET_PATTERNS):
            targets.append(s)
        elif any(re.search(p,s.name) for p in CONTEXT_PATTERNS):
            contexts.append(s)

    print('\n--- ARMV7_CONTACT_CONSTRUCTION_SYMBOLS ---')
    for s in targets:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not targets:
        print('NO_CONTACT_CONSTRUCTION_SYMBOLS')

    for s in targets:
        start=s.addr & ~1
        size=s.size or 0x2400
        stop=start+size
        print(f'\n--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body:
            print(line)
        print('\n--- DECODED_LITERAL_POOL ---')
        decode_word_lines(body)
        print('\n--- SOFTFLOAT_COMPARE_NEIGHBORHOODS ---')
        print_cmp_context(body)

    print('\n--- ARMV7_CONTEXT_SYMBOLS ---')
    for s in contexts:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    root=Path(stock)
    print('\n--- PINNED_2_1_2_SETTINGS_SOURCE ---')
    print_source_focus(find_source(root,'b2Settings.h'), [r'velocityThreshold', r'timeToSleep', r'linearSleepTolerance'], radius=4)
    print('\n--- PINNED_2_1_2_CONTACT_CONSTRUCTOR_SOURCE ---')
    print_source_focus(find_source(root,'b2ContactSolver.cpp'), [
        r'b2ContactSolver::b2ContactSolver', r'b2MixRestitution', r'velocityBias', r'velocityThreshold', r'vRel'
    ], radius=11)

    print('\ninterpretationRule=resolve the ARMv7 threshold from constructor/velocityBias dataflow before changing b2Settings.h or bird restitution; do not patch the Lua speed<0.05 lifecycle gate')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
