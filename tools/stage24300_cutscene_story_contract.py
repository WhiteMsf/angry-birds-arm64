#!/usr/bin/env python3
"""Stage 24.30.0: original cutscene/story subsystem contract audit.

Read-only. Inventories original Lua/corpus ownership, cutscene sprite-sheet
metadata, and ARMv7 native create/release sprite-sheet frontiers. It does not
render or substitute cutscene assets.
"""
from __future__ import annotations
import os, pathlib, re, subprocess, sys

HEADER='ANGRY_STAGE24_30_0_CUTSCENE_STORY_CONTRACT 1'
SCRIPT_NEEDLES=(
    'loadCutScenes','prepareCutScene','releaseCutScenes','createSpriteSheet',
    'getCutsceneBackgroundWidth','theme1Start','introAnimation','MENU_CUTSCENE',
    'CUTSCENES','STORY_BEGIN_','STORY_FLYING_PIGS_','STORY_HIDE_BIRDS_',
)
SYMBOL_TERMS=('createspritesheet','releasespritesheet','luaresources','resources::createsprite','spritesheet')


def run(args):
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                         text=True,errors='replace',check=False)
        return p.returncode,p.stdout.splitlines()
    except Exception as e:
        return -1,[f'exception={e}']


def hits(data:bytes, needle:str):
    out=[]; pos=0; n=needle.encode('ascii')
    while True:
        i=data.find(n,pos)
        if i<0: return out
        out.append(i); pos=i+max(1,len(n))


def ascii_runs(data:bytes,min_len=4):
    start=None
    for i,b in enumerate(data+b'\0'):
        if 32<=b<127:
            if start is None: start=i
        else:
            if start is not None and i-start>=min_len:
                yield start,data[start:i].decode('ascii','replace')
            start=None


def scan_scripts(root:pathlib.Path):
    rows={n:[] for n in SCRIPT_NEEDLES}
    if not root.is_dir(): return rows
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        try:data=p.read_bytes()
        except OSError:continue
        for n in SCRIPT_NEEDLES:
            for off in hits(data,n): rows[n].append((p,off))
    return rows


