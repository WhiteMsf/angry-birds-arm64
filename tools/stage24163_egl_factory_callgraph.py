#!/usr/bin/env python3
"""Stage 24.16.3 EGL factory origin callgraph audit.

Read-only analysis of the untouched ARMv7 libangrybirds.so.  Stage 24.16.2
proved GameLua.screenWidth/screenHeight come from EGL_Context::width/height and
that EGL_createContext forwards its width/height arguments unchanged.  This
pass walks *upstream* from EGL_createContext and the resize APIs so the exact
producer of those dimensions can be identified before changing presentation.
"""
from __future__ import annotations
import os,re,subprocess,sys
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

def exact(syms,name):
    return [s for s in syms if s.name==name and s.typ in 'TtWw']

def contains(syms,needle):
    return [s for s in syms if needle in s.name and s.typ in 'TtWw']

def parse_blocks(lines):
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+<(.+)>:\s*$'); hs=[]
    for i,l in enumerate(lines):
        m=rx.match(l)
        if m: hs.append((i,int(m.group(1),16)&~1,m.group(2)))
    out=[]
    for j,(i,a,n) in enumerate(hs): out.append((i,hs[j+1][0] if j+1<len(hs) else len(lines),a,n))
    return out

def call_target(line):
    if not re.search(r'\bblx?\b',line): return None
    m=re.search(r'\bblx?\s+0x([0-9A-Fa-f]+)',line)
    return (int(m.group(1),16)&~1) if m else None

def body_window(lines,bs,be,j,before=24,after=30):
    lo=max(bs,j-before); hi=min(be,j+after+1)
    return lines[lo:hi]

def main():
    if len(sys.argv)!=4:
        print('usage: stage24163_egl_factory_callgraph.py <llvm-nm> <llvm-objdump> <lib>',file=sys.stderr); return 2
    nm,objdump,lib=sys.argv[1:]
    print('ANGRY_STAGE24_16_3_EGL_FACTORY_CALLGRAPH 1')
    print('policy=DIAGNOSTIC_ONLY; untouched ARMv7 binary; no presentation constants invented')
    if not all(os.path.exists(x) for x in (nm,objdump,lib)):
        print('ERROR missing input'); return 3
    rc,nml=run([nm,'-S','-C',lib]); syms=parse_nm(nml)
    if not syms:
        rc,nml=run([nm,'-D','-S','-C',lib]); syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')

    factory_name='gr::EGL_createContext(int, int, gr::Context::OrientationType)'
    factories=exact(syms,factory_name)
    resets=contains(syms,'gr::EGL_Context::reset(int, int)')
    native=contains(syms,'gr::EGL_Context::setNativeSize(int, int)')
    print('FACTORY ' + (' '.join(f'0x{s.addr&~1:x}/0x{s.size:x}' for s in factories) if factories else 'NOT_FOUND'))
    print('RESET ' + (' '.join(f'0x{s.addr&~1:x}/0x{s.size:x}' for s in resets) if resets else 'NOT_FOUND'))
    print('SET_NATIVE_SIZE ' + (' '.join(f'0x{s.addr&~1:x}/0x{s.size:x}' for s in native) if native else 'NOT_FOUND'))

    drc,dis=run([objdump,'-d','--demangle',lib]); blocks=parse_blocks(dis)
    print(f'fullObjdumpExit={drc} lines={len(dis)} functions={len(blocks)}')
    by_addr={a:(bs,be,n) for bs,be,a,n in blocks}
    addr_to_name={s.addr&~1:s.name for s in syms}

    # Direct-call reverse graph: target address -> [(caller addr/name, line index)].
    reverse={}
    for bs,be,ba,bn in blocks:
        for j in range(bs,be):
            ta=call_target(dis[j])
            if ta is not None: reverse.setdefault(ta,[]).append((ba,bn,bs,be,j))

    print('\n--- EGL_CREATE_CONTEXT_BODY ---')
    for s in factories:
        bsbe=by_addr.get(s.addr&~1)
        if bsbe:
            bs,be,bn=bsbe
            for x in dis[bs:be]: print(x)

    roots=[]
    for kind,xs in [('factory',factories),('reset',resets),('setNativeSize',native)]:
        for s in xs: roots.append((kind,s.addr&~1,s.name))

    print('\n--- DIRECT_DIMENSION_PRODUCERS ---')
    total=0
    for kind,target,tname in roots:
        calls=reverse.get(target,[])
        print(f'TARGET kind={kind} addr=0x{target:x} name={tname} directCallers={len(calls)}')
        for ca,cn,bs,be,j in calls:
            total+=1
            print(f'\nCALL_EDGE kind={kind} caller=0x{ca:x} {cn} target=0x{target:x} call={dis[j].strip()}')
            for x in body_window(dis,bs,be,j): print(x)
    print(f'directDimensionProducerEdges={total}')

    # Recursively walk callers above EGL_createContext.  This is the missing
    # ownership hop from 24.16.2.  Print each edge once, with enough caller
    # context to recover r0/r1/r2 provenance.
    print('\n--- REVERSE_FACTORY_CALLGRAPH depth<=5 ---')
    seen_edges=set(); frontier=[]
    for s in factories: frontier.append((s.addr&~1,s.name,0,[s.addr&~1]))
    edge_count=0
    while frontier:
        target,tname,depth,path=frontier.pop(0)
        if depth>=5: continue
        for ca,cn,bs,be,j in reverse.get(target,[]):
            ek=(ca,target,j)
            if ek in seen_edges: continue
            seen_edges.add(ek); edge_count+=1
            indent='  '*depth
            print(f'\n{indent}UPSTREAM depth={depth+1} caller=0x{ca:x} {cn} -> target=0x{target:x} {tname}')
            print(f'{indent}call={dis[j].strip()}')
            for x in body_window(dis,bs,be,j,32,36): print(x)
            if ca not in path:
                frontier.append((ca,cn,depth+1,path+[ca]))
    print(f'reverseFactoryEdges={edge_count}')

    # Surface/window/EGL-related symbols are a compact cross-check.  We do not
    # infer ownership from names; they simply make unresolved indirect paths
    # obvious in the report if the reverse direct-call graph terminates early.
    print('\n--- ANDROID_EGL_SURFACE_SYMBOL_CROSSCHECK ---')
    rx=re.compile(r'(Android|Window|Surface|EGL|resolution|width|height)',re.I)
    rel=[s for s in syms if rx.search(s.name) and s.typ in 'TtWw']
    for s in sorted(rel,key=lambda q:q.addr)[:500]:
        print(f'SYMBOL 0x{s.addr&~1:x} size=0x{s.size:x} {s.name}')
    print(f'relatedSymbolCount={len(rel)} capped={min(len(rel),500)}')
    return 0

if __name__=='__main__': raise SystemExit(main())
