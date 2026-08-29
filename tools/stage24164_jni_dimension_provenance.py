#!/usr/bin/env python3
"""Stage 24.16.4 JNI dimension provenance audit.

Read-only analysis of the untouched ARMv7 libangrybirds.so. Stage 24.16.3
proved that Java_com_rovio_ka3d_MyRenderer_nativeInit is the sole direct caller
of gr::EGL_createContext and passes two values straight to the factory. This
pass dumps the JNI boundary and traces the ARM ABI origins of those values so
we can identify the exact Java nativeInit parameters that become
GameLua.screenWidth/screenHeight before changing presentation behavior.
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
        if m: out.append(Symbol(int(m.group(1),16)&~1,int(m.group(2),16),m.group(3),m.group(4)))
    return out

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

def insn_text(line):
    # objdump: " 48e80: e92d4ff0      push {...}"
    m=re.match(r'^\s*[0-9A-Fa-f]+:\s+(?:[0-9A-Fa-f]{4,8}\s+)+(.+?)\s*$',line)
    return m.group(1) if m else ''

def reg_written(text, reg):
    # Conservative ARM32 destination recognition for the common integer ops.
    # This is diagnostic annotation only; the full body is always emitted.
    t=text.strip().lower()
    r=reg.lower()
    pats=[
        rf'^(mov|movs|mvn|ldr|ldrb|ldrh|ldrsb|ldrsh|add|adds|sub|subs|rsb|and|orr|eor|bic|mul|mla|lsl|lsr|asr)\s+{re.escape(r)}\b',
        rf'^pop\s+\{{[^}}]*\b{re.escape(r)}\b',
    ]
    return any(re.search(p,t) for p in pats)

def parse_sp_adjust(text):
    t=text.strip().lower()
    # Return positive frame growth (entrySP-currentSP) delta contribution.
    m=re.match(r'^push\s+\{([^}]*)\}',t)
    if m:
        regs=[x.strip() for x in m.group(1).split(',') if x.strip()]
        # Expand simple ranges r4-r11.
        n=0
        for x in regs:
            mm=re.match(r'r(\d+)\s*-\s*r(\d+)$',x)
            if mm: n += int(mm.group(2))-int(mm.group(1))+1
            else: n += 1
        return 4*n
    m=re.match(r'^sub\s+sp\s*,\s*sp\s*,\s*#(0x[0-9a-f]+|\d+)',t)
    if m: return int(m.group(1),0)
    m=re.match(r'^add\s+sp\s*,\s*sp\s*,\s*#(0x[0-9a-f]+|\d+)',t)
    if m: return -int(m.group(1),0)
    return 0

def sp_offset(line):
    t=insn_text(line).lower()
    m=re.search(r'\[sp(?:\s*,\s*#(0x[0-9a-f]+|\d+))?\]',t)
    if not m: return None
    return int(m.group(1),0) if m.group(1) else 0

def java_param_for_entry_offset(off):
    # ARM32 JNI entry: r0=JNIEnv*, r1=jobject/class, r2=Java arg0,
    # r3=Java arg1, Java arg2 starts at entrySP+0.
    if off < 0 or off % 4: return None
    return 2 + off//4

def main():
    if len(sys.argv)!=4:
        print('usage: stage24164_jni_dimension_provenance.py <llvm-nm> <llvm-objdump> <lib>',file=sys.stderr); return 2
    nm,objdump,lib=sys.argv[1:]
    print('ANGRY_STAGE24_16_4_JNI_DIMENSION_PROVENANCE 1')
    print('policy=DIAGNOSTIC_ONLY; untouched ARMv7 binary; no presentation constants invented')
    if not all(os.path.exists(x) for x in (nm,objdump,lib)):
        print('ERROR missing input'); return 3
    rc,nml=run([nm,'-S','-C',lib]); syms=parse_nm(nml)
    if not syms:
        rc,nml=run([nm,'-D','-S','-C',lib]); syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')

    drc,dis=run([objdump,'-d','--demangle',lib]); blocks=parse_blocks(dis)
    print(f'fullObjdumpExit={drc} lines={len(dis)} functions={len(blocks)}')
    by_addr={a:(bs,be,n) for bs,be,a,n in blocks}

    my=[s for s in syms if 'Java_com_rovio_ka3d_MyRenderer_' in s.name and s.typ in 'TtWw']
    print('\n--- MYRENDERER_JNI_SYMBOLS ---')
    for s in sorted(my,key=lambda q:q.addr):
        print(f'JNI 0x{s.addr:x} size=0x{s.size:x} {s.name}')
    print(f'myRendererJniCount={len(my)}')

    init=[s for s in my if s.name=='Java_com_rovio_ka3d_MyRenderer_nativeInit']
    factory=[s for s in syms if s.name=='gr::EGL_createContext(int, int, gr::Context::OrientationType)' and s.typ in 'TtWw']
    if not init or not factory:
        print('ERROR nativeInit or EGL_createContext not found'); return 4
    ini=init[0]; fac=factory[0]
    block=by_addr.get(ini.addr)
    if not block:
        print('ERROR nativeInit body not found in objdump'); return 5
    bs,be,bn=block
    body=dis[bs:be]

    print('\n--- NATIVEINIT_FULL_BODY ---')
    for x in body: print(x)

    # Find factory call in nativeInit.
    call_j=None
    for j in range(bs,be):
        if call_target(dis[j])==fac.addr:
            call_j=j; break
    print('\n--- EGL_FACTORY_CALLSITE ---')
    if call_j is None:
        print('factoryCall=NOT_FOUND'); return 6
    print(f'factoryCall={dis[call_j].strip()}')
    for x in dis[max(bs,call_j-50):min(be,call_j+18)]: print(x)

    # Track monotonic initial stack-frame allocation from function start until
    # ordinary execution begins. This lets us map [sp,#imm] back to entrySP.
    frame=0
    print('\n--- ENTRY_ABI_AND_STACK_FRAME ---')
    print('ARM32_JNI_ENTRY r0=JNIEnv* r1=jobject/class r2=javaArg0 r3=javaArg1 entrySP+0=javaArg2 entrySP+4=javaArg3 ...')
    for j in range(bs+1,min(be,bs+30)):
        t=insn_text(dis[j])
        d=parse_sp_adjust(t)
        if d:
            frame += d
            print(f'FRAME deltaContribution={d:+d} cumulativeEntrySPMinusCurrentSP={frame} insn={dis[j].strip()}')
        # Stop after the first branch/call once prologue has clearly begun.
        if frame and re.search(r'\bblx?\b',t): break
    print(f'frameBytesAtEarlyBody={frame}')

    # Find the last writes to r9/r0/r1/r2 before the factory call. r0/r1/r2 at
    # the call are the factory width/height/orientation arguments.
    print('\n--- REGISTER_PROVENANCE_BEFORE_FACTORY ---')
    for reg in ('r9','r0','r1','r2'):
        hits=[]
        for j in range(bs+1,call_j):
            t=insn_text(dis[j])
            if reg_written(t,reg): hits.append(j)
        print(f'REG {reg} writesBeforeFactory={len(hits)}')
        for j in hits[-8:]:
            off=sp_offset(dis[j]); annot=''
            if off is not None and frame:
                entry_off=off-frame
                jp=java_param_for_entry_offset(entry_off)
                annot=f' spOff=0x{off:x} entrySPOff={entry_off:+d}' + (f' javaArg{jp}' if jp is not None else '')
            print(f'  {dis[j].strip()}{annot}')

    # Explicitly annotate every nativeInit stack load around the call, mapping
    # it to an incoming Java arg where the frame relation is exact.
    print('\n--- STACK_INPUTS_NEAR_FACTORY ---')
    for j in range(max(bs+1,call_j-90),call_j+1):
        t=insn_text(dis[j]).lower()
        if not re.match(r'^ldr\w*\s+r\d+\s*,\s*\[sp',t): continue
        off=sp_offset(dis[j])
        if off is None: continue
        entry_off=off-frame if frame else None
        jp=java_param_for_entry_offset(entry_off) if entry_off is not None else None
        print(f'{dis[j].strip()} frame={frame} entrySPOff={entry_off if entry_off is not None else "?"}' + (f' -> javaArg{jp}' if jp is not None else ''))

    # Dump likely dimension/surface JNI siblings too; these can independently
    # corroborate which Java parameters represent width/height.
    print('\n--- RELATED_JNI_BODIES ---')
    rx=re.compile(r'(resize|size|surface|resolution|width|height|init)',re.I)
    emitted=0
    for s in sorted(my,key=lambda q:q.addr):
        if s.addr==ini.addr or not rx.search(s.name): continue
        b=by_addr.get(s.addr)
        if not b: continue
        b0,b1,n=b
        print(f'\nJNI_BODY 0x{s.addr:x} size=0x{s.size:x} {s.name}')
        for x in dis[b0:b1]: print(x)
        emitted+=1
    print(f'relatedJniBodies={emitted}')

    # Keep nearby JNI-ish rodata strings visible for signatures/debug messages.
    print('\n--- JNI_RODATA_STRING_CROSSCHECK ---')
    rrc,rod=run([objdump,'-s','-j','.rodata',lib])
    ascii_runs=[]
    for line in rod:
        if re.search(r'(nativeInit|MyRenderer|screenWidth|screenHeight|width|height|resolution)',line,re.I):
            ascii_runs.append(line)
    for line in ascii_runs[:200]: print(line)
    print(f'rodataKeywordLines={len(ascii_runs)} capped={min(len(ascii_runs),200)} objdumpExit={rrc}')
    return 0

if __name__=='__main__': raise SystemExit(main())
