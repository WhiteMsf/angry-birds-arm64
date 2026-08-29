#!/usr/bin/env python3
"""Stage 24.22.7: untouched ARMv7 Box2D linear-slop / position-correction audit.

Diagnostic only.

Stage 24.22.6 asked whether Rovio changed fixture material mixing. The named
b2Contact owner was the wrong boundary for Box2D 2.1.2, because the mix happens
inside b2ContactSolver construction. Fortunately Stage 24.22.4 already dumped
that exact constructor and proved stock behavior: friction is sqrt(fA*fB) and
restitution is max(rA,rB).

A stronger remaining clue is historical: untouched ARMv7 shape construction
materializes polygon m_radius=0.1f, while stock Box2D 2.1.2 derives its default
b2_polygonRadius from 2*b2_linearSlop (=0.01 for stock slop 0.005). The current
ARM64 bridge overrides only polygon radius to 0.1 while still compiling the
stock solver settings. This audit resolves the original linear slop and related
position-correction constants before any physics mutation.
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

def print_source_focus(path:Path|None, patterns:list[str], radius:int=10):
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
    rx=re.compile(r'^\s*([0-9a-fA-F]+):.*?\.word\s+0x([0-9a-fA-F]{8})\s*$')
    found=[]
    for line in lines:
        m=rx.match(line)
        if not m: continue
        u=int(m.group(2),16)
        f=struct.unpack('<f', struct.pack('<I', u))[0]
        if f == f and abs(f) != float('inf'):
            found.append((int(m.group(1),16),u,f))
    if not found:
        print('NO_LITERAL_WORDS_DECODED')
        return
    known={
        0x3ba3d70a:'stock_linearSlop_0.005',
        0x3c23d70a:'0.01',
        0x3d4ccccd:'candidate_linearSlop_0.05',
        0x3dcccccd:'0.1',
        0x3e4ccccd:'0.2',
        0x3f400000:'0.75',
        0x3f800000:'1.0',
    }
    for addr,u,f in found:
        tag=known.get(u,'')
        marker=f' known={tag}' if tag else (' candidateFloat=yes' if 0.0 <= abs(f) <= 16.0 else '')
        print(f'0x{addr:08x} word=0x{u:08x} float={f:.12g}{marker}')

def print_float_math_context(lines, radius=18):
    pats=(
        r'__aeabi_fcmp(?:lt|le|gt|ge|eq)',
        r'__aeabi_fadd|__addsf3',
        r'__aeabi_fsub|__subsf3',
        r'__aeabi_fmul|__mulsf3',
        r'__aeabi_fdiv|__divsf3',
        r'sqrtf?',
    )
    hits=[]
    for i,line in enumerate(lines):
        if any(re.search(p,line,re.I) for p in pats): hits.append(i)
    if not hits:
        print('NO_SOFTFLOAT_MATH_CONTEXT')
        return
    spans=[]
    for i in hits:
        a=max(0,i-radius); b=min(len(lines),i+radius+1)
        if spans and a <= spans[-1][1]: spans[-1]=(spans[-1][0],max(spans[-1][1],b))
        else: spans.append((a,b))
    for n,(a,b) in enumerate(spans,1):
        print(f'--- mathWindow={n} lines={a+1}-{b} ---')
        for line in lines[a:b]: print(line)

def print_known_float_hits(lines):
    # Literal-pool words are easiest, but also expose textual immediates when objdump
    # happens to print a raw 32-bit value in an instruction/comment.
    patterns=[
        ('stock_linearSlop_0.005','3ba3d70a'),
        ('candidate_linearSlop_0.05','3d4ccccd'),
        ('polygonRadius_0.1','3dcccccd'),
        ('maxLinearCorrection_orBaumgarte_0.2','3e4ccccd'),
        ('toiBaumgarte_0.75','3f400000'),
    ]
    anyhit=False
    for label,hexv in patterns:
        hs=[ln for ln in lines if hexv in ln.lower()]
        if hs:
            anyhit=True
            print(f'{label}: hits={len(hs)}')
            for ln in hs[:20]: print(ln)
    if not anyhit: print('NO_RAW_KNOWN_FLOAT_HEX_HITS')

TARGET_RX=[
    re.compile(r'^b2ContactSolver::SolvePositionConstraints\('),
    re.compile(r'^b2ContactSolver::b2ContactSolver\('),
    re.compile(r'^b2Island::Solve\('),
]
CONTEXT_RX=[
    re.compile(r'^b2PolygonShape::SetAsBox\('),
    re.compile(r'^b2PolygonShape::Set\('),
    re.compile(r'^b2World::Step\('),
]

def main():
    if len(sys.argv)!=5:
        print('usage: stage24227_linear_slop_position_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <stock-box2d-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,stock=sys.argv[1:]
    print('ANGRY_STAGE24_22_7_LINEAR_SLOP_POSITION_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; no physics/contact/gameplay mutation')
    print('resolvedBeforeThisStage=ARMv7 b2ContactSolver constructor at 0x77ff8..0x78028 computes sqrt(frictionA*frictionB) and max(restitutionA,restitutionB), exactly stock Box2D 2.1.2 material mixing')
    print('keyClue=ARMv7 GameLua polygon/box local shape construction materializes m_radius=0.1f; stock Box2D 2.1.2 polygonRadius=2*linearSlop=0.01 with linearSlop=0.005')
    print('currentHybrid=current ARM64 bridge forces polygon m_radius=0.1f but still compiles stock solver b2_linearSlop=0.005 and other stock position-correction settings')
    print('question=did Rovio also change b2_linearSlop (plausibly 0.05) and/or maxLinearCorrection/contactBaumgarte, making our current radius-only reconstruction internally inconsistent?')
    print(f'lib={lib}')
    print(f'stockBox2D={stock}')
    for p in (nm,objdump,lib,stock):
        if not os.path.exists(p):
            print(f'ERROR missing={p}')
            return 3

    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml: rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')

    targets=[]; contexts=[]
    for s in syms:
        if s.typ not in 'TtWw': continue
        if any(rx.search(s.name) for rx in TARGET_RX): targets.append(s)
        elif any(rx.search(s.name) for rx in CONTEXT_RX): contexts.append(s)

    print('\n--- ARMV7_POSITION_CORRECTION_OWNER_SYMBOLS ---')
    for s in targets: print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not targets: print('NO_NAMED_POSITION_CORRECTION_SYMBOLS')

    seen=set()
    for s in targets:
        key=(s.addr,s.size,s.name)
        if key in seen: continue
        seen.add(key)
        start=s.addr & ~1; size=s.size or 0x1800; stop=start+size
        print(f'\n--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body: print(line)
        print('\n--- DECODED_LITERAL_POOL ---')
        decode_word_lines(body)
        print('\n--- KNOWN_FLOAT_HEX_HITS ---')
        print_known_float_hits(body)
        print('\n--- SOFTFLOAT_MATH_NEIGHBORHOODS ---')
        print_float_math_context(body)

    print('\n--- ARMV7_CONTEXT_SYMBOLS ---')
    for s in contexts: print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    root=Path(stock)
    print('\n--- PINNED_2_1_2_SETTINGS_SOURCE ---')
    print_source_focus(find_source(root,'b2Settings.h'), [
        r'linearSlop', r'polygonRadius', r'maxLinearCorrection',
        r'contactBaumgarte', r'toiBaumgarte', r'velocityThreshold',
        r'timeToSleep', r'linearSleepTolerance'
    ], radius=5)
    print('\n--- PINNED_2_1_2_POSITION_SOLVER_SOURCE ---')
    print_source_focus(find_source(root,'b2ContactSolver.cpp'), [
        r'SolvePositionConstraints', r'linearSlop', r'maxLinearCorrection', r'baumgarte', r'b2Clamp'
    ], radius=16)
    print('\n--- PINNED_2_1_2_ISLAND_CALLER_SOURCE ---')
    print_source_focus(find_source(root,'b2Island.cpp'), [
        r'SolvePositionConstraints', r'contactBaumgarte', r'positionIterations'
    ], radius=10)
    print('\n--- PINNED_2_1_2_POLYGON_RADIUS_SOURCE ---')
    p=find_source(root,'b2Collision.h') or find_source(root,'b2PolygonShape.cpp')
    print_source_focus(p, [r'polygonRadius', r'linearSlop', r'm_radius'], radius=8)

    print('\ninterpretationRule=if ARMv7 position solver uses linearSlop=0.05 (or another non-stock value), patch the Box2D settings coherently rather than keeping a stock 0.005 solver with only polygon radius forced to 0.1; do not change the Lua speed<0.05 failure lifecycle gate')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
