#!/usr/bin/env python3
"""Stage 24.25.0: original ARMv7 audio-system contract audit.

Diagnostic only. Inventories the native LuaResources/Resources/AudioOutput entry
points that back untouched gamelogic audio calls. No audio state or playback is
implemented here.
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

KEYS=(
    'createAudio','playAudio','stopAudio','stopAllAudio','isAudioPlaying',
    'getAudioOutput','getTrackVolume','setTrackVolume','getMasterVolume',
    'setMasterVolume'
)

def wanted(s:Sym)->bool:
    if s.typ not in 'TtWw': return False
    n=s.name
    owner=('game::LuaResources::' in n or 'game::Resources::' in n or
           'audio::AudioOutput::' in n)
    return owner and any(k in n for k in KEYS)

def main():
    if len(sys.argv)!=4:
        print('usage: stage24250_audio_system_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so>', file=sys.stderr)
        return 2
    nm,objdump,lib=sys.argv[1:]
    print('ANGRY_STAGE24_25_0_AUDIO_NATIVE_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; no playback/volume/gameplay mutation')
    print('question=what exact native contracts back untouched res.createAudio/playAudio/stopAudio/isAudioPlaying and volume APIs?')
    print(f'lib={lib}')
    for p in (nm,objdump,lib):
        if not os.path.exists(p):
            print(f'ERROR missing={p}')
            return 3
    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml:
        rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    matches=[]; seen=set()
    for s in sorted((x for x in syms if wanted(x)), key=lambda x:(x.addr,x.name)):
        k=(s.addr,s.name)
        if k not in seen:
            seen.add(k); matches.append(s)
    print(f'nmExit={rc} parsedSymbols={len(syms)} audioTargets={len(matches)}')
    print('\n--- TARGET_SYMBOLS ---')
    for s in matches:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not matches:
        print('NO_TARGET_SYMBOLS')
        return 4
    print('\n--- OWNER_SUMMARY ---')
    for owner in ('game::LuaResources::','game::Resources::','audio::AudioOutput::'):
        owned=[s for s in matches if owner in s.name]
        print(f'{owner} count={len(owned)}')
        for s in owned: print(f'  0x{s.addr:08x} {s.name}')
    # Bodies are bounded so the report stays useful instead of becoming an ELF dump.
    for s in matches:
        start=s.addr & ~1
        size=s.size or 0x100
        size=min(size,0x700)
        stop=start+size
        print(f'\n--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body: print(line)
    print('\ninterpretationRule=reconstruct only proven Resources/AudioOutput ownership and argument flow; do not synthesize audio handles, track routing, loop semantics, or volume state from guesses')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
