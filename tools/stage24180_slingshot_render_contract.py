#!/usr/bin/env python3
"""Stage 24.18.0 original slingshot/resource render contract audit.

Read-only audit against the untouched ARMv7 libangrybirds.so and the user's
1.4.2 data tree.  It intentionally does not invent sprite names, offsets,
geometry, draw order or rubber-band rendering.
"""
from __future__ import annotations
import os, re, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

@dataclass
class Sym:
    addr:int; size:int; typ:str; name:str

def run(args:list[str]):
    p=subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     text=True, errors='replace')
    return p.returncode, p.stdout.splitlines()

def parse_nm(lines:Iterable[str]):
    out=[]; rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    for ln in lines:
        m=rx.match(ln)
        if m: out.append(Sym(int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(4)))
    return out

def printable_strings(data:bytes, minlen:int=4):
    rx=re.compile(rb'[\x20-\x7e]{%d,}'%minlen)
    for m in rx.finditer(data):
        yield m.start(), m.group().decode('ascii','replace')

def function_blocks(lines:list[str]):
    hdr=re.compile(r'^\s*([0-9A-Fa-f]+)\s+<(.+)>:\s*$')
    hs=[]
    for i,ln in enumerate(lines):
        m=hdr.match(ln)
        if m: hs.append((i,int(m.group(1),16),m.group(2)))
    out=[]
    for j,(i,a,n) in enumerate(hs):
        e=hs[j+1][0] if j+1<len(hs) else len(lines)
        out.append((i,e,a,n))
    return out

def main():
    if len(sys.argv)!=5:
        print('usage: stage24180_slingshot_render_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <dataRoot>',file=sys.stderr); return 2
    nm,objdump,lib,data_root=sys.argv[1:]
    print('ANGRY_STAGE24_18_0_SLINGSHOT_RENDER_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; NO guessed sprite names/offsets/geometry; untouched ARMv7 + local 1.4.2 assets')
    print(f'lib={lib}'); print(f'dataRoot={data_root}')
    for p in (nm,objdump,lib,data_root):
        if not os.path.exists(p): print(f'ERROR missing={p}'); return 3

    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml: rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')
    relrx=re.compile(r'(?i)(GameLua::drawGame|slingshot|sling|rubber|resource|Sprite|Image::render|drawSprite|Particles::draw)')
    rel=[s for s in syms if relrx.search(s.name)]
    print(f'\n--- RELATED_SYMBOLS count={len(rel)} capped=500 ---')
    for s in rel[:500]: print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    dg=next((s for s in syms if s.name=='GameLua::drawGame()' and s.typ in 'TtWw'),None)
    if not dg:
        dg=next((s for s in syms if 'GameLua::drawGame()' in s.name and s.typ in 'TtWw'),None)
    print('\n--- DRAWGAME_BODY ---')
    if dg:
        st=dg.addr & ~1; sz=dg.size or 0x1200; sp=st+sz
        print(f'symbol={dg.name} start=0x{st:x} size=0x{sz:x} stop=0x{sp:x}')
        drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{st:x}',f'--stop-address=0x{sp:x}',lib])
        print(f'objdumpExit={drc} lines={len(body)}')
        for ln in body: print(ln)
        print('\n--- DRAWGAME_CALL_SEQUENCE ---')
        callrx=re.compile(r'\bblx?\b')
        calls=[(i,ln) for i,ln in enumerate(body) if callrx.search(ln)]
        print(f'calls={len(calls)}')
        for k,(i,ln) in enumerate(calls):
            print(f'CALL[{k:03d}] bodyLine={i:04d} {ln}')
        # Capture larger contexts around calls that are resource/sprite/image oriented.
        focus=re.compile(r'(?i)(Sprite|Image|Resource|render\(|Particles::draw|MaskedImage|setWorld|Matrix|Texture)')
        print('\n--- DRAWGAME_RESOURCE_CALL_CONTEXTS ---')
        hits=0
        for i,ln in calls:
            if not focus.search(ln): continue
            hits+=1
            print(f'\nFOCUS[{hits}] call={ln}')
            for x in body[max(0,i-18):min(len(body),i+22)]: print(x)
        print(f'focusCalls={hits}')
    else:
        print('drawGame=NOT_FOUND')

    # Binary strings: exact names are evidence, not guesses.
    data=Path(lib).read_bytes()
    keyrx=re.compile(r'(?i)(sling|rubber|catapult|band|shoot|launch)')
    bmatches=[(o,s) for o,s in printable_strings(data) if keyrx.search(s)]
    print(f'\n--- ARMV7_BINARY_KEYWORD_STRINGS count={len(bmatches)} ---')
    for o,s in bmatches[:1000]: print(f'0x{o:08x}\t{s}')

    # Asset tree: filenames and embedded DAT/COMP strings containing sling-like terms.
    root=Path(data_root); image=root/'images'/'864x480'
    files=list(image.rglob('*')) if image.exists() else []
    namehits=[p for p in files if p.is_file() and keyrx.search(p.name)]
    print(f'\n--- ASSET_FILENAME_HITS root={image} count={len(namehits)} ---')
    for p in namehits[:500]: print(f'FILE\t{p.relative_to(root)}\tbytes={p.stat().st_size}')

    print('\n--- ASSET_METADATA_STRING_HITS ---')
    mh=0
    metadata=[p for p in files if p.is_file() and p.suffix.lower() in ('.dat','.lua','.txt')]
    for p in metadata:
        try: raw=p.read_bytes()
        except OSError: continue
        ss=[(o,s) for o,s in printable_strings(raw) if keyrx.search(s)]
        if not ss: continue
        mh+=1
        print(f'\nMETA\t{p.relative_to(root)}\tbytes={len(raw)}\thits={len(ss)}')
        # Also expose neighboring strings; sprite sheets often place texture name and sprites adjacently.
        allss=list(printable_strings(raw))
        idx={o:i for i,(o,_) in enumerate(allss)}
        shown=set()
        for o,s in ss:
            i=idx.get(o,0)
            for j in range(max(0,i-3),min(len(allss),i+4)):
                oo,tt=allss[j]
                if (oo,tt) in shown: continue
                shown.add((oo,tt)); print(f'  STR\t0x{oo:06x}\t{tt}')
    print(f'metadataFilesWithHits={mh}')

    # Gamelogic/loadlist raw printable names around sling/rubber globals.
    print('\n--- LUA_CONFIG_STRING_HITS ---')
    for rp in ('scripts/gamelogic.lua','scripts/loadlist.lua','scripts/blocks.lua'):
        p=root/rp
        if not p.exists(): continue
        raw=p.read_bytes(); alls=list(printable_strings(raw)); hits=[(o,s) for o,s in alls if keyrx.search(s)]
        print(f'FILE\t{rp}\tbytes={len(raw)}\thits={len(hits)}')
        for o,s in hits[:500]: print(f'  0x{o:08x}\t{s}')

    print('\n--- AUDIT_CONCLUSION_GUARD ---')
    print('implementationDecision=DEFERRED_UNTIL_REPORT_REVIEW')
    print('requiredEvidence=exact resource/sprite owners + exact drawGame call/transform branch + rubber geometry owner')
    return 0

if __name__=='__main__': raise SystemExit(main())
