#!/usr/bin/env python3
"""Stage 24.25.4 complete audio-fidelity audit.

Diagnostic/static side only.  Audits the untouched ARMv7 track-volume path,
createAudio/AudioReader/AudioClip decode path, and the user's original MP3
payload headers.  It deliberately does not choose or implement an MP3 backend.
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

def mp3_first_frame(path:Path):
    b=path.read_bytes()
    pos=0
    id3=False
    if len(b)>=10 and b[:3]==b'ID3':
        id3=True
        size=((b[6]&0x7f)<<21)|((b[7]&0x7f)<<14)|((b[8]&0x7f)<<7)|(b[9]&0x7f)
        pos=10+size
        if b[5] & 0x10: pos += 10
    br_v1_l3=[0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0]
    br_v2_l3=[0,8,16,24,32,40,48,56,64,80,96,112,128,144,160,0]
    sr_base=[44100,48000,32000,0]
    for i in range(pos, max(pos,len(b)-4)):
        h=int.from_bytes(b[i:i+4],'big')
        if (h & 0xffe00000) != 0xffe00000: continue
        ver=(h>>19)&3; layer=(h>>17)&3; br=(h>>12)&15; sri=(h>>10)&3
        if ver==1 or layer!=1 or br in (0,15) or sri==3: continue # require Layer III
        if ver==3:
            version='MPEG1'; sr=sr_base[sri]; bitrate=br_v1_l3[br]
        elif ver==2:
            version='MPEG2'; sr=sr_base[sri]//2; bitrate=br_v2_l3[br]
        elif ver==0:
            version='MPEG2.5'; sr=sr_base[sri]//4; bitrate=br_v2_l3[br]
        else: continue
        mode=(h>>6)&3
        channels=1 if mode==3 else 2
        return dict(offset=i, id3=id3, version=version, layer='III', bitrate_kbps=bitrate,
                    sample_rate=sr, channels=channels, bytes=len(b))
    return dict(offset=-1,id3=id3,bytes=len(b),error='no-layer3-frame')

def main():
    if len(sys.argv)!=5:
        print('usage: stage24254_audio_fidelity_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <audio-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,audio_root=sys.argv[1:]
    print('ANGRY_STAGE24_25_4_AUDIO_FIDELITY_CONTRACT 1')
    print('policy=AUDIT_FIRST; only already-proven AudioMixer track-volume clamp may be mirrored by runtime; no MP3 implementation')
    print('questions=does original track volume clamp; can Lua intentionally overshoot; how does original createAudio/decode path treat MP3; what are untouched MP3 payload formats?')
    print(f'lib={lib}')
    print(f'audioRoot={audio_root}')
    for p in (nm,objdump,lib):
        if not os.path.exists(p):
            print(f'ERROR missing={p}')
            return 3
    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml:
        rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')

    exact_keys=(
        'audio::AudioMixer::setTrackVolume(', 'audio::AudioMixer::getTrackVolume(',
        'audio::AudioOutput::setTrackVolume(', 'audio::AudioOutput::getTrackVolume(',
        'game::LuaResources::setTrackVolume(', 'game::LuaResources::getTrackVolume(',
        'game::Resources::createAudio(', 'game::LuaResources::createAudio(',
        'audio::AudioClip::AudioClip(', 'audio::AudioReader::AudioReader(',
    )
    broad_keys=('audio::AudioReader::','audio::AudioDecoder::','audio::Mp3','audio::MP3','MP3','Mpeg','MPEG','FileFormat')
    matches=[]; seen=set()
    for s in sorted(syms,key=lambda x:(x.addr,x.name)):
        if s.typ not in 'TtWw': continue
        if any(k in s.name for k in exact_keys) or any(k in s.name for k in broad_keys):
            key=(s.addr,s.name)
            if key not in seen:
                seen.add(key); matches.append(s)
    print('\n--- TARGET_SYMBOLS ---')
    for s in matches: print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    # Dump the most relevant bodies. Cap broad decoder symbols to keep report usable.
    priority=[]
    for s in matches:
        n=s.name
        if ('setTrackVolume' in n or 'getTrackVolume' in n or 'createAudio(' in n or
            'AudioReader::' in n or 'AudioClip::AudioClip(' in n or
            'MP3' in n or 'Mpeg' in n or 'MPEG' in n):
            priority.append(s)
    for s in priority[:32]:
        start=s.addr & ~1; size=min(s.size or 0x100,0x900); stop=start+size
        print(f'\n--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body: print(line)

    # Machine-readable proof marker for the clamp already visible in the untouched body:
    # __aeabi_fcmplt(value,0), then __aeabi_fcmpgt(value,1), storing 0/1 when outside.
    setmix=[s for s in syms if 'audio::AudioMixer::setTrackVolume(float, int)'==s.name]
    if setmix:
        s=setmix[0]; start=s.addr&~1; stop=start+min(s.size or 0x300,0x400)
        _,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        txt='\n'.join(body)
        has_lt='__aeabi_fcmplt' in txt
        has_gt='__aeabi_fcmpgt' in txt
        has_one=('1065353216' in txt or '#1065353216' in txt)
        print(f'\nTRACK_VOLUME_CLAMP_PROOF symbol=AudioMixer::setTrackVolume lowerCompare0={str(has_lt).lower()} upperCompare1={str(has_gt).lower()} floatOneImmediate={str(has_one).lower()} conclusion={"CLAMP_0_1_PROVEN" if has_lt and has_gt and has_one else "REVIEW_BODY"}')

    print('\n--- MP3_PAYLOAD_HEADERS ---')
    root=Path(audio_root)
    mp3s=sorted(root.rglob('*.mp3')) if root.exists() else []
    print(f'mp3Count={len(mp3s)}')
    variants={}
    for p in mp3s:
        try: info=mp3_first_frame(p)
        except Exception as e: info={'error':str(e),'bytes':p.stat().st_size if p.exists() else -1}
        rel=str(p.relative_to(root)).replace('\\','/') if root.exists() else str(p)
        parts=' '.join(f'{k}={v}' for k,v in info.items())
        print(f'MP3 path={rel!r} {parts}')
        if 'sample_rate' in info:
            key=(info.get('version'),info.get('bitrate_kbps'),info.get('sample_rate'),info.get('channels'))
            variants[key]=variants.get(key,0)+1
    print('MP3_VARIANTS')
    for k,c in sorted(variants.items(),key=lambda x:str(x[0])):
        print(f'  count={c} version={k[0]} bitrate_kbps={k[1]} sample_rate={k[2]} channels={k[3]}')

    print('\ninterpretationRule=separate raw Lua requests from native-stored track volume; a Lua overshoot can be vanilla while an observable track volume above 1.0 cannot be, because untouched AudioMixer clamps before storage')
    print('mp3Rule=do not choose MediaPlayer/OpenSL/decoder implementation until original createAudio/AudioReader ownership and payload format are read together')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
