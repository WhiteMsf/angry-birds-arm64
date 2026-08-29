#!/usr/bin/env python3
"""Stage 24.25.5 MP3 decode / looping ownership audit.

Static diagnostic only.  It reads untouched ARMv7 symbols and bodies around
AudioReader, AudioClip and AudioMixer to determine where MP3 is decoded,
how decoded data reaches the mixer, and which original method owns EOF/loop
reset.  No replacement decoder is selected here.
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

def body(objdump,lib,s,max_bytes=0x1800):
    start=s.addr & ~1
    size=min(s.size or 0x100,max_bytes)
    stop=start+size
    rc,lines=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
    return rc,lines,start,stop

def calls(lines):
    # llvm-objdump branch/call annotations: bl 0x... <demangled name>
    out=[]
    for ln in lines:
        if re.search(r'\bblx?\b',ln):
            m=re.search(r'<([^>]+)>',ln)
            if m: out.append(m.group(1))
    seen=[]
    for x in out:
        if x not in seen: seen.append(x)
    return seen

def main():
    if len(sys.argv)!=4:
        print('usage: stage24255_mp3_decode_loop_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so>',file=sys.stderr)
        return 2
    nm,objdump,lib=sys.argv[1:]
    print('ANGRY_STAGE24_25_5_MP3_DECODE_LOOP_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; untouched ARMv7 ownership; no MP3 backend selected')
    print('questions=AudioReader MP3 output contract; reset/EOF ownership; AudioMixer read path; loop ownership; clip/mixer state')
    print(f'lib={lib}')
    for p in (nm,objdump,lib):
        if not os.path.exists(p): print(f'ERROR missing={p}'); return 3
    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml: rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')

    exact_names={
      'audio::AudioReader::readData(void*, int, int)',
      'audio::AudioReader::reset(io::InputStream*, io::FileFormat, audio::AudioConfiguration const&)',
      'audio::AudioReader::readData_mp3(void*, int, int)',
      'audio::AudioReader::deinit_mp3()',
      'audio::AudioReader::readHeader_mp3()',
      'audio::AudioReader::init_mp3()',
      'audio::AudioReader::readData_wav(void*, int, int)',
      'audio::AudioReader::readHeader_wav()',
      'audio::AudioMixer::mixUnlimited8(audio::AudioConfiguration const&, void*, int)',
      'audio::AudioMixer::mixUnlimited16(audio::AudioConfiguration const&, void*, int)',
      'audio::AudioMixer::mixUnlimited8to16(audio::AudioConfiguration const&, void*, int)',
      'audio::AudioMixer::playClip(audio::AudioClip*, float, bool, int)',
    }
    # Include constructors/destructors and all small public format accessors so
    # field layout can be inferred from untouched ldr/str offsets.
    def wanted(s):
        n=s.name
        if n in exact_names: return True
        if n.startswith('audio::AudioReader::'):
            return any(k in n for k in ('AudioReader(', '~AudioReader', 'audioFormat()', 'channels()', 'sampleRate()', 'byteRate()', 'blockAlign()', 'bitsPerSample()', 'dataSize()', 'readFully('))
        if n.startswith('audio::AudioClip::'):
            return True
        if n.startswith('audio::AudioMixer::') and any(k in n for k in ('mix','playClip','stopClip','isClipPlaying')):
            return True
        return False
    targets=[s for s in sorted(syms,key=lambda x:(x.addr,x.name)) if s.typ in 'TtWw' and wanted(s)]
    print('\n--- TARGET_SYMBOLS ---')
    for s in targets: print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    print('\n--- CALL_GRAPH_SUMMARY ---')
    bodies={}
    for s in targets:
        rc2,ls,start,stop=body(objdump,lib,s,0x1800)
        bodies[(s.addr,s.name)]=(rc2,ls,start,stop)
        cs=calls(ls)
        if cs:
            print(f'CALLER name={s.name!r}')
            for c in cs: print(f'  -> {c}')

    # Machine-readable relationships that matter for a faithful replacement.
    def find_body(name):
        for s in targets:
            if s.name==name: return s,bodies[(s.addr,s.name)]
        return None,None
    mix_names=[n for n in exact_names if 'AudioMixer::mixUnlimited' in n]
    mix_calls_read=False; mix_calls_reset=False
    for n in mix_names:
        s,b=find_body(n)
        if b:
            txt='\n'.join(b[1])
            mix_calls_read |= 'AudioReader::readData(' in txt
            mix_calls_reset |= 'AudioReader::reset(' in txt
    s,b=find_body('audio::AudioReader::readData(void*, int, int)')
    dispatch_mp3=False
    if b: dispatch_mp3='AudioReader::readData_mp3' in '\n'.join(b[1])
    s,b=find_body('audio::AudioReader::reset(io::InputStream*, io::FileFormat, audio::AudioConfiguration const&)')
    reset_init_mp3=reset_header_mp3=False
    if b:
        txt='\n'.join(b[1]); reset_init_mp3='AudioReader::init_mp3' in txt; reset_header_mp3='AudioReader::readHeader_mp3' in txt
    s,b=find_body('audio::AudioMixer::playClip(audio::AudioClip*, float, bool, int)')
    play_has_bool_logic=False
    if b:
        # bool loop arrives as the third C++ argument; this is intentionally a
        # conservative marker only: body is still printed for manual review.
        txt='\n'.join(b[1]); play_has_bool_logic=('cmp' in txt and len(b[1])>20)
    print('\n--- MACHINE_MARKERS ---')
    print(f'READ_DATA_DISPATCH mp3Branch={str(dispatch_mp3).lower()}')
    print(f'MIXER_READ_PATH callsAudioReaderReadData={str(mix_calls_read).lower()} callsAudioReaderReset={str(mix_calls_reset).lower()}')
    print(f'RESET_MP3_PATH callsInitMp3={str(reset_init_mp3).lower()} callsReadHeaderMp3={str(reset_header_mp3).lower()}')
    print(f'PLAYCLIP_LOOP_ARGUMENT bodyContainsControlFlow={str(play_has_bool_logic).lower()} reviewBody=true')

    # Print full relevant bodies. readHeader_mp3 is ~0xa84 in the original;
    # 0x1800 cap is deliberately large enough to include it whole.
    print('\n--- DISASSEMBLY ---')
    priority=[]
    order=[
      'audio::AudioReader::reset(io::InputStream*, io::FileFormat, audio::AudioConfiguration const&)',
      'audio::AudioReader::readData(void*, int, int)',
      'audio::AudioReader::init_mp3()', 'audio::AudioReader::readHeader_mp3()',
      'audio::AudioReader::readData_mp3(void*, int, int)', 'audio::AudioReader::deinit_mp3()',
      'audio::AudioMixer::playClip(audio::AudioClip*, float, bool, int)',
      'audio::AudioMixer::mixUnlimited16(audio::AudioConfiguration const&, void*, int)',
      'audio::AudioMixer::mixUnlimited8to16(audio::AudioConfiguration const&, void*, int)',
      'audio::AudioMixer::mixUnlimited8(audio::AudioConfiguration const&, void*, int)',
    ]
    byname={s.name:s for s in targets}
    for n in order:
        if n in byname: priority.append(byname[n])
    for s in targets:
        if s not in priority and (s.name.startswith('audio::AudioClip::') or 'AudioReader::AudioReader(' in s.name): priority.append(s)
    seen=set()
    for s in priority:
        k=(s.addr,s.name)
        if k in seen: continue
        seen.add(k)
        rc2,ls,start,stop=bodies[k]
        print(f'\nARMV7_BODY name={s.name!r} start=0x{start:x} size=0x{stop-start:x} stop=0x{stop:x} objdumpExit={rc2} lines={len(ls)}')
        for ln in ls: print(ln)

    print('\ninterpretationRule=do not infer loop/reset semantics from Android APIs; use the untouched AudioMixer/AudioReader call graph and bodies above')
    print('implementationGate=MP3 playback may be implemented only after EOF/readData/reset/loop ownership is resolved from this report')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
