#!/usr/bin/env python3
"""Stage 24.31.3 UI micro-fidelity contract audit.

Read-only against untouched ARMv7 + original script corpus.  It focuses on the
three proven visual frontiers: main-menu settings gear, About Golden Egg star
effect, and atlas/composprite seam behavior.  No half-texel/pivot/visibility fix
is selected here; the report exists to choose the exact fix from evidence.
"""
from __future__ import annotations
import pathlib,re,subprocess,sys
from dataclasses import dataclass

HEADER='ANGRY_STAGE24_31_3_UI_MICROFIDELITY_CONTRACT 1'
@dataclass
class Sym: addr:int; size:int; typ:str; name:str

def run(args):
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace',check=False)
        return p.returncode,p.stdout.splitlines()
    except Exception as e: return -1,[f'exception={e}']

def parse_nm(lines):
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$'); out=[]
    for ln in lines:
        m=rx.match(ln)
        if m: out.append(Sym(int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(4)))
    return out

def ascii_runs(data,minlen=4):
    rx=re.compile(rb'[\x20-\x7e]{%d,}'%minlen)
    for m in rx.finditer(data): yield m.start(),m.group().decode('ascii','replace')

def main():
    if len(sys.argv)!=6:
        print('usage: stage24313_ui_microfidelity_contract.py <llvm-nm> <llvm-objdump> <armv7-lib> <scripts-root> <project-cpp>',file=sys.stderr); return 2
    nm,objdump,lib,scripts,cpp=sys.argv[1:]
    scripts=pathlib.Path(scripts); cpp=pathlib.Path(cpp)
    print(HEADER)
    print('policy=' + ('HISTORICAL_AUDIT_WITH_24_31_4_FOLLOWUP_ACTIVE' if 'STAGE24314_APPLY_HALF_TEXEL_FIX' in cpp.read_text(encoding='utf-8',errors='replace') else 'READ_ONLY_AUDIT; do not invent half-texel, pivot, visibility, or animation fixes before report review'))
    print('frontiers=mainMenu settings gear disappears/reappears; About Golden Egg aura flies offscreen; straight seams visible across UI/composprite panels')

    rc,nml=run([nm,'-S','-C',lib])
    if rc!=0 or not nml: rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'\n[ARMV7_SYMBOLS] nmExit={rc} parsed={len(syms)}')
    targets=[
        'game::SpriteSheet::drawSprite(gr::Context*, game::Sprite const*, float, float, float, float, game::Anchor) const',
        'game::Resources::drawCompoSprite(lang::String const&, lang::String const&, float, float, game::Anchor) const',
        'game::LuaResources::drawSprite(lua::LuaState*)',
        'game::LuaResources::drawCompoSprite(lua::LuaState*)',
        'GameLua::setRenderState(lua::LuaState*)',
    ]
    found=0
    for want in targets:
        hits=[s for s in syms if s.name==want]
        if not hits:
            # tolerate namespace/demangler spelling differences while staying exact enough
            key=want.split('(')[0]
            hits=[s for s in syms if s.name.startswith(key+'(')]
        print(f'target={want!r} hits={len(hits)}')
        for s in hits[:3]:
            found+=1
            start=s.addr & ~1; size=min(max(s.size or 0x80,0x40),0x500)
            drc,body=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',lib])
            print(f'BODY name={s.name!r} start=0x{start:x} size=0x{size:x} objdumpExit={drc} lines={len(body)}')
            for ln in body: print(ln)

    print('\n[ORIGINAL_SCRIPT_LITERAL_PROVENANCE]')
    needles=('MAIN_SETTINGS_LEFT','MAIN_SETTINGS_RIGHT','GOLDEN_EGG_STAR_EFFECT','GOLDEN_EGG','settingsPage','buttonSettings','rotation','angle','visible','drawCompoSprite','drawBox')
    files=[]
    if scripts.is_dir():
        for p in sorted(scripts.rglob('*')):
            if p.is_file():
                try: files.append((p,p.read_bytes()))
                except OSError: pass
    for n in needles:
        hits=[]; nb=n.encode('ascii')
        for p,b in files:
            pos=0
            while True:
                i=b.find(nb,pos)
                if i<0: break
                hits.append((p,i)); pos=i+max(1,len(nb))
        print(f'needle={n!r} hits={len(hits)}')
        for p,off in hits[:40]:
            try: rel=p.relative_to(scripts)
            except ValueError: rel=p
            print(f'  {rel} offset=0x{off:x}')

    print('\n[LITERAL_NEIGHBORHOODS]')
    keyrx=re.compile(r'(?i)(MAIN_SETTINGS|GOLDEN_EGG|STAR_EFFECT|settingsPage)')
    for p,b in files:
        strings=list(ascii_runs(b)); idx={off:i for i,(off,_) in enumerate(strings)}
        kh=[(off,text) for off,text in strings if keyrx.search(text)]
        if not kh: continue
        try: rel=p.relative_to(scripts)
        except ValueError: rel=p
        print(f'FILE {rel} hits={len(kh)}')
        shown=set()
        for off,text in kh:
            i=idx[off]
            for j in range(max(0,i-5),min(len(strings),i+6)):
                item=strings[j]
                if item in shown: continue
                shown.add(item); print(f'  0x{item[0]:08x}\t{item[1]}')

    src=cpp.read_text(encoding='utf-8',errors='replace') if cpp.is_file() else ''
    checks={
        'runtimeSpriteGeometryTelemetry':'[stage24.31.3-ui] SPRITE seq=' in src,
        'runtimeRenderStateTelemetry':'[stage24.31.3-ui] RENDER_STATE' in src,
        'compoPartTelemetry':'[stage24.31.3-ui] COMPO_PART' in src,
        'edgeAndHalfTexelLogged':'uvEdge=' in src and 'uvHalfTexel=' in src,
        'samplingModeRecognized':('STAGE24314_APPLY_HALF_TEXEL_FIX' in src) or ('STAGE24313_APPLY_HALF_TEXEL_FIX' not in src),
        'tutorialStillPresent':'l_stage24312_res_drawCompoSprite' in src,
        'persistenceStillPresent':'l_stage24311_saveLuaFile' in src and 'PASS_FROM_DISK' in src,
    }
    print('\n[ARM64_AUDIT_GUARDS]')
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
    ok=found>=3 and all(checks.values())
    print('\n[DECISION_GATE]')
    print('nextEvidence=runtime target draw calls + original SpriteSheet::drawSprite body decide whether seams are UV edge sampling vs geometry; target render-state/pivot/visibility sequence decides gear and Golden Egg effect')
    print('implementationDecision=' + ('FOLLOWUP_24_31_4_CENTER_SAMPLE_ACTIVE' if 'STAGE24314_APPLY_HALF_TEXEL_FIX' in src else 'DEFERRED_UNTIL_RUNTIME_REPRODUCTION'))
    print('VERDICT=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 3
if __name__=='__main__': raise SystemExit(main())
