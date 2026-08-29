#!/usr/bin/env python3
"""Stage 24.25.8: audio lifecycle closure / ground-collision provenance audit.

Diagnostic only.  It deliberately does not patch the ARM64 runtime.  The goal
is to close the remaining observable boundaries before declaring the current
audio subsystem complete:
  * AudioOutput/AudioMixer start/stop output semantics;
  * master-volume ownership around the already-proven track clamp;
  * clip query/stop/voice cleanup paths;
  * provenance of the literal `ground_collision` request seen at runtime;
  * whether an original audio payload with a matching ground alias exists.
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

OWNER_PREFIXES=(
    'audio::AudioOutput::', 'audio::AudioMixer::',
    'game::Resources::', 'game::LuaResources::'
)
TOKENS=(
    'startOutput','stopOutput','startAudioOutput','stopAudioOutput',
    'setMasterVolume','getMasterVolume','setTrackVolume','getTrackVolume',
    'playClip','stopClip','stopClips','isClipPlaying','getPlayingClipCount',
    'flushQueueAndRemoveEndedClips','mixUnlimited','mixLimited','start()','stop()'
)

def wanted(s:Sym)->bool:
    if s.typ not in 'TtWw': return False
    if not any(p in s.name for p in OWNER_PREFIXES): return False
    return any(t in s.name for t in TOKENS)

def scan_tree(root, needles):
    hits={n:[] for n in needles}
    if not root or not os.path.isdir(root): return hits
    for base,_,files in os.walk(root):
        for fn in files:
            p=os.path.join(base,fn)
            try:
                b=open(p,'rb').read()
            except OSError:
                continue
            low=b.lower()
            for n in needles:
                nb=n.encode('utf-8').lower()
                pos=0
                while True:
                    i=low.find(nb,pos)
                    if i<0: break
                    hits[n].append((p,i))
                    pos=i+max(1,len(nb))
    return hits

def main():
    if len(sys.argv)!=6:
        print('usage: stage24258_audio_closure_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <scripts-dir> <audio-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,scripts,audio_root=sys.argv[1:]
    print('ANGRY_STAGE24_25_8_AUDIO_CLOSURE_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; no gameplay/audio mutation')
    print('questions=start-stop-output semantics; master-volume semantics; clip end/query cleanup; ground_collision provenance')
    print(f'lib={lib}')
    print(f'scripts={scripts}')
    print(f'audioRoot={audio_root}')
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
    print(f'nmExit={rc} parsedSymbols={len(syms)} targets={len(matches)}')
    print('\n--- TARGET_SYMBOLS ---')
    for s in matches:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    print('\n--- ORIGINAL_SCRIPT_STRING_PROVENANCE ---')
    needles=['ground_collision','audioRampVolume','audioRampLength','startAudioOutput','stopAudioOutput','isAudioPlaying','stopAudio','stopAllAudio']
    sh=scan_tree(scripts,needles)
    for n in needles:
        hs=sh[n]
        print(f"needle='{n}' hits={len(hs)}")
        for p,off in hs[:40]:
            try: rel=os.path.relpath(p,scripts)
            except Exception: rel=p
            print(f'  {rel} offset=0x{off:x}')
        if len(hs)>40: print(f'  ... +{len(hs)-40} more')

    print('\n--- ORIGINAL_AUDIO_PAYLOAD_GROUND_CANDIDATES ---')
    files=[]
    if os.path.isdir(audio_root):
        for base,_,fns in os.walk(audio_root):
            for fn in fns:
                if fn.lower().endswith(('.wav','.mp3')):
                    files.append(os.path.join(base,fn))
    ground=[p for p in files if 'ground' in os.path.basename(p).lower()]
    print(f'audioFiles={len(files)} groundNamedFiles={len(ground)}')
    for p in sorted(ground):
        print('  '+os.path.relpath(p,audio_root))
    exact=[p for p in files if os.path.splitext(os.path.basename(p))[0].lower()=='ground_collision']
    print(f'exactPayloadBasename_ground_collision={len(exact)}')

    # Bodies are deliberately bounded.  The user-supplied original lib remains
    # the authority; this report only exposes the control/data flow.
    for s in matches:
        start=s.addr & ~1
        size=s.size or 0x100
        size=min(max(size,4),0x800)
        stop=start+size
        print(f'\n--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body: print(line)

    print('\ninterpretationRule=do not fix ground_collision, output suspend, master gain, stop/query, or loop behavior unless original Lua/native ownership is proven; a missing payload plus literal Lua request may itself be vanilla')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
