#!/usr/bin/env python3
import sys, re, struct, zipfile
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit('usage: stage24150_scene_asset_audit.py <imageRoot> <Level1.lua> <Level57.lua>')
root=Path(sys.argv[1]); levels=[Path(sys.argv[2]),Path(sys.argv[3])]
families=('INGAME_SKIES_','INGAME_PARALLAX_','INGAME_GROUNDS_','INGAME_THEME_GROUND_')
print('Stage 24.15.0 exact gameplay-scene asset contract audit')
print('imageRoot='+str(root))

# Conservative printable-string extraction; metadata is not modified or decoded heuristically.
def strings(data, minlen=4):
    return [m.group().decode('ascii','ignore') for m in re.finditer(rb'[ -~]{%d,}'%minlen,data)]

def pvr_header(data):
    if len(data)<52: return None
    vals=struct.unpack_from('<13I',data,0)
    keys=('header','height','width','mipAdditional','flags','dataLength','bpp','rMask','gMask','bMask','aMask','tag','surfaces')
    d=dict(zip(keys,vals)); d['type']=d['flags']&0xff
    return d

def print_pvr(label,data):
    h=pvr_header(data)
    if not h:
        print(f'PVR\t{label}\tINVALID_SHORT\tbytes={len(data)}'); return
    print('PVR\t%s\tbytes=%d\tsize=%dx%d\tmipAdditional=%d\tflags=0x%08x\ttype=0x%02x\tdata=%d\tbpp=%d\tmasks=%08x/%08x/%08x/%08x\ttag=0x%08x\tsurfaces=%d' % (
        label,len(data),h['width'],h['height'],h['mipAdditional'],h['flags'],h['type'],h['dataLength'],h['bpp'],h['rMask'],h['gMask'],h['bMask'],h['aMask'],h['tag'],h['surfaces']))

found=[]
for p in sorted(root.iterdir() if root.exists() else []):
    n=p.name.upper()
    if any(n.startswith(f) for f in families) and (n.endswith('.DAT') or n.endswith('.PVR') or n.endswith('.PVR.ZIP') or n.endswith('.PNG')):
        found.append(p)
print('sceneFiles=%d'%len(found))
for p in found:
    print(f'FILE\t{p.name}\tbytes={p.stat().st_size}')
    u=p.name.upper()
    if u.endswith('.DAT'):
        ss=strings(p.read_bytes())
        refs=[]
        for s in ss:
            if re.search(r'\.(?:pvr|png)$',s,re.I) or any(k in s.upper() for k in ('SKY','PARALLAX','FOREGROUND','GROUND')):
                if s not in refs: refs.append(s)
        for s in refs[:120]: print(f'DATSTR\t{p.name}\t{s}')
    elif u.endswith('.PVR'):
        print_pvr(p.name,p.read_bytes())
    elif u.endswith('.PVR.ZIP'):
        try:
            with zipfile.ZipFile(p,'r') as z:
                entries=[x for x in z.namelist() if x.lower().endswith('.pvr')]
                print(f'ZIP\t{p.name}\tentries={len(entries)}\t'+';'.join(entries))
                for e in entries[:4]: print_pvr(p.name+'!'+e,z.read(e))
        except Exception as e:
            print(f'ZIP\t{p.name}\tERROR={e}')

for lv in levels:
    data=lv.read_bytes()
    ss=strings(data)
    hits=[]
    for s in ss:
        if any(k in s.upper() for k in ('THEMESPRITE','SKY','PARALLAX','FOREGROUND','GROUND','THEME')):
            if s not in hits: hits.append(s)
    print(f'LEVELSTRINGS\t{lv.name}\tbytes={len(data)}\thits={len(hits)}')
    for s in hits[:160]: print(f'LEVELSTR\t{lv.name}\t{s}')
