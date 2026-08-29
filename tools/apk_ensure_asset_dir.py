#!/usr/bin/env python3
import pathlib, sys, zipfile

if len(sys.argv) != 4:
    raise SystemExit('usage: apk_ensure_asset_dir.py apk asset_dir apk_prefix')

apk = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2])
prefix = sys.argv[3].strip('/').replace('\\', '/')
if not apk.is_file():
    raise SystemExit(f'APK not found: {apk}')
if not root.is_dir():
    raise SystemExit(f'asset dir not found: {root}')

files = sorted(p for p in root.rglob('*') if p.is_file())
if not files:
    raise SystemExit(f'asset dir is empty: {root}')

with zipfile.ZipFile(apk, 'a', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    names = set(z.namelist())
    added = []
    present = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        arc = f'{prefix}/{rel}' if prefix else rel
        if arc in names:
            present.append(arc)
            continue
        z.write(path, arc)
        names.add(arc)
        added.append(arc)

with zipfile.ZipFile(apk, 'r') as z:
    names = set(z.namelist())
    missing = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        arc = f'{prefix}/{rel}' if prefix else rel
        if arc not in names:
            missing.append(arc)
    if missing:
        raise SystemExit('APK asset verification failed; missing: ' + ', '.join(missing))

print(f'[stage24.13.2b-apk] menu asset verification PASS files={len(files)} already={len(present)} injected={len(added)}')
for arc in added:
    print(f'[stage24.13.2b-apk] injected {arc}')
