#!/usr/bin/env python3
"""Stage 24.31.5 original RenderState2D transform contract audit.

Read-only audit against untouched ARMv7.  The goal is to recover the exact
consumer semantics for the matrix/scalar fields written by GameLua::setRenderState
before changing the ARM64 menu renderer.  This intentionally targets the main
settings gear and About Golden Egg transform bugs, not the already-closed UI
seam/presentation problem.
"""
from __future__ import annotations
import pathlib,re,subprocess,sys
from dataclasses import dataclass

HEADER='ANGRY_STAGE24_31_5_RENDERSTATE2D_CONTRACT 1'
@dataclass
class Sym: addr:int; size:int; typ:str; name:str

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

def body(objdump,lib,s):
    start=s.addr & ~1
    size=min(max(s.size or 0x80,0x40),0x1000)
    rc,lines=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',lib])
    print(f"\n[BODY] name={s.name!r} start=0x{start:x} size=0x{size:x} objdumpExit={rc} lines={len(lines)}")
    for ln in lines: print(ln)
    return lines

def main():
    if len(sys.argv)!=5:
        print('usage: stage24315_renderstate2d_contract.py <llvm-nm> <llvm-objdump> <armv7-lib> <project-cpp>',file=sys.stderr)
        return 2
    nm,objdump,lib,cpp=sys.argv[1:]
    print(HEADER)
    print('policy=READ_ONLY_ARMV7_EVIDENCE; Stage24.31.5b may consume this report through one global per-image reconstruction')
    print('frontiers=MAIN_SETTINGS gear rotates out/disappears; GOLDEN_EGG_STAR_EFFECT drifts offscreen while rotating')
    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml: rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'[SYMBOLS] nmExit={rc} parsed={len(syms)}')

    targets=[
        'GameLua::setRenderState(lua::LuaState*)',
        'gr::EGL_Context::getRenderState2D()',
        'gr::EGL_Context::setRenderState2D(gr::RenderState2D const&)',
        'gr::EGL_RenderBatcher::isBatchable(gr::EGL_RenderBatcher::Type, gr::Image*, int, gr::RenderState2D const&)',
        'gr::EGL_RenderBatcher::add(gr::EGL_RenderBatcher::Type, gr::Shader*, math::float3 const*, math::float2 const*, math::float4 const*, gr::Image*, int)',
        'gr::EGL_RenderBatcher::render(gr::EGL_RenderBatcher::Type, gr::Shader*, math::float3 const*, math::float2 const*, math::float4 const*, gr::Image*, int)',
        'gr::EGL_RenderBatcher::flush()',
        'gr::EGL_Shader_Default::begin()',
    ]
    found=0
    captured={}
    for want in targets:
        hits=[s for s in syms if s.name==want]
        if not hits:
            key=want.split('(')[0]
            hits=[s for s in syms if s.name.startswith(key+'(')]
        print(f"target={want!r} hits={len(hits)}")
        for s in hits[:2]:
            found+=1
            captured[s.name]=body(objdump,lib,s)

    print('\n[SETRENDERSTATE_FIELD_WRITE_HINTS]')
    sr=[]
    for k,v in captured.items():
        if k.startswith('GameLua::setRenderState('): sr=v; break
    if sr:
        for ln in sr:
            # Surface the exact state writes and trig calls without pretending
            # to infer the downstream pivot formula here.
            if re.search(r'\b(cos|sin)@plt\b|\[r5, #0x(?:10|14|18|1c|20|24|28|2c|30|34)\]',ln,re.I):
                print(ln)
    else:
        print('MISSING GameLua::setRenderState body')

    print('\n[RENDERBATCHER_STATE_COPY_HINTS]')
    add=[]
    for k,v in captured.items():
        if k.startswith('gr::EGL_RenderBatcher::add('): add=v; break
    if add:
        for ln in add:
            if 'memcpy@plt' in ln or '#92' in ln or '#0x5c' in ln or '#0x60' in ln:
                print(ln)
    else:
        print('MISSING RenderBatcher::add body')

    src=pathlib.Path(cpp).read_text(encoding='utf-8',errors='replace')
    checks={
        'legacyPresentationClosed':'[stage24.31.4f-presentation] PRESENT_PASS' in src,
        'arm64TransformSurfacePresent':(('const float tx = x + pivotX -' in src and 'glLoadMatrixf(model)' in src) or ('stage24315bTransformQuad' in src and 'glLoadIdentity()' in src)),
        'gearTelemetryRetained':'MAIN_SETTINGS' in src and '[stage24.31.3-ui] RENDER_STATE' in src,
        'targetSpriteTelemetryRetained':'[stage24.31.3-ui] SPRITE' in src and 'page == "mainMenu" || page == "about"' in src,
        'scorePassiveObserverPresent':'[stage24.31.5-score-passive]' in src,
    }
    print('\n[ARM64_GUARDS]')
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
    print('\n[DECISION_GATE]')
    print('requiredInterpretation=use exact vertex/pivot/translation/scale semantics from original backend; Stage24.31.5b replaces the old composed world-space model once, globally')
    print('antiFix=do not special-case MAIN_SETTINGS or GOLDEN_EGG_STAR_EFFECT by sprite name')
    ok=found>=6 and all(checks.values())
    print('VERDICT=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 3
if __name__=='__main__': raise SystemExit(main())
