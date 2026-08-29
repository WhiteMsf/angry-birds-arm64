#!/usr/bin/env python3
import hashlib, pathlib, sys

def fourcc_candidates(data):
    out=[]
    for i in range(0, max(0,len(data)-3)):
        b=data[i:i+4]
        if all(32 <= x < 127 for x in b):
            t=b.decode('ascii','replace')
            if all(c.isupper() or c.isdigit() or c=='_' for c in t):
                out.append((i,t))
    return out

def be32(b): return int.from_bytes(b,'big') if len(b)==4 else None

def audit(path):
    p=pathlib.Path(path); d=p.read_bytes()
    print(f'FILE\t{p.name}\tbytes={len(d)}\tsha256={hashlib.sha256(d).hexdigest()}')
    print('HEADHEX\t'+d[:128].hex())
    print('HEADASCII\t'+''.join(chr(x) if 32<=x<127 else '.' for x in d[:128]))
    print(f'KA3D_OFFSET\t{d.find(b"KA3D")}')
    print(f'SPRT_OFFSET\t{d.find(b"SPRT")}')
    if len(d)>=8: print(f'BE32_AT_4\t{be32(d[4:8])}')
    c=fourcc_candidates(d)
    print('FOURCC_CANDIDATES\t'+','.join(f'{off}:{tag}' for off,tag in c[:64]))
    # length-prefixed printable strings (u16 big endian) are characteristic
    # of KA3D sprite metadata and reveal the actual container cursor.
    hits=[]
    for i in range(len(d)-2):
        n=int.from_bytes(d[i:i+2],'big')
        if 1 <= n <= 96 and i+2+n <= len(d):
            b=d[i+2:i+2+n]
            if all(32<=x<127 for x in b):
                hits.append((i,n,b.decode('ascii')))
    print('U16STRINGS\t'+' | '.join(f'{off}:{n}:{s}' for off,n,s in hits[:80]))
    print()

if len(sys.argv)!=4:
    raise SystemExit('usage: stage24154_scene_dat_container_audit.py <skies.dat> <parallax.dat> <grounds.dat>')
print('ANGRY_STAGE24_15_4_SCENE_DAT_CONTAINER_AUDIT 1')
print('policy=NO_MAGIC_NUMBERS; exact local 1.4.2 bytes only')
for x in sys.argv[1:]: audit(x)
