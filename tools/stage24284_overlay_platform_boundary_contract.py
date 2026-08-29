#!/usr/bin/env python3
"""Stage 24.28.4: overlay render ownership + external platform button boundary audit.

Read-only.  It does not launch URLs or alter original assets.  It inventories
openURL/trailer/social/store provenance in the user's original script corpus and
nearby ARMv7/JNI symbols/strings so the live ARM64 shim can remain diagnostic.
"""
from __future__ import annotations
import os, pathlib, re, subprocess, sys

HEADER='ANGRY_STAGE24_28_4_OVERLAY_PLATFORM_BOUNDARY_CONTRACT 1'
NEEDLES=(
    'openURL','gotoAngryBirdsTrailer','ANGRY_BIRDS_TRAILER_URL','trailer',
    'facebook','twitter','menuOvi','MENU_OVI','MENU_APP_STORE','store',
    'levelComplete','levelFailed','pause','gameFinished',
)
SYM_TERMS=('url','browser','intent','market','store','trailer','facebook','twitter','open')

def run(args):
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                         text=True,errors='replace',check=False)
        return p.returncode,p.stdout.splitlines()
    except Exception as e:
        return -1,[f'exception={e}']

def ascii_runs(data:bytes,min_len=4):
    start=None
    for i,b in enumerate(data+b'\0'):
        if 32<=b<127:
            if start is None:start=i
        else:
            if start is not None and i-start>=min_len:
                yield start,data[start:i].decode('ascii','replace')
            start=None

def scan_raw(root:pathlib.Path):
    hits={n:[] for n in NEEDLES}
    if not root.is_dir(): return hits
    for p in root.rglob('*'):
        if not p.is_file(): continue
        try:data=p.read_bytes()
        except OSError:continue
        low=data.lower()
        for n in NEEDLES:
            needle=n.lower().encode()
            pos=0
            while True:
                i=low.find(needle,pos)
                if i<0:break
                hits[n].append((p,i))
                pos=i+max(1,len(needle))
    return hits

def main():
    if len(sys.argv)!=5:
        print('usage: stage24284_overlay_platform_boundary_contract.py <llvm-nm> <lib.so> <scripts-root> <project-cpp>',file=sys.stderr)
        return 2
    nm,lib,scripts,cpp=sys.argv[1:]
    scripts=pathlib.Path(scripts); cpp=pathlib.Path(cpp)
    print(HEADER)
    print('policy=READ_ONLY; URL launching remains disabled in Stage24.28.4')
    print('runtimeFix=FULL_FRAME_MENU and GAMEPLAY_OVERLAY are separate ownership classes')
    print('overlayPages=pause;levelComplete;levelFailed;gameFinished;gameFinishedThreeStars;gameFinishedLP2;gameFinishedThreeStarsLP2')

    hits=scan_raw(scripts)
    print('\n[ORIGINAL_SCRIPT_PROVENANCE]')
    for n in NEEDLES:
        hs=hits[n]
        print(f"needle={n!r} hits={len(hs)}")
        for p,off in hs[:80]:
            try:r=p.relative_to(scripts)
            except ValueError:r=p
            print(f'  {r} offset=0x{off:x}')
        if len(hs)>80: print(f'  ... +{len(hs)-80} more')

    print('\n[ORIGINAL_SCRIPT_ASCII_CONTEXT]')
    context=[]
    if scripts.is_dir():
        for p in scripts.rglob('*'):
            if not p.is_file(): continue
            try:data=p.read_bytes()
            except OSError:continue
            for off,text in ascii_runs(data,4):
                lo=text.lower()
                if any(t.lower() in lo for t in NEEDLES[:10]):
                    try:r=p.relative_to(scripts)
                    except ValueError:r=p
                    context.append((str(r),off,text))
    for r,off,text in context[:500]:
        print(f'  {r} offset=0x{off:x} text={text}')
    print(f'asciiContextHits={len(context)}')

    print('\n[ARMV7_SYMBOL_FRONTIER]')
    if os.path.exists(nm) and os.path.exists(lib):
        rc,lines=run([nm,'-C','-S',lib])
        chosen=[]
        for line in lines:
            low=line.lower()
            if any(t in low for t in SYM_TERMS): chosen.append(line)
        print(f'nmExit={rc} selected={len(chosen)}')
        for line in chosen[:300]: print(line)
    else:
        print('nm/lib unavailable')

    print('\n[ARMV7_BINARY_STRINGS]')
    try:
        data=pathlib.Path(lib).read_bytes()
        selected=[]
        for off,text in ascii_runs(data,4):
            lo=text.lower()
            if any(t in lo for t in ('url','browser','market','trailer','facebook','twitter','ovi','store')):
                selected.append((off,text))
        print(f'selected={len(selected)}')
        for off,text in selected[:500]: print(f'  offset=0x{off:x} text={text}')
    except OSError as e:
        print(f'libReadError={e}')

    print('\n[ARM64_SOURCE_GUARDS]')
    text=cpp.read_text(encoding='utf-8',errors='replace') if cpp.is_file() else ''
    checks={
        'overlayClassifier':'stage24284IsGameplayOverlayPage' in text,
        'safeOpenURL':'l_stage24284_openURL' in text,
        'overlayPassLog':'OVERLAY_FRAME_PASS' in text,
        'fullFrameClassifier':'stage24284FullFrameMenu' in text,
    }
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')

    # The proven v0.26.86 fault requires at least an openURL string in the original
    # script corpus and the source guards in the build under test.
    if not hits['openURL']:
        print('VERDICT=FAIL original script corpus contains no openURL provenance')
        return 3
    if not all(checks.values()):
        print('VERDICT=FAIL ARM64 Stage24.28.4 source guards incomplete')
        return 4
    print('VERDICT=PASS overlay ownership and external URL boundary inventoried')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
