#!/usr/bin/env python3
"""Stage 24.25.1: audio mixer + original WAV contract audit.

Diagnostic only.  Tightens the remaining native backend questions left by
Stage24.25.0 and inventories the user's untouched 1.4.2 WAV payload formats.
No audio is played and no source asset is modified.
"""
from __future__ import annotations
import os, re, struct, subprocess, sys
from dataclasses import dataclass
from collections import Counter, defaultdict

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

NEEDLES=(
    'audio::AudioOutput::playClip', 'audio::AudioOutput::stopClip',
    'audio::AudioOutput::stopClips', 'audio::AudioOutput::isClipPlaying',
    'audio::AudioOutput::AudioOutput', 'audio::AudioClip::AudioClip',
    'audio::AudioMixer::play', 'audio::AudioMixer::stop',
    'audio::AudioMixer::is', 'audio::AudioMixer::getTrackVolume',
    'audio::AudioMixer::setTrackVolume', 'audio::AudioMixer::mix',
    'game::Resources::createAudioOutput',
)

def wanted(s):
    return s.typ in 'TtWw' and any(n in s.name for n in NEEDLES)

def parse_wav(path):
    data=open(path,'rb').read()
    if len(data)<12 or data[:4]!=b'RIFF' or data[8:12]!=b'WAVE':
        return {'ok':False,'error':'not-RIFF/WAVE','bytes':len(data)}
    off=12; fmt=None; data_bytes=None; chunks=[]
    while off+8<=len(data):
        tag=data[off:off+4]; n=struct.unpack_from('<I',data,off+4)[0]
        payload=off+8
        chunks.append((tag.decode('latin1','replace'),n))
        if payload+n>len(data):
            return {'ok':False,'error':f'truncated-chunk-{tag!r}','bytes':len(data),'chunks':chunks}
        if tag==b'fmt ' and n>=16:
            code,channels,rate,byte_rate,align,bits=struct.unpack_from('<HHIIHH',data,payload)
            fmt=(code,channels,rate,byte_rate,align,bits,n)
        elif tag==b'data':
            data_bytes=n
        off=payload+n+(n&1)
    if not fmt or data_bytes is None:
        return {'ok':False,'error':'missing-fmt-or-data','bytes':len(data),'chunks':chunks}
    code,channels,rate,byte_rate,align,bits,fmt_size=fmt
    duration=(data_bytes/byte_rate) if byte_rate else 0.0
    return {'ok':True,'bytes':len(data),'code':code,'channels':channels,'rate':rate,
            'byte_rate':byte_rate,'align':align,'bits':bits,'fmt_size':fmt_size,
            'data_bytes':data_bytes,'duration':duration,'chunks':chunks}

def main():
    if len(sys.argv)!=5:
        print('usage: stage24251_audio_mixer_wav_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <sfx-dir>', file=sys.stderr)
        return 2
    nm,objdump,lib,sfx=sys.argv[1:]
    print('ANGRY_STAGE24_25_1_AUDIO_MIXER_WAV_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; no playback; no WAV mutation')
    print('question=what exact mixer/handle backend sits under Resources::playAudio, and what PCM formats do untouched 1.4.2 SFX use?')
    print(f'lib={lib}')
    print(f'wavSearchRoot={sfx}')
    for p in (nm,objdump,lib):
        if not os.path.exists(p):
            print(f'ERROR missing={p}')
            return 3
    wav_root_available=os.path.isdir(sfx)
    if not wav_root_available:
        print(f'WAV_SEARCH_ROOT_UNAVAILABLE path={sfx}')

    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml:
        rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    matches=[]; seen=set()
    for s in sorted((x for x in syms if wanted(x)), key=lambda x:(x.addr,x.name)):
        key=(s.addr,s.name)
        if key not in seen:
            seen.add(key); matches.append(s)
    print(f'nmExit={rc} parsedSymbols={len(syms)} mixerTargets={len(matches)}')
    print('\n--- MIXER_TARGET_SYMBOLS ---')
    for s in matches:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not matches:
        print('NO_MIXER_TARGET_SYMBOLS')
        return 4

    for s in matches:
        start=s.addr & ~1
        size=min(s.size or 0x120,0x900)
        stop=start+size
        print(f'\n--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body: print(line)

    wavs=[]
    if wav_root_available:
        for root,_,files in os.walk(sfx):
            for fn in files:
                if fn.lower().endswith('.wav'):
                    wavs.append(os.path.join(root,fn))
    wavs.sort(key=lambda p: os.path.relpath(p,sfx).lower())
    print('\n--- ORIGINAL_WAV_INVENTORY ---')
    print(f'wavCount={len(wavs)}')
    if not wavs:
        print('wavPayloadAvailable=no')
        print('WAV inventory skipped nonfatally: no local WAV payload was found under the supplied search root.')
        print('interpretationRule=native mixer audit remains valid; locate/extract original WAV payload before selecting or validating a playback backend')
        return 0
    sigs=Counter(); failures=[]; total_data=0; total_seconds=0.0
    examples=defaultdict(list)
    for p in wavs:
        rel=os.path.relpath(p,sfx).replace('\\','/')
        w=parse_wav(p)
        if not w['ok']:
            failures.append((rel,w['error']))
            print(f"WAV_FAIL file='{rel}' error={w['error']} bytes={w.get('bytes',0)}")
            continue
        sig=(w['code'],w['channels'],w['rate'],w['bits'],w['align'],w['byte_rate'],w['fmt_size'])
        sigs[sig]+=1
        if len(examples[sig])<8: examples[sig].append(rel)
        total_data+=w['data_bytes']; total_seconds+=w['duration']
        print("WAV file='%s' format=%d channels=%d rate=%d bits=%d align=%d byteRate=%d fmtSize=%d dataBytes=%d duration=%.6f" %
              (rel,w['code'],w['channels'],w['rate'],w['bits'],w['align'],w['byte_rate'],w['fmt_size'],w['data_bytes'],w['duration']))
    print('\n--- WAV_FORMAT_GROUPS ---')
    for sig,count in sorted(sigs.items(), key=lambda kv:(-kv[1],kv[0])):
        code,ch,rate,bits,align,br,fs=sig
        print(f'FORMAT count={count} code={code} channels={ch} rate={rate} bits={bits} align={align} byteRate={br} fmtSize={fs} examples={examples[sig]}')
    print(f'wavValid={sum(sigs.values())} wavInvalid={len(failures)} uniqueFormats={len(sigs)} totalDataBytes={total_data} summedDurationSeconds={total_seconds:.6f}')
    print('pcmOnly=' + ('yes' if sigs and all(sig[0]==1 for sig in sigs) else 'no'))
    print('interpretationRule=do not choose Android playback format/resampler/voice policy until these original WAV signatures and ARMv7 AudioMixer ownership are known')
    return 0 if not failures else 6

if __name__=='__main__':
    raise SystemExit(main())
