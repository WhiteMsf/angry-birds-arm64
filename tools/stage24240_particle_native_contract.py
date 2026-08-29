#!/usr/bin/env python3
import re, subprocess, sys
from pathlib import Path

HEADER = 'ANGRY_STAGE24_24_0_PARTICLE_NATIVE_CONTRACT 1'


def run(cmd):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, errors='replace', check=False)
        return p.returncode, p.stdout.splitlines()
    except Exception as e:
        return -1, [f'exception={e}']


def parse_nm(lines):
    out=[]
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+\S+\s+(.+)$')
    for line in lines:
        m=rx.match(line)
        if not m: continue
        addr=int(m.group(1),16); size=int(m.group(2),16); name=m.group(3)
        out.append((addr,size,name,line))
    return out


def ascii_runs(data, minlen=5):
    start=None
    for i,b in enumerate(data+b'\x00'):
        if 32 <= b < 127:
            if start is None: start=i
        else:
            if start is not None and i-start >= minlen:
                yield start, data[start:i].decode('ascii','replace')
            start=None


def main():
    if len(sys.argv) != 4:
        print('usage: stage24240_particle_native_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so>')
        return 2
    nm, objdump, lib = map(Path, sys.argv[1:])
    print(HEADER)
    print('policy=DIAGNOSTIC_ONLY; no particle simulation/render implementation')
    print(f'lib={lib}')
    if not lib.is_file():
        print('lib=NOT_FOUND')
        return 3

    rc, lines = run([str(nm), '-S', '-C', str(lib)])
    if rc != 0 or not lines:
        rc, lines = run([str(nm), '-D', '-S', '-C', str(lib)])
    print(f'nmExit={rc} nmLines={len(lines)}')
    syms=parse_nm(lines)
    particle_syms=[]
    for item in syms:
        n=item[2]
        low=n.lower()
        if ('particles::' in low or 'particles::' in n or 'particles(' in low or
            'particles' in low and ('lua' in low or 'render' in low or 'update' in low or 'limit' in low) or
            'particlesystem' in low or 'particleview' in low):
            particle_syms.append(item)
    # Deduplicate by address/name and keep manageable.
    seen=set(); filtered=[]
    for item in sorted(particle_syms, key=lambda x:(x[0],x[2])):
        key=(item[0],item[2])
        if key in seen: continue
        seen.add(key); filtered.append(item)
    print(f'particleSymbols={len(filtered)}')
    for addr,size,name,line in filtered:
        print(f'SYMBOL addr=0x{addr:x} size=0x{size:x} name={name}')

    # Prioritize the Angry Birds wrapper class. These are the native owners we
    # need before replacing the headless particles.addParticles boundary.
    priority=[]
    wanted = ('Particles::Particles', 'Particles::setSoftLimit', 'Particles::setHardLimit',
              'Particles::add', 'Particles::update', 'Particles::render',
              'Particles::draw', 'Particles::clear', 'Particles::reset')
    for item in filtered:
        if any(w in item[2] for w in wanted): priority.append(item)
    # If names differ, include all Particles:: owners, capped to avoid giant logs.
    for item in filtered:
        if 'Particles::' in item[2] and item not in priority: priority.append(item)
    priority=priority[:24]
    print(f'disassemblyCandidates={len(priority)}')
    for addr,size,name,_ in priority:
        start=addr & ~1
        if size <= 0: size=0x500
        stop=start+min(size,0x2000)
        print(f'--- DISASM {name} start=0x{start:x} stop=0x{stop:x} ---')
        drc, dump=run([str(objdump), '-d', '--demangle',
                      f'--start-address=0x{start:x}', f'--stop-address=0x{stop:x}', str(lib)])
        print(f'objdumpExit={drc} lines={len(dump)}')
        for line in dump: print(line)

    data=lib.read_bytes()
    words=('particle','maxparticles','softlimit','hardlimit','emitter','spriteelement',
           'lifetime','startvelocity','startposition','endsize','startalpha','endalpha')
    string_hits=[]
    for off,text in ascii_runs(data,5):
        low=text.lower()
        if any(w in low for w in words):
            string_hits.append((off,text))
    print(f'particleStringHits={len(string_hits)}')
    for off,text in string_hits[:300]:
        print(f'STRING offset=0x{off:x} text={text}')
    if len(string_hits)>300: print(f'STRING_TRUNCATED remaining={len(string_hits)-300}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
