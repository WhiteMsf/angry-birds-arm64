#!/usr/bin/env python3
from __future__ import annotations
import hashlib, pathlib, re, shutil, struct, sys, zipfile

if len(sys.argv) != 4:
    print('usage: stage24481_find_original_launcher_icon.py <angry-re-root> <downloads-root> <output-png>', file=sys.stderr)
    raise SystemExit(2)

root = pathlib.Path(sys.argv[1]).resolve()
downloads = pathlib.Path(sys.argv[2]).resolve()
out = pathlib.Path(sys.argv[3]).resolve()

# The source archive must remain asset-free. This helper locates the user's own
# launcher icon at build time from either an extracted APK tree or the original
# APK adjacent to that tree.
NAME_SCORE = {
    'icon.png': 100,
    'ic_launcher.png': 95,
    'app_icon.png': 90,
    'angrybirds.png': 80,
    'angry_birds.png': 80,
}
DENSITY_SCORE = {'xxxhdpi': 60, 'xxhdpi': 50, 'xhdpi': 40, 'hdpi': 30, 'mdpi': 20, 'ldpi': 10}

def png_size(data: bytes):
    if len(data) >= 24 and data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR':
        return struct.unpack('>II', data[16:24])
    return (0,0)

def score_path(path: str, data: bytes):
    p = path.replace('\\','/').lower()
    name = p.rsplit('/',1)[-1]
    if not re.search(r'(^|/)res/(drawable|mipmap)[^/]*/', p):
        return None
    base = NAME_SCORE.get(name)
    if base is None:
        if 'icon' not in name or not name.endswith('.png'):
            return None
        base = 45
    den = 0
    for k,v in DENSITY_SCORE.items():
        if k in p:
            den = max(den,v)
    w,h = png_size(data)
    if not w or not h:
        return None
    # Prefer actual icon-like square images and then the largest retained density.
    square = 25 if abs(w-h) <= 2 else 0
    area_bonus = min((w*h)//1024, 100)
    return base + den + square + area_bonus, w, h

candidates=[]
if root.exists():
    for f in root.rglob('*.png'):
        try:
            data=f.read_bytes()
        except OSError:
            continue
        sc=score_path(str(f.relative_to(root)),data)
        if sc:
            candidates.append((sc[0],sc[1],sc[2],f'file:{f}',data))

apk_paths=[]
if root.exists():
    apk_paths.extend(root.rglob('*.apk'))
if downloads.exists():
    for f in downloads.glob('*.apk'):
        n=f.name.lower()
        if 'angry' in n or 'rovio' in n:
            apk_paths.append(f)
seen=set()
for apk in apk_paths:
    try:
        key=str(apk.resolve()).lower()
    except OSError:
        key=str(apk).lower()
    if key in seen: continue
    seen.add(key)
    try:
        with zipfile.ZipFile(apk) as z:
            for name in z.namelist():
                if not name.lower().endswith('.png'):
                    continue
                try: data=z.read(name)
                except Exception: continue
                sc=score_path(name,data)
                if sc:
                    candidates.append((sc[0]+5,sc[1],sc[2],f'apk:{apk}!/{name}',data))
    except (OSError, zipfile.BadZipFile):
        pass

if not candidates:
    print('ERROR: original launcher icon not found.', file=sys.stderr)
    print(f'Searched extracted resources under: {root}', file=sys.stderr)
    print(f'Also searched top-level Angry/Rovio APKs under: {downloads}', file=sys.stderr)
    print('Keep the original APK in Downloads or preserve its res/drawable*/icon.png under angry-re.', file=sys.stderr)
    raise SystemExit(1)

candidates.sort(key=lambda x:(x[0],x[1]*x[2]),reverse=True)
score,w,h,source,data=candidates[0]
out.parent.mkdir(parents=True,exist_ok=True)
out.write_bytes(data)
sha=hashlib.sha256(data).hexdigest()
print('ANGRY_STAGE24_48_1_ORIGINAL_LAUNCHER_ICON 1')
print(f'source={source}')
print(f'width={w}')
print(f'height={h}')
print(f'bytes={len(data)}')
print(f'sha256={sha}')
print(f'candidateCount={len(candidates)}')
print('verdict=PASS_ORIGINAL_LOCAL_ASSET')
