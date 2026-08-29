#!/usr/bin/env python3
"""Stage 24.16.2 screen-global source + EGL construction audit.

Read-only analysis of the untouched ARMv7 libangrybirds.so.  It closes the
specific ownership chain left open by 24.16.1:
  EGL_Context(w,h,orientation) -> Context::width/height virtual slots ->
  GameLua constructor -> Lua globals screenWidth/screenHeight.
No viewport/aspect formula is invented here.
"""
from __future__ import annotations
import os, re, struct, subprocess, sys
from dataclasses import dataclass

@dataclass
class Symbol:
    addr:int; size:int; typ:str; name:str

def run(args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
    return p.returncode,p.stdout.splitlines()

def parse_nm(lines):
    out=[]; rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    for line in lines:
        m=rx.match(line)
        if m: out.append(Symbol(int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(4)))
    return out

def elf32_sections(path):
    b=open(path,'rb').read()
    if b[:4]!=b'\x7fELF' or b[4]!=1: raise ValueError('expected ELF32')
    endian='<' if b[5]==1 else '>'
    eh=struct.unpack_from(endian+'16sHHIIIIIHHHHHH',b,0)
    shoff,shentsize,shnum,shstrndx=eh[6],eh[11],eh[12],eh[13]
    sh=[]
    for i in range(shnum):
        vals=struct.unpack_from(endian+'IIIIIIIIII',b,shoff+i*shentsize)
        sh.append(vals)
    shstr=sh[shstrndx]; names=b[shstr[4]:shstr[4]+shstr[5]]
    out=[]
    for vals in sh:
        no=vals[0]; end=names.find(b'\0',no); name=names[no:end].decode('utf-8','replace') if no<len(names) else ''
        out.append((name,vals[3],vals[4],vals[5])) # name, addr, offset, size
    return b,out,endian

def va_to_off(sections,va):
    for name,addr,off,size in sections:
        if size and addr<=va<addr+size:
            return off+(va-addr),name
    return None,None

def cstring_vas(blob,sections,needle):
    out=[]; start=0
    while True:
        i=blob.find(needle+b'\0',start)
        if i<0: break
        for name,addr,off,size in sections:
            if off<=i<off+size:
                out.append((addr+(i-off),name)); break
        start=i+1
    return out

def exact(symbols,needle):
    return [s for s in symbols if needle in s.name and s.typ in 'TtWw']

def body(objdump,lib,s):
    start=s.addr & ~1; stop=start+(s.size or 0x800)
    rc,lines=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',lib])
    return rc,lines

def print_body(objdump,lib,s,key):
    rc,lines=body(objdump,lib,s)
    print(f'\n--- BODY key={key} symbol={s.name} start=0x{s.addr&~1:x} size=0x{s.size:x} ---')
    print(f'objdumpExit={rc} lines={len(lines)}')
    for x in lines: print(x)

def parse_blocks(lines):
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+<(.+)>:\s*$'); hs=[]
    for i,l in enumerate(lines):
        m=rx.match(l)
        if m: hs.append((i,int(m.group(1),16),m.group(2)))
    out=[]
    for j,(i,a,n) in enumerate(hs): out.append((i,hs[j+1][0] if j+1<len(hs) else len(lines),a,n))
    return out

def main():
    if len(sys.argv)!=4:
        print('usage: stage24162_screen_global_source.py <llvm-nm> <llvm-objdump> <lib>',file=sys.stderr); return 2
    nm,objdump,lib=sys.argv[1:]
    print('ANGRY_STAGE24_16_2_SCREEN_GLOBAL_SOURCE 1')
    print('policy=DIAGNOSTIC_ONLY; untouched ARMv7 binary; no guessed presentation constants')
    if not all(os.path.exists(x) for x in (nm,objdump,lib)):
        print('ERROR missing input'); return 3
    rc,nml=run([nm,'-S','-C',lib]); syms=parse_nm(nml)
    if not syms:
        rc,nml=run([nm,'-D','-S','-C',lib]); syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')
    blob,secs,endian=elf32_sections(lib)
    for key in ('screenWidth','screenHeight'):
        hits=cstring_vas(blob,secs,key.encode())
        print(f'STRING {key} ' + (' '.join(f'va=0x{va:x} section={sec}' for va,sec in hits) if hits else 'NOT_FOUND'))

    wants=[
      ('egl_ctor','gr::EGL_Context::EGL_Context('),
      ('egl_width','gr::EGL_Context::width() const'),('egl_height','gr::EGL_Context::height() const'),
      ('egl_nativewidth','gr::EGL_Context::nativeWidth() const'),('egl_nativeheight','gr::EGL_Context::nativeHeight() const'),
      ('egl_setnativesize','gr::EGL_Context::setNativeSize('),('egl_reset','gr::EGL_Context::reset('),
      ('egl_setorientation','gr::EGL_Context::setOrientation('),('egl_setviewport','gr::EGL_Context::setViewport('),
      ('gamelua_ctor','GameLua::GameLua('),
    ]
    chosen=[]
    for key,needle in wants:
        xs=exact(syms,needle)
        print(f'TARGET key={key} count={len(xs)} ' + ' '.join(f'0x{s.addr:x}/0x{s.size:x}' for s in xs))
        chosen += [(key,s) for s in xs]
    for key,s in chosen:
        if key!='gamelua_ctor' or s==exact(syms,'GameLua::GameLua(')[0]:
            print_body(objdump,lib,s,key)

    # Resolve the Context vtable slots used by GameLua: object vptr points to
    # vtable+8 in the Itanium ABI, so slot 0x64 == symbol+8+0x64, etc.
    vts=[s for s in syms if s.name=='vtable for gr::EGL_Context']
    addrmap={s.addr&~1:s for s in syms}
    print('\n--- EGL_CONTEXT_VTABLE ---')
    if vts:
        vt=vts[0]; print(f'vtable=0x{vt.addr:x} size=0x{vt.size:x}')
        for slot in (0x64,0x68):
            eva=vt.addr+8+slot; off,sec=va_to_off(secs,eva)
            if off is None or off+4>len(blob):
                print(f'VSLOT offset=0x{slot:x} entryVA=0x{eva:x} UNMAPPED'); continue
            target=struct.unpack_from(endian+'I',blob,off)[0] & ~1
            sym=addrmap.get(target)
            print(f'VSLOT offset=0x{slot:x} entryVA=0x{eva:x} target=0x{target:x} symbol={sym.name if sym else "<unresolved>"}')
    else: print('vtable NOT_FOUND')

    # Focused GameLua constructor slice: this is where the two virtual calls are
    # converted from int to float and written via LuaTable::setNumber.
    print('\n--- GAMELUA_SCREEN_GLOBAL_INJECTION ---')
    gcs=exact(syms,'GameLua::GameLua(')
    if gcs:
        _,gl=body(objdump,lib,gcs[0])
        for i,line in enumerate(gl):
            if 'ldr\tpc' in line and ('#0x64]' in line or '#0x68]' in line):
                lo=max(0,i-8); hi=min(len(gl),i+14)
                print(f'WINDOW virtualCallLine={i} {line.strip()}')
                for x in gl[lo:hi]: print(x)
    else: print('GameLua ctor NOT_FOUND')

    # Direct caller ownership, using numeric target addresses as well as labels.
    print('\n--- DIRECT_CONSTRUCTION_AND_RESIZE_CALLERS ---')
    drc,dis=run([objdump,'-d','--demangle',lib]); print(f'fullObjdumpExit={drc} lines={len(dis)}')
    blocks=parse_blocks(dis)
    targets=[]
    for key in ('egl_ctor','egl_reset','egl_setnativesize'):
        needle=dict(wants)[key]
        for s in exact(syms,needle): targets.append((key,s.addr&~1,s.name))
    hits=0
    for bs,be,ba,bn in blocks:
        for j in range(bs,be):
            line=dis[j]
            if not re.search(r'\bblx?\b',line): continue
            tm=re.search(r'\bblx?\s+0x([0-9A-Fa-f]+)',line)
            ta=int(tm.group(1),16)&~1 if tm else None
            for key,addr,name in targets:
                if ta==addr or name in line:
                    hits+=1; lo=max(bs,j-16); hi=min(be,j+22)
                    print(f'\nCALLER target={key} 0x{addr:x} caller={bn} call={line.strip()}')
                    for x in dis[lo:hi]: print(x)
    print(f'directConstructionResizeHits={hits}')
    return 0
if __name__=='__main__': raise SystemExit(main())
