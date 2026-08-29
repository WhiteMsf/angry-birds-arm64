#!/usr/bin/env python3
from __future__ import annotations
import hashlib, pathlib, sys, zipfile
if len(sys.argv) != 3:
    raise SystemExit('usage: stage24490_make_source_archive.py <source-root> <output.zip>')
root=pathlib.Path(sys.argv[1]).resolve(); out=pathlib.Path(sys.argv[2]).resolve()
exclude_dirs={'.git','b24','vendor','stage24-output','stage24-apk-work','dist','__pycache__'}
forbidden_ext={'.apk','.aab','.jks','.keystore','.p12','.pfx','.pem','.der','.key'}
forbidden_names={'settings.lua','highscores.lua','source-manifest-sha256.txt'}
files=[]
for p in root.rglob('*'):
    if not p.is_file(): continue
    rel=p.relative_to(root)
    if any(part in exclude_dirs for part in rel.parts): continue
    if p.suffix.lower() in forbidden_ext: continue
    if p.name.lower() in forbidden_names: continue
    files.append((rel,p))
out.parent.mkdir(parents=True,exist_ok=True)
manifest=[]
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for rel,p in sorted(files,key=lambda x:str(x[0]).lower()):
        data=p.read_bytes()
        manifest.append(f'{hashlib.sha256(data).hexdigest()}  {rel.as_posix()}')
        info=zipfile.ZipInfo(f'angry-birds-arm64-1.0.0-source/{rel.as_posix()}')
        info.date_time=(2026,8,22,0,0,0)
        info.external_attr=0o644<<16
        info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,data)
    mdata=('ANGRY_BIRDS_ARM64_SOURCE_MANIFEST 1\n'+'\n'.join(manifest)+'\n').encode()
    info=zipfile.ZipInfo('angry-birds-arm64-1.0.0-source/SOURCE-MANIFEST-SHA256.txt')
    info.date_time=(2026,8,22,0,0,0); info.external_attr=0o644<<16; info.compress_type=zipfile.ZIP_DEFLATED
    z.writestr(info,mdata)
print('ANGRY_STAGE24_49_1_SOURCE_ARCHIVE 1')
print(f'files={len(files)}')
print(f'output={out}')
print(f'sha256={hashlib.sha256(out.read_bytes()).hexdigest()}')
