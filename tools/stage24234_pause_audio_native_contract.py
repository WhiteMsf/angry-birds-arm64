#!/usr/bin/env python3
"""Stage 24.23.4: untouched ARMv7 pause-audio native contract audit.

Diagnostic only. Dumps the exact LuaResources volume functions that the pause
menu reaches through res.getTrackVolume/setTrackVolume and nearby audio methods.
No runtime/gameplay/audio behavior is modified.
"""
from __future__ import annotations
import os, re, subprocess, sys
from dataclasses import dataclass

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

TARGETS = [
    'game::LuaResources::getTrackVolume(float)',
    'game::LuaResources::setTrackVolume(float, float)',
    'game::LuaResources::getMasterVolume()',
    'game::LuaResources::setMasterVolume(float)',
    'game::LuaResources::isAudioPlaying(lua::LuaState*)',
]

def main():
    if len(sys.argv)!=4:
        print('usage: stage24234_pause_audio_native_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so>', file=sys.stderr)
        return 2
    nm,objdump,lib=sys.argv[1:]
    print('ANGRY_STAGE24_23_4_PAUSE_AUDIO_NATIVE_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; no audio/menu/gameplay mutation')
    print('question=what exact native contract backs res.getTrackVolume/setTrackVolume reached by untouched pause drawMenu?')
    print(f'lib={lib}')
    for p in (nm,objdump,lib):
        if not os.path.exists(p):
            print(f'ERROR missing={p}')
            return 3
    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml:
        rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')
    found=[]
    for target in TARGETS:
        exact=[s for s in syms if s.name==target and s.typ in 'TtWw']
        if exact:
            found.extend(exact)
        else:
            # tolerate compiler spelling variations but keep matching narrow
            key=target.split('::')[-1].split('(')[0]
            found.extend([s for s in syms if 'LuaResources::'+key+'(' in s.name and s.typ in 'TtWw'])
    # dedupe by address/name
    uniq=[]; seen=set()
    for s in sorted(found, key=lambda x:(x.addr,x.name)):
        k=(s.addr,s.name)
        if k not in seen:
            seen.add(k); uniq.append(s)
    print('\n--- TARGET_SYMBOLS ---')
    for s in uniq:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not uniq:
        print('NO_TARGET_SYMBOLS')
        return 4
    for s in uniq:
        start=s.addr & ~1
        size=s.size or 0x100
        stop=start+size
        print(f'\n--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body:
            print(line)
    print('\ninterpretationRule=use this only to reconstruct the native Resources volume API required by untouched pause Lua; do not synthesize pause actions or sound state from guessed values')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
