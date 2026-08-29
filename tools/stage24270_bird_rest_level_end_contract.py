#!/usr/bin/env python3
"""Stage 24.27.0 bird-rest/angular-settle/removal/level-end native contract audit.

Read-only. Dumps the untouched ARMv7 sleep/awake solver bodies and the *effective*
patched Box2D 2.1.2 source used by the ARM64 build. Gameplay/Lua control-flow is
captured separately by the runtime closure probe.
"""
from __future__ import annotations
import os, re, subprocess, sys
from dataclasses import dataclass
from pathlib import Path

HEADER='ANGRY_STAGE24_27_0_BIRD_REST_LEVEL_END_NATIVE_CONTRACT 1'

@dataclass
class Sym:
    addr:int; size:int; typ:str; name:str

def run(args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     text=True,errors='replace')
    return p.returncode,p.stdout.splitlines()

def parse_nm(lines):
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    out=[]
    for line in lines:
        m=rx.match(line)
        if m: out.append(Sym(int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(4)))
    return out

def find_one(root:Path,name:str):
    hits=list(root.rglob(name)); return hits[0] if hits else None

def source_window(path:Path|None, patterns:list[str], radius:int=8):
    if not path:
        print('source=NOT_FOUND'); return
    print(f'source={path}')
    lines=path.read_text(errors='replace').splitlines()
    wanted=set()
    for i,line in enumerate(lines):
        if any(re.search(p,line,re.I) for p in patterns):
            wanted.update(range(max(0,i-radius),min(len(lines),i+radius+1)))
    last=-2
    for i in sorted(wanted):
        if i!=last+1 and last>=0: print('...')
        print(f'{i+1:05d}: {lines[i]}'); last=i

def main():
    if len(sys.argv)!=5:
        print('usage: stage24270_bird_rest_level_end_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <effective-box2d-root>',file=sys.stderr)
        return 2
    nm,objdump,lib,box=sys.argv[1:]
    print(HEADER)
    print('policy=DIAGNOSTIC_ONLY; no damping/sleep/velocity/contact/timer/camera/end-state mutation')
    print('question=when a shot bird visually settles slowly, which boundary owns the delay: Box2D awake/sleep, persistent contacts/angular velocity, Lua speed<0.05 remove timer, camera ownership, or level-end gating?')
    for x in (nm,objdump,lib,box):
        if not os.path.exists(x): print(f'ERROR missing={x}'); return 3

    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml: rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    targets=[
        r'b2Island::Solve\(', r'b2Body::SetAwake\(', r'b2World::Step\(',
        r'b2Body::SetLinearVelocity\(', r'b2Body::SetAngularVelocity\('
    ]
    matched=[s for s in syms if s.typ in 'TtWw' and any(re.search(p,s.name) for p in targets)]
    print(f'nmExit={rc} parsedSymbols={len(syms)} matched={len(matched)}')
    for s in matched: print(f'SYMBOL addr=0x{s.addr:08x} size=0x{s.size:x} type={s.typ} name={s.name}')
    seen=set()
    for s in matched:
        start=s.addr & ~1
        if start in seen: continue
        seen.add(start); size=s.size or 0x1000; stop=start+size
        print(f'--- ARMV7_BODY name={s.name} start=0x{start:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body: print(line)

    root=Path(box)
    print('--- EFFECTIVE_ARM64_SETTINGS_AFTER_ROVIO_PATCH ---')
    source_window(find_one(root,'b2Settings.h'),[
        r'linearSlop',r'angularSlop',r'velocityThreshold',r'timeToSleep',
        r'linearSleepTolerance',r'angularSleepTolerance',r'maxTranslation',
        r'maxRotation',r'contactBaumgarte'
    ],4)
    print('--- EFFECTIVE_ARM64_ISLAND_SLEEP_LOGIC ---')
    source_window(find_one(root,'b2Island.cpp'),[
        r'timeToSleep',r'linearSleepTolerance',r'angularSleepTolerance',
        r'm_sleepTime',r'SetAwake\(false\)',r'allowSleep'
    ],10)
    print('--- EFFECTIVE_ARM64_BODY_AWAKE_LOGIC ---')
    source_window(find_one(root,'b2Body.cpp'),[r'SetAwake',r'm_sleepTime',r'e_awakeFlag'],10)
    print('runtimeCorrelation=stage24.27.0-bird-rest-runtime.txt samples Lua+Box2D at ~10Hz plus immediate state transitions; it reports observed consecutive time below remove/sleep tolerances but does not expose or mutate private m_sleepTime')
    print('interpretationRule=do not change angularDamping, restitution, sleep thresholds, remove timer, or level-end timing until runtime identifies the gate and ARMv7 comparison justifies a divergence')
    return 0
if __name__=='__main__': raise SystemExit(main())