def main():
    if len(sys.argv)!=7:
        print('usage: stage24300_cutscene_story_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <scripts-root> <image-root> <project-cpp>',file=sys.stderr)
        return 2
    nm,objdump,lib,scripts,image,cpp=sys.argv[1:]
    scripts=pathlib.Path(scripts); image=pathlib.Path(image); cpp=pathlib.Path(cpp)
    print(HEADER)
    print('policy=READ_ONLY; Stage24.30.0 installs audit-only createSpriteSheet/releaseCutScenes probes; no cutscene renderer or fabricated asset is enabled')

    rows=scan_scripts(scripts)
    print('\n[ORIGINAL_SCRIPT_PROVENANCE]')
    for n in SCRIPT_NEEDLES:
        r=rows[n]
        print(f'needle={n!r} hits={len(r)}')
        for p,off in r[:80]:
            try:rel=p.relative_to(scripts)
            except ValueError:rel=p
            print(f'  {rel} offset=0x{off:x}')
        if len(r)>80: print(f'  ... +{len(r)-80} more')

    print('\n[CUTSCENE_METADATA_INVENTORY]')
    dats=sorted([p for p in image.glob('CUTSCENES*.dat') if p.is_file()]) if image.is_dir() else []
    print(f'cutsceneDatCount={len(dats)}')
    total_story=0; total_cutscene=0
    for p in dats:
        try:data=p.read_bytes()
        except OSError as e:
            print(f'file={p.name!r} readError={e}'); continue
        textures=[]; story=[]; cuts=[]
        for off,text in ascii_runs(data,4):
            lo=text.lower()
            if lo.endswith(('.pvr','.png')): textures.append(text)
            if text.startswith('STORY_'): story.append(text)
            if text.startswith('CUTSCENE_'): cuts.append(text)
        story=list(dict.fromkeys(story)); cuts=list(dict.fromkeys(cuts)); textures=list(dict.fromkeys(textures))
        total_story += len(story); total_cutscene += len(cuts)
        print(f'file={p.name!r} bytes={len(data)} textures={";".join(textures) or "-"} storyNames={len(story)} cutsceneNames={len(cuts)}')
        for s in story[:120]: print(f'  STORY {s}')
        for s in cuts[:120]: print(f'  CUTSCENE {s}')
    print(f'totalUniqueWithinFiles.storyEntries={total_story} totalUniqueWithinFiles.cutsceneEntries={total_cutscene}')

    print('\n[ARMV7_NATIVE_SYMBOLS]')
    selected=[]
    if os.path.exists(nm) and os.path.exists(lib):
        rc,lines=run([nm,'-S','-C',lib])
        if rc!=0 or not lines:
            rc,lines=run([nm,'-D','-S','-C',lib])
        for line in lines:
            low=line.lower()
            if any(t in low for t in SYMBOL_TERMS): selected.append(line)
        print(f'nmExit={rc} selected={len(selected)}')
        for line in selected[:300]: print(line)
    else:
        print('nm/lib unavailable')

    # Disassemble direct create/release SpriteSheet candidates when symbol size is available.
    print('\n[ARMV7_TARGETED_DISASSEMBLY]')
    sym_re=re.compile(r'^\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\S\s+(.+)$')
    dumped=0
    for line in selected:
        m=sym_re.match(line)
        if not m: continue
        addr=int(m.group(1),16)&~1; size=int(m.group(2),16); name=m.group(3)
        low=name.lower()
        if 'createspritesheet' not in low and 'releasespritesheet' not in low: continue
        stop=addr+min(max(size,0x40),0x1800)
        rc,body=run([objdump,'-d','--demangle',f'--start-address=0x{addr:x}',f'--stop-address=0x{stop:x}',lib])
        print(f'ARMV7_BODY name={name!r} start=0x{addr:x} size=0x{stop-addr:x} objdumpExit={rc} lines={len(body)}')
        for x in body[:800]: print(x)
        dumped+=1
        if dumped>=12: break
    print(f'targetBodiesDumped={dumped}')

    print('\n[ARMV7_BINARY_STRINGS]')
    if os.path.exists(lib):
        try:data=pathlib.Path(lib).read_bytes()
        except OSError as e:data=b''; print(f'libReadError={e}')
        chosen=[]
        for off,text in ascii_runs(data,4):
            lo=text.lower()
            if any(t in lo for t in ('createspritesheet','releasespritesheet','cutscene','story_','spritesheet')):
                chosen.append((off,text))
        print(f'selected={len(chosen)}')
        for off,text in chosen[:500]: print(f'  offset=0x{off:x} text={text}')

    print('\n[ARM64_SOURCE_GUARDS]')
    text=cpp.read_text(encoding='utf-8',errors='replace') if cpp.is_file() else ''
    checks={
        'createSpriteSheetProbe':'l_res_createSpriteSheet300' in text,
        'releaseCutScenesProbe':'l_stage24300_releaseCutScenes' in text,
        'luaContractDump':'stage24300_dump_cutscene_lua_contract' in text,
        'runtimeMarker':'stage24.30.0-cutscene-runtime' in text,
        'resBinding':'lua_setfield(L, -2, "createSpriteSheet")' in text,
    }
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')

    required=('loadCutScenes','prepareCutScene','createSpriteSheet')
    missing=[n for n in required if not rows[n]]
    if missing:
        print(f'VERDICT=FAIL requiredScriptSymbolsMissing={";".join(missing)}')
        return 3
    if not dats:
        print('VERDICT=FAIL no CUTSCENES*.dat metadata found')
        return 4
    if not all(checks.values()):
        print('VERDICT=FAIL ARM64 audit probe/source guards incomplete')
        return 5
    print('VERDICT=PASS cutscene/story contract frontier inventoried; rendering remains intentionally unimplemented')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
