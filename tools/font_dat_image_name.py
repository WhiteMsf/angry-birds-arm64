#!/usr/bin/env python3
import sys, struct
from pathlib import Path

def be16(b,p): return struct.unpack_from('>H',b,p)[0], p+2
def be32(b,p): return struct.unpack_from('>I',b,p)[0], p+4

def mutf8(b,p,end):
    n,p=be16(b,p)
    if p+n>end: raise ValueError('readUTF beyond chunk')
    raw=b[p:p+n]; p+=n
    # Font image names are ASCII in the period assets. Decode modified UTF-8
    # permissively enough to preserve any non-ASCII path if one appears.
    out=[]; i=0
    while i<len(raw):
        a=raw[i]; i+=1
        if a<0x80: cp=a
        elif a&0xE0==0xC0:
            if i>=len(raw): raise ValueError('bad mutf8')
            q=raw[i]; i+=1; cp=((a&0x1f)<<6)|(q&0x3f)
        elif a&0xF0==0xE0:
            if i+1>=len(raw): raise ValueError('bad mutf8')
            q,r=raw[i],raw[i+1]; i+=2; cp=((a&0xf)<<12)|((q&0x3f)<<6)|(r&0x3f)
        else: raise ValueError('bad mutf8 lead')
        out.append(chr(cp))
    return ''.join(out),p

def parse(path):
    b=Path(path).read_bytes(); end=len(b)
    if end<4: raise ValueError('too small')
    p=0; magic,p=be32(b,p)
    KA3D=int.from_bytes(b'KA3D','big'); FONT=int.from_bytes(b'FONT','big')
    if magic!=KA3D:
        name,_=mutf8(b,0,end); return name
    declared,p=be32(b,p)
    while p+8<=end:
        cid,p=be32(b,p); ln,p=be32(b,p); cend=p+ln
        if cend>end: raise ValueError('chunk exceeds file')
        if cid==FONT:
            version,p2=be16(b,p)
            if version!=1: raise ValueError(f'FONT version {version}')
            name,_=mutf8(b,p2,cend); return name
        p=cend
    raise ValueError('FONT chunk not found')

if __name__=='__main__':
    if len(sys.argv)!=2:
        print('usage: font_dat_image_name.py FONT.dat',file=sys.stderr); sys.exit(2)
    try:
        print(parse(sys.argv[1]))
    except Exception as e:
        print(f'ERROR: {e}',file=sys.stderr); sys.exit(1)
