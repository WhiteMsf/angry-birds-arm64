#!/usr/bin/env python3
"""Stage 24.25.6 AudioClipInstance EOF / loop ownership audit.

Static diagnostic only. Stage24.25.5 proved that AudioClip::getData delegates to
AudioReader::readData and that the mixer delegates each voice read to
AudioClipInstance::fetchData.  Therefore fetchData -- not AudioMixer::playClip --
is the missing ownership boundary for EOF, cursor rewind and loop semantics.

This tool disassembles the complete untouched ARMv7 AudioClipInstance / cursor /
queue-removal path and emits conservative machine-readable relationships.  It
never selects or implements an ARM64 MP3 decoder.
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
    return p.returncode,p.stdout.splitlines()

def parse_nm(lines):
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    out=[]
    for line in lines:
        m=rx.match(line)
        if m:
            out.append(Sym(int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(4)))
    return out

def body(objdump,lib,s,max_bytes=0x3000):
    start=s.addr & ~1
    size=min(s.size or 0x100,max_bytes)
    stop=start+size
    rc,lines=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
    return rc,lines,start,stop

def calls(lines):
    out=[]
    for ln in lines:
        if re.search(r'\bblx?\b',ln):
            m=re.search(r'<([^>]+)>',ln)
            if m and m.group(1) not in out: out.append(m.group(1))
    return out

def main():
    if len(sys.argv)!=4:
        print('usage: stage24256_audioclipinstance_eof_loop_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so>',file=sys.stderr)
        return 2
    nm,objdump,lib=sys.argv[1:]
    print('ANGRY_STAGE24_25_6_AUDIOCLIPINSTANCE_EOF_LOOP_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; untouched ARMv7 ownership; no MP3 backend selected')
    print('premise=Stage24.25.5: mixer -> AudioClipInstance::fetchData -> AudioClip::getData -> AudioReader::readData')
    print('questions=exact EOF sentinel; loop flag consumption; cursor rewind/reset; ended-voice flag; queue removal; handle lifetime')
    print(f'lib={lib}')
    for p in (nm,objdump,lib):
        if not os.path.exists(p): print(f'ERROR missing={p}'); return 3
    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml: rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')

    exact={
      'audio::AudioMixer::flushQueueAndRemoveEndedClips()',
      'audio::AudioMixer::playClip(audio::AudioClip*, float, bool, int)',
      'audio::AudioMixer::mixUnlimited8(audio::AudioConfiguration const&, void*, int)',
      'audio::AudioMixer::mixUnlimited16(audio::AudioConfiguration const&, void*, int)',
      'audio::AudioMixer::mixUnlimited8to16(audio::AudioConfiguration const&, void*, int)',
      'audio::AudioClip::getData(void*, int, audio::AudioClipCursor*)',
      'audio::AudioReader::readData(void*, int, int)',
      'audio::AudioReader::readData_mp3(void*, int, int)',
    }
    def wanted(s):
        n=s.name
        if n in exact: return True
        if n.startswith('audio::AudioClipInstance::'): return True
        if n.startswith('audio::AudioClipCursor::'): return True
        if n.startswith('audio::AudioMixer::') and any(k in n for k in (
            'flushQueue','RemoveEnded','isClipPlaying','stopClip','stopClips','getPlayingClipCount')): return True
        if n.startswith('lang::Array<audio::AudioClipInstance>') and any(k in n for k in ('remove','erase','add','resize')): return True
        return False
    targets=[s for s in sorted(syms,key=lambda x:(x.addr,x.name)) if s.typ in 'TtWw' and wanted(s)]
    print('\n--- TARGET_SYMBOLS ---')
    for s in targets: print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    bodies={}
    print('\n--- CALL_GRAPH_SUMMARY ---')
    for s in targets:
        rc2,ls,start,stop=body(objdump,lib,s)
        bodies[(s.addr,s.name)]=(rc2,ls,start,stop)
        cs=calls(ls)
        if cs:
            print(f'CALLER name={s.name!r}')
            for c in cs: print(f'  -> {c}')

    def one_contains(prefix_or_exact, needle):
        vals=[]
        for s in targets:
            if s.name==prefix_or_exact or s.name.startswith(prefix_or_exact):
                vals.append(needle in '\n'.join(bodies[(s.addr,s.name)][1]))
        return any(vals)

    fetch_syms=[s for s in targets if s.name.startswith('audio::AudioClipInstance::fetchData(')]
    fetch_txt='\n'.join('\n'.join(bodies[(s.addr,s.name)][1]) for s in fetch_syms)
    flush_syms=[s for s in targets if s.name=='audio::AudioMixer::flushQueueAndRemoveEndedClips()']
    flush_txt='\n'.join('\n'.join(bodies[(s.addr,s.name)][1]) for s in flush_syms)
    print('\n--- MACHINE_MARKERS ---')
    print(f'FETCHDATA_FOUND value={str(bool(fetch_syms)).lower()} count={len(fetch_syms)}')
    print(f'FETCHDATA_CALLS_AUDIOCLIP_GETDATA value={str("AudioClip::getData" in fetch_txt).lower()}')
    print(f'FETCHDATA_REFERENCES_CURSOR value={str("AudioClipCursor" in fetch_txt).lower()}')
    print(f'FETCHDATA_HAS_LOOP_CONTROL value={str(bool(fetch_txt) and ("ldrb" in fetch_txt or "tst" in fetch_txt) and "cmp" in fetch_txt).lower()} reviewBody=true')
    print(f'FLUSH_FOUND value={str(bool(flush_syms)).lower()}')
    print(f'FLUSH_REMOVES_AUDIOCLIPINSTANCE value={str("AudioClipInstance::~AudioClipInstance" in flush_txt or "Array<audio::AudioClipInstance>::remove" in flush_txt).lower()} reviewBody=true')
    print('NOTE=machine markers are conservative; field/flag meaning must come from the full bodies below, not mnemonic presence alone')

    # Put the ownership-critical bodies first, then every selected support body.
    priority=[]
    order_prefix=[
      'audio::AudioClipInstance::fetchData(',
      'audio::AudioClipInstance::AudioClipInstance(',
      'audio::AudioClipInstance::~AudioClipInstance(',
      'audio::AudioClipCursor::',
      'audio::AudioMixer::flushQueueAndRemoveEndedClips()',
      'audio::AudioMixer::playClip(audio::AudioClip*, float, bool, int)',
      'audio::AudioClip::getData(void*, int, audio::AudioClipCursor*)',
      'audio::AudioReader::readData(void*, int, int)',
      'audio::AudioReader::readData_mp3(void*, int, int)',
      'audio::AudioMixer::mixUnlimited16(',
      'audio::AudioMixer::mixUnlimited8to16(',
      'audio::AudioMixer::mixUnlimited8(',
    ]
    for pfx in order_prefix:
        for s in targets:
            if (s.name==pfx or s.name.startswith(pfx)) and s not in priority: priority.append(s)
    for s in targets:
        if s not in priority: priority.append(s)

    print('\n--- DISASSEMBLY ---')
    seen=set()
    for s in priority:
        k=(s.addr,s.name)
        if k in seen: continue
        seen.add(k)
        rc2,ls,start,stop=bodies[k]
        print(f'\nARMV7_BODY name={s.name!r} start=0x{start:x} size=0x{stop-start:x} stop=0x{stop:x} objdumpExit={rc2} lines={len(ls)}')
        for ln in ls: print(ln)

    print('\ninterpretationRule=loop/EOF semantics are closed only when fetchData plus flushQueueAndRemoveEndedClips explain cursor rewind and voice termination without Android-specific assumptions')
    print('implementationGate=do not add MP3 playback until this ownership boundary is resolved')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
