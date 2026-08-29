#!/usr/bin/env python3
"""Stage 24.31.4d — original atlas edge / blit / blend contract audit.

Read-only. 24.31.4a recovered edge-to-edge EGL_Image UVs; 24.31.4b/c
recovered the physical POT texture backing and sampler.  Since seams remain
with those canonical semantics, this pass asks what still differs:
  * are sprite borders padded/extruded in the untouched atlas pixels?
  * does EGL_Texture::blt / EGL_Image::blt transform alpha or edge pixels?
  * what blend function/state does the ARMv7 renderer actually use?
  * does SpriteSheet::drawSprite adjust the DAT source rectangle before Image::draw?
No renderer fix is selected by this report.
"""
from __future__ import annotations
import pathlib, re, struct, subprocess, sys, zlib
from dataclasses import dataclass

HEADER='ANGRY_STAGE24_31_4D_ORIGINAL_ATLAS_BLIT_BLEND_CONTRACT 1'

@dataclass
class Sym:
    addr:int; size:int; typ:str; name:str

def run(args):
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace',check=False)
        return p.returncode,p.stdout.splitlines()
    except Exception as e:
        return -1,[f'exception={e}']

def parse_nm(lines):
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    out=[]
    for ln in lines:
        m=rx.match(ln)
        if m: out.append(Sym(int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(4)))
    return out

def ca(s): return s.addr & ~1

def containing(syms,addr):
    cand=[s for s in syms if ca(s)<=addr<ca(s)+max(s.size,1)]
    return max(cand,key=lambda s:ca(s)) if cand else None

def disasm(objdump,lib,s,max_size=0x1400):
    st=ca(s); sz=min(max(s.size or 0x100,0x40),max_size)
    rc,lines=run([objdump,'-d','--demangle',f'--start-address=0x{st:x}',f'--stop-address=0x{st+sz:x}',lib])
    return rc,st,sz,lines

def be16(d,p): return (d[p]<<8)|d[p+1]
def si16(v): return v-65536 if v&0x8000 else v

def parse_dat(path:pathlib.Path):
    d=path.read_bytes(); sprt=d.find(b'SPRT')
    if sprt < 0 or sprt+8>len(d): return []
    p=sprt+8
    def u16():
        nonlocal p
        if p+2>len(d): raise ValueError('eof u16')
        v=be16(d,p); p+=2; return v
    def i16(): return si16(u16())
    def s16():
        nonlocal p
        n=u16()
        if p+n>len(d): raise ValueError('eof str')
        s=d[p:p+n].decode('latin1','replace'); p+=n; return s
    try:
        nt=u16(); textures=[s16() for _ in range(nt)]; ns=u16(); out=[]
        for _ in range(ns):
            name=s16(); x,y,w,h,px,py=[i16() for _ in range(6)]
            tex=textures[0] if len(textures)==1 else ''
            out.append((name,tex,x,y,w,h,px,py,path.name))
        return out
    except Exception:
        return []

