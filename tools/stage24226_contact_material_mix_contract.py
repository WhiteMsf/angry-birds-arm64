#!/usr/bin/env python3
"""Stage 24.22.6: untouched ARMv7 Box2D contact material-mixing audit.

Diagnostic only. Stage 24.22.5 tied GameLua createCircle/createBox construction
back to untouched ARMv7 and showed that all physics-affecting body/fixture values
currently under suspicion are passed exactly as reconstructed: dynamic/static type
from density, angularDamping=1.0, inertiaScale=1.0, default body flags, direct
friction/restitution/density, and direct circle/box geometry. The only observed
construction mismatch is fixture userData (original RenderObjectData*, reconstructed
bridge nullptr), which cannot alter solver impulses.

The next lower ownership boundary is b2Contact's material combination. Stock Box2D
2.1.2 mixes friction as sqrt(f1*f2) and restitution as max(r1,r2). With a bird
restitution 0.43 and ground restitution 0.0, stock max preserves 0.43 and can keep
feeding restitution to low-amplitude contacts. This audit asks whether Rovio kept
that exact rule or changed it.
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
        marker=''
        if 0.0 <= abs(f) <= 16.0:
            marker=' candidateFloat=yes'
        print(f'0x{addr:08x} word=0x{u:08x} float={f:.12g}{marker}')

def print_math_context(lines, radius=14):
    pats=(
        r'__aeabi_fcmp(?:lt|le|gt|ge|eq)',
        r'__aeabi_fmul|__mulsf3',
        r'__aeabi_fdiv|__divsf3',
        r'sqrtf?|__aeabi_f2d|__aeabi_d2f',
    )
    hits=[]
    for i,line in enumerate(lines):
        if any(re.search(p,line,re.I) for p in pats):
            hits.append(i)
    if not hits:
        print('NO_MATERIAL_MATH_CONTEXT')
        return
    spans=[]
    for i in hits:
        a=max(0,i-radius); b=min(len(lines),i+radius+1)
        if spans and a <= spans[-1][1]:
            spans[-1]=(spans[-1][0], max(spans[-1][1],b))
        else:
            spans.append((a,b))
    for n,(a,b) in enumerate(spans,1):
        print(f'--- materialMathWindow={n} lines={a+1}-{b} ---')
        for line in lines[a:b]:
            print(line)

def main():
    if len(sys.argv)!=5:
        print('usage: stage24226_contact_material_mix_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <stock-box2d-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,stock=sys.argv[1:]
    print('ANGRY_STAGE24_22_6_CONTACT_MATERIAL_MIX_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; no physics/contact/material/gameplay mutation')
    print('question=does untouched ARMv7 combine fixture friction/restitution exactly like stock Box2D 2.1.2 (sqrt(f1*f2), max(r1,r2)), or did Rovio change the contact material-mixing rule?')
    print('priorProof=Stage24.22.5 createCircle/createBox physically matches current bridge: density selects body type; angularDamping=1.0; linearDamping=0; allowSleep/awake/active=true; fixedRotation/bullet=false; inertiaScale=1.0; friction/restitution/density and geometry pass directly. Original fixture userData=RenderObjectData* while current bridge uses nullptr, but userData cannot change solver impulses.')
    print('runtimeRelevance=bird fixture friction=0.3 restitution=0.43 density=6.0; ground fixture friction=0.8 restitution=0.0 density=0.0; terminal birds can alternate near vertical velocities +1.198/-0.135 and never satisfy original Lua speed<0.05 removal gate')
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

    # Box2D 2.1.x normally exposes b2Contact constructors and Update/Reset-ish
    # ownership under these names. Keep broad context if one exact variant is absent.
    target_rx=[
        re.compile(r'^b2Contact::b2Contact\('),
        re.compile(r'^b2Contact::Reset\('),
        re.compile(r'^b2Contact::Update\('),
    ]
    context_rx=[
        re.compile(r'^b2Fixture::Create\('),
        re.compile(r'^b2ContactSolver::b2ContactSolver\('),
        re.compile(r'^b2ContactFactory::Create\('),
    ]
    targets=[]; contexts=[]
    for s in syms:
        if s.typ not in 'TtWw':
            continue
        if any(rx.search(s.name) for rx in target_rx):
            targets.append(s)
        elif any(rx.search(s.name) for rx in context_rx):
            contexts.append(s)

    print('\n--- ARMV7_CONTACT_MATERIAL_OWNER_SYMBOLS ---')
    for s in targets:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not targets:
        print('NO_NAMED_B2CONTACT_OWNER_SYMBOLS')

    # Also inventory every b2Contact symbol so a renamed/inlined ownership path is visible.
    print('\n--- ARMV7_ALL_B2CONTACT_SYMBOLS ---')
    all_contact=[s for s in syms if s.typ in 'TtWw' and ('b2Contact::' in s.name or 'b2ContactFactory::' in s.name)]
    for s in all_contact:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not all_contact:
        print('NO_B2CONTACT_SYMBOLS')

    seen=set()
    dump_targets=targets[:]
    # If exact owner names weren't found, dump small b2Contact functions first as candidates.
    if not dump_targets:
        dump_targets=[s for s in all_contact if 0 < s.size <= 0x800]
    for s in dump_targets:
        key=(s.addr,s.size,s.name)
        if key in seen: continue
        seen.add(key)
        start=s.addr & ~1
        size=s.size or 0x800
        stop=start+size
        print(f'\n--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body:
            print(line)
        print('\n--- DECODED_LITERAL_POOL ---')
        decode_word_lines(body)
        print('\n--- MATERIAL_MATH_NEIGHBORHOODS ---')
        print_math_context(body)

    print('\n--- ARMV7_CONTEXT_SYMBOLS ---')
    for s in contexts:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    root=Path(stock)
    print('\n--- PINNED_2_1_2_CONTACT_HEADER_MIX_SOURCE ---')
    print_source_focus(find_source(root,'b2Contact.h'), [
        r'b2MixFriction', r'b2MixRestitution', r'sqrt', r'b2Max'
    ], radius=8)
    print('\n--- PINNED_2_1_2_CONTACT_IMPLEMENTATION_SOURCE ---')
    print_source_focus(find_source(root,'b2Contact.cpp'), [
        r'b2Contact::b2Contact', r'm_friction', r'm_restitution', r'b2MixFriction', r'b2MixRestitution'
    ], radius=14)
    print('\n--- PINNED_2_1_2_SOLVER_CONSUMER_SOURCE ---')
    print_source_focus(find_source(root,'b2ContactSolver.cpp'), [
        r'cc->restitution', r'constraint->restitution', r'velocityBias', r'velocityThreshold'
    ], radius=10)

    print('\ninterpretationRule=do not patch bird restitution, ground restitution, velocity threshold, sleep constants, or Lua speed<0.05 until the ARMv7 b2Contact material-combination rule is resolved; if mixing is stock too, move next to solver/manifold/contact persistence rather than object construction')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
