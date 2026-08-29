#!/usr/bin/env python3
import hashlib, os, re, struct, sys
from pathlib import Path

if len(sys.argv) != 2:
    print('usage: stage24160_presentation_tree_audit.py <data-root>', file=sys.stderr)
    raise SystemExit(2)
root = Path(sys.argv[1])
if not root.is_dir():
    print(f'ERROR\tdata-root-missing\t{root}', file=sys.stderr)
    raise SystemExit(3)

print('ANGRY_STAGE24_16_0_ASSET_PROFILE_CONTRACT 1')
print(f'dataRoot={root}')
print('policy=inventory-only; no inferred viewport; no magic numbers')

res_re = re.compile(r'^(\d+)x(\d+)(?:_|$)', re.I)

def list_profiles(parent: Path, kind: str):
    print(f'--- {kind.upper()} PROFILE DIRECTORIES ---')
    if not parent.is_dir():
        print(f'{kind}\tMISSING\t{parent}')
        return
    for d in sorted((p for p in parent.iterdir() if p.is_dir()), key=lambda p:p.name.lower()):
        m=res_re.match(d.name)
        if m:
            w,h=map(int,m.groups())
            ratio=(w/h) if h else 0.0
            files=sum(1 for p in d.iterdir() if p.is_file())
            print(f'{kind}\t{d.name}\t{w}x{h}\taspect={ratio:.9f}\tfiles={files}')
        else:
            print(f'{kind}\t{d.name}\tUNPARSED\tfiles={sum(1 for p in d.iterdir() if p.is_file())}')

list_profiles(root/'images','image')
list_profiles(root/'fonts','font')

keywords=[
    b'screenWidth', b'screenHeight', b'selectAssetProfile', b'selectFontProfile',
    b'initCameras', b'levelStartCamera', b'doItAllCamera', b'defaultCamera',
    b'repositionScreen', b'480x320', b'864x480', b'320x240', b'800x480', b'854x480'
]
print('--- LUA / CONFIG KEYWORD OWNERS ---')
for p in sorted(root.rglob('*')):
    if not p.is_file() or p.suffix.lower() not in {'.lua','.txt','.xml','.cfg','.ini'}:
        continue
    try:
        data=p.read_bytes()
    except OSError:
        continue
    hits=[k.decode('ascii') for k in keywords if k in data]
    if hits:
        rel=p.relative_to(root)
        sha=hashlib.sha256(data).hexdigest()
        print(f'OWNER\t{rel}\tbytes={len(data)}\tsha256={sha}\thits={",".join(hits)}')

print('--- RELEVANT ORIGINAL FILES ---')
for name in ('select_profiles.lua','gamelogic.lua','loadlist.lua','blocks.lua'):
    found=sorted(root.rglob(name))
    if not found:
        print(f'FILE\t{name}\tNOT_FOUND')
    for p in found:
        data=p.read_bytes()
        print(f'FILE\t{p.relative_to(root)}\tbytes={len(data)}\tsha256={hashlib.sha256(data).hexdigest()}')

print('--- INGAME FAMILY BY IMAGE PROFILE ---')
for d in sorted((p for p in (root/'images').iterdir() if p.is_dir()), key=lambda p:p.name.lower()) if (root/'images').is_dir() else []:
    present=[]
    for stem in ('INGAME_SKIES_1','INGAME_PARALLAX_1','INGAME_GROUNDS_1','INGAME_THEME_GROUND_1'):
        exts=[x.suffix.lower() for x in d.glob(stem+'.*') if x.is_file()]
        if exts:
            present.append(stem+':'+'/'.join(sorted(set(exts))))
    if present:
        print(f'INGAME\t{d.name}\t'+'\t'.join(present))