PNG_SIG=b'\x89PNG\r\n\x1a\n'
def decode_png(path:pathlib.Path):
    data=path.read_bytes()
    if not data.startswith(PNG_SIG): raise ValueError('not png')
    pos=8; ih=None; pal=None; trns=None; chunks=[]
    while pos+12<=len(data):
        n=struct.unpack('>I',data[pos:pos+4])[0]; typ=data[pos+4:pos+8]; c=data[pos+8:pos+8+n]; pos+=12+n
        if typ==b'IHDR': ih=struct.unpack('>IIBBBBB',c)
        elif typ==b'PLTE': pal=[tuple(c[i:i+3]) for i in range(0,len(c),3)]
        elif typ==b'tRNS': trns=c
        elif typ==b'IDAT': chunks.append(c)
        elif typ==b'IEND': break
    if not ih: raise ValueError('no ihdr')
    w,h,bd,ct,comp,flt,inter=ih
    if bd!=8 or comp or flt or inter: raise ValueError(f'unsupported png {bd}/{ct}/{comp}/{flt}/{inter}')
    ch={0:1,2:3,3:1,4:2,6:4}[ct]; raw=zlib.decompress(b''.join(chunks)); stride=w*ch
    rows=[]; q=0; prev=bytearray(stride)
    def paeth(a,b,c):
        p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
        return a if pa<=pb and pa<=pc else (b if pb<=pc else c)
    for _ in range(h):
        ft=raw[q]; q+=1; cur=bytearray(raw[q:q+stride]); q+=stride
        for i in range(stride):
            a=cur[i-ch] if i>=ch else 0; b=prev[i]; c=prev[i-ch] if i>=ch else 0
            if ft==1: cur[i]=(cur[i]+a)&255
            elif ft==2: cur[i]=(cur[i]+b)&255
            elif ft==3: cur[i]=(cur[i]+((a+b)//2))&255
            elif ft==4: cur[i]=(cur[i]+paeth(a,b,c))&255
            elif ft!=0: raise ValueError('png filter')
        rows.append(cur); prev=cur
    pix=[]
    for row in rows:
        rr=[]
        for x in range(w):
            if ct==6: r,g,b,a=row[x*4:x*4+4]
            elif ct==2: r,g,b=row[x*3:x*3+3]; a=255
            elif ct==4: g,a=row[x*2:x*2+2]; r=b=g
            elif ct==0: g=row[x]; r=b=g; a=255
            else:
                idx=row[x]; r,g,b=pal[idx]; a=trns[idx] if trns and idx<len(trns) else 255
            rr.append((r,g,b,a))
        pix.append(rr)
    return w,h,pix,'PNG_RGBA8'

def decode_pvr(path:pathlib.Path):
    d=path.read_bytes()
    if len(d)<52: raise ValueError('short pvr')
    hdr=struct.unpack_from('<13I',d,0); hl,h,w,mips,flags,dl,bpp,rm,gm,bm,am,tag,surf=hdr
    if hl!=52 or tag!=0x21525650 or mips!=0 or surf!=1: raise ValueError('unsupported pvr topology')
    typ=flags&0xff; payload=d[52:]
    if typ==0x10 and bpp==16:
        pix=[]
        for y in range(h):
            rr=[]
            for x in range(w):
                i=2*(y*w+x); v=payload[i]|(payload[i+1]<<8)
                rr.append((((v>>12)&15)*17,((v>>8)&15)*17,((v>>4)&15)*17,(v&15)*17))
            pix.append(rr)
        return w,h,pix,'PVR_RGBA4444'
    if typ==0x13 and bpp==16:
        pix=[]
        for y in range(h):
            rr=[]
            for x in range(w):
                i=2*(y*w+x); v=payload[i]|(payload[i+1]<<8)
                r=((v>>11)&31)*255//31; g=((v>>5)&63)*255//63; b=(v&31)*255//31
                rr.append((r,g,b,255))
            pix.append(rr)
        return w,h,pix,'PVR_RGB565'
    raise ValueError(f'unsupported pvr typ=0x{typ:x} bpp={bpp} mips={mips}')

def edge_stats(pix,W,H,x,y,w,h):
    # DAT y convention is intentionally tested both ways. Return metrics for direct
    # row origin and vertically mirrored origin; do not silently choose one.
    outs=[]
    for mode,yy in [('direct',y),('flip',H-y-h)]:
        if x<0 or yy<0 or w<=0 or h<=0 or x+w>W or yy+h>H: continue
        sides=[]
        specs=[('L',[(x,yy+j,x-1,yy+j) for j in range(h) if x>0]),
               ('R',[(x+w-1,yy+j,x+w,yy+j) for j in range(h) if x+w<W]),
               ('T',[(x+i,yy,x+i,yy-1) for i in range(w) if yy>0]),
               ('B',[(x+i,yy+h-1,x+i,yy+h) for i in range(w) if yy+h<H])]
        for sn,pairs in specs:
            if not pairs: continue
            eq=zero=nonzero=rgb_same_alpha_diff=0; n=len(pairs)
            ain=aout=0
            for ix,iy,ox,oy in pairs:
                a=pix[iy][ix]; b=pix[oy][ox]
                eq += a==b; zero += b[3]==0; nonzero += b[3]>0; ain+=a[3]; aout+=b[3]
                rgb_same_alpha_diff += (a[:3]==b[:3] and a[3]!=b[3])
            sides.append((sn,n,eq/n,zero/n,nonzero/n,ain/n,aout/n,rgb_same_alpha_diff/n))
        outs.append((mode,sides))
    return outs

def main():
    if len(sys.argv)!=6:
        print('usage: tool <llvm-nm> <llvm-objdump> <armv7-lib> <images-dir> <project-cpp>',file=sys.stderr); return 2
    nm,objdump,lib,imgdir,cpp=sys.argv[1:]
    root=pathlib.Path(imgdir); src=pathlib.Path(cpp).read_text(encoding='utf-8',errors='replace')
    print(HEADER)
    print('policy=READ_ONLY_NO_RENDER_FIX')
    print('known=31.4a edge-to-edge UV; 31.4b/c POT backing + LINEAR sampler restored; user still observes seams')
    print('question=Do untouched atlas pixels, blit/alpha conversion, blend state, or SpriteSheet source-rect delegation explain why ARMv7 is seam-free?')

    rc,nml=run([nm,'-S','-C',lib]);
    if rc!=0 or not nml: rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml); print(f'nmExit={rc} parsedSymbols={len(syms)}')
    targets=[]
    needles=('SpriteSheet::drawSprite(','EGL_Texture::blt(','EGL_Image::blt(','getGLFormat(','EGL_Shader_Default::begin(','EGL_Texture::allocate(')
    for s in syms:
        if any(n in s.name for n in needles): targets.append(s)
    print(f'\n[TARGET_SYMBOLS] count={len(targets)}')
    for s in targets: print(f'addr=0x{ca(s):08x} size=0x{s.size:x} name={s.name!r}')
    for s in targets:
        dr,st,sz,ls=disasm(objdump,lib,s)
        print(f'\n[BODY] name={s.name!r} start=0x{st:x} size=0x{sz:x} exit={dr}')
        for ln in ls: print(ln)

    drc,all_dis=run([objdump,'-d','--demangle',lib]); addr_rx=re.compile(r'^\s*([0-9a-fA-F]+):')
    glapis=('glBlendFunc','glBlendFuncSeparate','glBlendEquation','glTexEnv','glColor4','glAlphaFunc')
    hits=[]
    for i,ln in enumerate(all_dis):
        if not any(k in ln for k in glapis): continue
        m=addr_rx.match(ln)
        if not m: continue
        a=int(m.group(1),16); hits.append((i,a,containing(syms,a)))
    print(f'\n[GL_BLEND_ALPHA_CALLS] count={len(hits)}')
    for i,a,owner in hits:
        print(f'CALL addr=0x{a:08x} owner={(owner.name if owner else "<unknown>")!r}')
        for ln in all_dis[max(0,i-16):min(len(all_dis),i+3)]: print('  '+ln)
    print('\n[KNOWN_BLEND_ENUMS]')
    for k,v in {'GL_ZERO':0,'GL_ONE':1,'GL_SRC_ALPHA':0x302,'GL_ONE_MINUS_SRC_ALPHA':0x303,'GL_DST_ALPHA':0x304,'GL_ONE_MINUS_DST_ALPHA':0x305,'GL_FUNC_ADD':0x8006}.items(): print(f'{k}=0x{v:x} ({v})')

    # Parse every SPRT DAT then narrow to UI seam families. This also records owner/texture provenance.
    entries=[]
    for dat in root.rglob('*.dat'):
        try: entries.extend(parse_dat(dat))
        except Exception: pass
    rx=re.compile(r'^(EPISODE[0-9]+_(TOP_MIDDLE|BOTTOM_MIDDLE|LEFT|RIGHT|CENTER)|SCORE_(TOP_MIDDLE|BOTTOM_MIDDLE|LEFT|RIGHT|CENTER)|MENU_SLIDER_BG_|TUTORIAL_|PLAY_BUTTON_BG_)')
    suspects=[e for e in entries if rx.search(e[0])]
    print(f'\n[SUSPECT_SPRITES] totalSPRT={len(entries)} suspects={len(suspects)}')
    cache={}
    for e in suspects:
        name,tex,x,y,w,h,px,py,sheet=e
        if not tex: continue
        # images dir may be the 864x480 leaf; also search below/above by basename.
        cands=list(root.rglob(tex))
        if not cands:
            print(f'SPRITE name={name!r} sheet={sheet!r} texture={tex!r} rect={x},{y},{w},{h} asset=NOT_FOUND')
            continue
        tp=cands[0]
        key=str(tp)
        if key not in cache:
            try:
                cache[key]=decode_png(tp) if tp.suffix.lower()=='.png' else decode_pvr(tp)
            except Exception as ex:
                cache[key]=ex
        dec=cache[key]
        if isinstance(dec,Exception):
            print(f'SPRITE name={name!r} sheet={sheet!r} texture={tex!r} rect={x},{y},{w},{h} decode=UNSUPPORTED err={dec}')
            continue
        W,H,pix,fmt=dec
        print(f'SPRITE name={name!r} sheet={sheet!r} texture={tex!r} fmt={fmt} tex={W}x{H} rect={x},{y},{w},{h} pivot={px},{py}')
        for mode,sides in edge_stats(pix,W,H,x,y,w,h):
            for sn,n,eq,z,nz,ai,ao,rs in sides:
                print(f' EDGE mode={mode} side={sn} n={n} outsideEqualsInside={eq:.3f} outsideAlphaZero={z:.3f} outsideAlphaNonzero={nz:.3f} avgInsideA={ai:.1f} avgOutsideA={ao:.1f} sameRGBDifferentA={rs:.3f}')

    print('\n[CURRENT_ARM64_BLEND_STATE]')
    for needle in ('glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)','glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)'):
        print(f'sourceContains[{needle!r}]={"yes" if needle in src else "no"}')
    print('\n[INTERPRETATION_RULES]')
    print('rule1=If outsideEqualsInside is high on seam sprites, atlas extrusion is part of the contract; preserve source rect exactly and reproduce texture/blit semantics.')
    print('rule2=If outside pixels differ/are transparent, edge-to-edge LINEAR is only safe if original blit/alpha/blend or geometry semantics compensate; do not invent half-texel.')
    print('rule3=If ARMv7 uses premultiplied-alpha blend (ONE, ONE_MINUS_SRC_ALPHA), reproduce alpha representation and blend centrally, not per widget.')
    print('rule4=If source-rect delegation in SpriteSheet differs from raw DAT x/y/w/h, reproduce that delegation before changing EGL_Image UV math.')
    print('VERDICT=PASS_EVIDENCE_CAPTURED')
    return 0

if __name__=='__main__': raise SystemExit(main())
