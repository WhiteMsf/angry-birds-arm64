#!/usr/bin/env python3
"""Stage24.47.6B: acquire original ARMv7 MyRenderer JNI lifecycle bodies.

Read-only evidence.  Robust against llvm-nm/llvm-objdump CLI differences seen
across Android NDK releases.  The lifecycle implementation itself is not
changed by this auditor hotfix.
"""
from __future__ import annotations
import pathlib,re,subprocess,sys

def run(args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
    return p.returncode,p.stdout.splitlines()

def parse_nm(lines):
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    out={}
    for line in lines:
        m=rx.match(line)
        if not m:
            continue
        name=m.group(4)
        ent=(int(m.group(1),16)&~1,int(m.group(2),16),m.group(3))
        old=out.get(name)
        # Prefer an executable/text witness and a non-zero/larger size when
        # normal .symtab and .dynsym both expose the same function.
        score=lambda e: ((e[2] in 'TtWw'), e[1] > 0, e[1])
        if old is None or score(ent) > score(old):
            out[name]=ent
    return out

def full_disassembly_function(objdump,lib,name,addr):
    """Fallback used only if range options fail on a particular llvm-objdump."""
    rc,lines=run([objdump,'-d','--demangle',lib])
    if rc:
        return rc,lines
    hdr=re.compile(r'^\s*([0-9A-Fa-f]+)\s+<(.+)>:\s*$')
    start=None
    for i,line in enumerate(lines):
        m=hdr.match(line)
        if not m:
            continue
        a=int(m.group(1),16)&~1
        n=m.group(2)
        if a==addr or n==name:
            start=i
            break
    if start is None:
        return 5,[f'fallback full objdump could not locate {name} at 0x{addr:x}']
    end=len(lines)
    for i in range(start+1,len(lines)):
        if hdr.match(lines[i]):
            end=i
            break
    return 0,lines[start:end]

def body_for(objdump,lib,name,addr,size):
    stop=addr+max(size,4)
    # IMPORTANT: the equals form is the already-proven syntax used throughout
    # the existing Stage24 native auditors on the user's NDK/llvm-objdump.
    rc,body=run([objdump,'-d','--demangle',f'--start-address=0x{addr:x}',f'--stop-address=0x{stop:x}',lib])
    if rc==0 and any(re.match(r'^\s*[0-9A-Fa-f]+\s+<',x) or re.match(r'^\s*[0-9A-Fa-f]+:',x) for x in body):
        return 0,body,'RANGE_EQUALS'
    frc,fbody=full_disassembly_function(objdump,lib,name,addr)
    if frc==0:
        return 0,fbody,'FULL_OBJDUMP_FALLBACK'
    return rc or frc, body + ['--- fallback ---'] + fbody, 'FAILED'

def main():
    if len(sys.argv)!=4:
        print('usage: stage24476_native_jni_lifecycle_audit.py <llvm-nm> <llvm-objdump> <armv7-lib>',file=sys.stderr)
        return 2
    nm,objdump,lib=sys.argv[1:]
    print('ANGRY_STAGE24_47_6_NATIVE_JNI_LIFECYCLE_AUDIT 2')
    print('policy=READ_ONLY_ARMV7_ACQUISITION; wrapper TERM_WINDOW must not be equated with nativeDeinit')
    for x in (nm,objdump,lib):
        if not pathlib.Path(x).exists():
            print(f'ERROR missing input={x}')
            return 3

    nrc,nlines=run([nm,'-S','-C',lib])
    drc,dlines=run([nm,'-D','-S','-C',lib])
    if nrc and drc:
        print(f'ERROR llvm-nm failed normalExit={nrc} dynamicExit={drc}')
        return 4
    syms=parse_nm((nlines if nrc==0 else []) + (dlines if drc==0 else []))
    print(f'nmExit={nrc} dynNmExit={drc} parsedSymbols={len(syms)}')

    targets=[
        'Java_com_rovio_ka3d_MyRenderer_nativeInit',
        'Java_com_rovio_ka3d_MyRenderer_nativePause',
        'Java_com_rovio_ka3d_MyRenderer_nativeResume',
        'Java_com_rovio_ka3d_MyRenderer_nativeDeinit',
    ]
    ok=True
    for name in targets:
        ent=syms.get(name)
        if not ent:
            print(f'TARGET name={name} status=MISSING')
            ok=False
            continue
        addr,size,typ=ent
        print(f'TARGET name={name} status=FOUND addr=0x{addr:x} size=0x{size:x} type={typ}')
        rc,body,method=body_for(objdump,lib,name,addr,size)
        print(f'BODY_ACQUIRE name={name} method={method} exit={rc}')
        if rc:
            print(f'BODY name={name} status=OBJDUMP_FAIL')
            for line in body[:80]:
                print(line)
            ok=False
            continue
        print(f'BODY_BEGIN name={name}')
        for line in body:
            print(line)
        print(f'BODY_END name={name}')

    print('separation=pause/resume/deinit_are_distinct_original_JNI_entrypoints')
    print('verdict='+('PASS' if ok else 'FAIL'))
    return 0 if ok else 1

if __name__=='__main__':
    raise SystemExit(main())
