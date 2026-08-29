#!/usr/bin/env python3
"""Stage 24.19.2 untouched ARMv7 ordinary-contact score ownership audit.

Evidence only. Dumps GameLua::BeginContact in full, inventories score-facing calls
inside that body, and reports raw binary offsets of the relevant Lua keys.
No compatibility implementation is inferred or modified here.
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

def binary_hits(data:bytes, needle:bytes):
    hits=[]; pos=0
    while True:
        i=data.find(needle,pos)
        if i<0: break
        hits.append(i); pos=i+1
    return hits

def main():
    if len(sys.argv)!=4:
        print('usage: stage24192_block_score_ownership.py <llvm-nm> <llvm-objdump> <libangrybirds.so>', file=sys.stderr)
        return 2
    nm,objdump,lib=sys.argv[1:]
    print('ANGRY_STAGE24_19_2_BLOCK_SCORE_OWNERSHIP 1')
    print('policy=DIAGNOSTIC_ONLY; untouched ARMv7 binary; no score mutation')
    print('question=does ordinary GameLua::BeginContact floor(totalActualDamage)*10 own scoreTable.blocks.score?')
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
    cands=[s for s in syms if 'GameLua::BeginContact(' in s.name and s.typ in 'TtWw']
    print(f'beginContactCandidates={len(cands)}')
    for s in cands:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not cands:
        return 4

    # aliases can share an address; dump each unique body once.
    seen=set()
    for s in cands:
        start=s.addr & ~1
        if start in seen: continue
        seen.add(start)
        size=s.size or 0x3000
        stop=start+size
        print()
        print(f'--- BEGINCONTACT_FULL_BODY start=0x{start:x} size=0x{size:x} stop=0x{stop:x} ---')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for line in body:
            print(line)
        print()
        print('--- BEGINCONTACT_SCORE_FACING_CALLS ---')
        focus=re.compile(r'(?i)(floor|__aeabi|__fix|Lua(Table|Object|State)::(get|set|is|to)|setNumber|getNumber|score|blockCollision|birdCollision)')
        for i,line in enumerate(body):
            if re.search(r'\bblx?\b',line) and focus.search(line):
                lo=max(0,i-12); hi=min(len(body),i+18)
                print(f'CALL_CONTEXT line={i}')
                for x in body[lo:hi]: print(x)
                print()

    data=open(lib,'rb').read()
    print('--- RAW_KEY_OFFSETS ---')
    for key in (b'scoreTable\x00',b'blocks\x00',b'score\x00',b'blockCollision\x00',b'birdCollision\x00',b'strength\x00',b'defence\x00'):
        hits=binary_hits(data,key)
        print(f"key={key[:-1].decode('ascii')} hits={len(hits)} offsets=" + ','.join(f'0x{x:x}' for x in hits[:32]))
    print('note=file offsets are ownership landmarks only; inspect PC-relative loads in the body before assigning semantics')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
