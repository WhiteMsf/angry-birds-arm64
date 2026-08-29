#!/usr/bin/env python3
import struct, sys, zlib

PNG_SIG = b'\x89PNG\r\n\x1a\n'

def paeth(a,b,c):
    p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
    if pa <= pb and pa <= pc: return a
    if pb <= pc: return b
    return c

def decode_png(path):
    data=open(path,'rb').read()
    if not data.startswith(PNG_SIG): raise ValueError('not PNG')
    pos=8; ihdr=None; palette=None; trns=None; idat=[]
    while pos+12 <= len(data):
        n=struct.unpack('>I',data[pos:pos+4])[0]; typ=data[pos+4:pos+8]; chunk=data[pos+8:pos+8+n]; pos += 12+n
        if typ==b'IHDR': ihdr=struct.unpack('>IIBBBBB',chunk)
        elif typ==b'PLTE': palette=[tuple(chunk[i:i+3]) for i in range(0,len(chunk),3)]
        elif typ==b'tRNS': trns=chunk
        elif typ==b'IDAT': idat.append(chunk)
        elif typ==b'IEND': break
    if ihdr is None: raise ValueError('IHDR missing')
    w,h,bitdepth,colortype,comp,flt,interlace=ihdr
    if comp!=0 or flt!=0 or interlace!=0: raise ValueError(f'unsupported PNG compression/filter/interlace {comp}/{flt}/{interlace}')
    if bitdepth != 8: raise ValueError(f'unsupported PNG bit depth {bitdepth}; expected 8')
    channels={0:1,2:3,3:1,4:2,6:4}.get(colortype)
    if channels is None: raise ValueError(f'unsupported PNG color type {colortype}')
    raw=zlib.decompress(b''.join(idat))
    stride=w*channels; bpp=channels
    expected=(stride+1)*h
    if len(raw)!=expected: raise ValueError(f'unexpected decompressed size {len(raw)} != {expected}')
    rows=[]; p=0; prev=bytearray(stride)
    for y in range(h):
        ft=raw[p]; p+=1; cur=bytearray(raw[p:p+stride]); p+=stride
        for x in range(stride):
            a=cur[x-bpp] if x>=bpp else 0
            b=prev[x]
            c=prev[x-bpp] if x>=bpp else 0
            if ft==1: cur[x]=(cur[x]+a)&255
            elif ft==2: cur[x]=(cur[x]+b)&255
            elif ft==3: cur[x]=(cur[x]+((a+b)//2))&255
            elif ft==4: cur[x]=(cur[x]+paeth(a,b,c))&255
            elif ft!=0: raise ValueError(f'unsupported filter {ft}')
        rows.append(cur); prev=cur
    rgba=bytearray(w*h*4); o=0
    for row in rows:
        for x in range(w):
            if colortype==6:
                r,g,b,a=row[x*4:x*4+4]
            elif colortype==2:
                r,g,b=row[x*3:x*3+3]; a=255
                if trns and len(trns)>=6:
                    tr,tg,tb=struct.unpack('>HHH',trns[:6])
                    if r==tr and g==tg and b==tb: a=0
            elif colortype==0:
                g=row[x]; r=b=g; a=255
                if trns and len(trns)>=2 and g == struct.unpack('>H',trns[:2])[0]: a=0
            elif colortype==4:
                g,a=row[x*2:x*2+2]; r=b=g
            else:
                idx=row[x]
                if palette is None or idx >= len(palette): raise ValueError('palette index out of range')
                r,g,b=palette[idx]; a=trns[idx] if trns and idx<len(trns) else 255
            rgba[o:o+4]=bytes((r,g,b,a)); o+=4
    return w,h,bytes(rgba)

def main():
    if len(sys.argv)!=3:
        print('usage: png_to_rgba8.py INPUT.png OUTPUT.rgba8', file=sys.stderr); return 2
    w,h,rgba=decode_png(sys.argv[1])
    with open(sys.argv[2],'wb') as f:
        f.write(b'ABR8')
        f.write(struct.pack('<II',w,h))
        f.write(rgba)
    print(f'{sys.argv[1]} -> {sys.argv[2]} {w}x{h} RGBA8 bytes={len(rgba)}')
    return 0
if __name__=='__main__': raise SystemExit(main())
