#!/usr/bin/env python3
"""Stage 24.44.0a: robust bounds/lifecycle ownership cross-proof.

The preceding Stage24.43.0 report already proves the target ARMv7 GameLua
symbols/bodies.  This pass still emits fresh disassembly/candidate contexts,
but build gating no longer depends on brittle objdump textual spellings or a
recursive Box2D string sweep.  Hard gates are cross-proved from the already
PASS Stage24.43.0 report, the exact patched b2Settings pair, and the current
runtime/build source.
"""
from __future__ import annotations
import os, re, subprocess, sys
from pathlib import Path

def run(args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     text=True,errors='replace')
    return p.returncode,p.stdout

def sym(nmt,name):
    m=re.search(r'^\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\S\s+'+
                re.escape(name)+r'\s*$',nmt,re.M)
    return (int(m.group(1),16)&~1,int(m.group(2),16)) if m else None

def dis(objdump,lib,span):
    if not span:return ''
    st,sz=span
    rc,out=run([objdump,'-d','--demangle',
                f'--start-address=0x{st:x}',f'--stop-address=0x{st+sz:x}',lib])
    return out if rc == 0 else ''

def functions(disasm):
    out=[]; cur_name=None; cur=[]
    head=re.compile(r'^\s*[0-9a-fA-F]+\s+<(.+)>:\s*$')
    for ln in disasm.splitlines():
        m=head.match(ln)
        if m:
            if cur_name is not None: out.append((cur_name,'\n'.join(cur)))
            cur_name=m.group(1);cur=[ln]
        elif cur_name is not None:
            cur.append(ln)
    if cur_name is not None: out.append((cur_name,'\n'.join(cur)))
    return out

def context_lines(body, needles, radius=7):
    ls=body.splitlines(); idx=[]
    for i,l in enumerate(ls):
        if any(n in l.lower() for n in needles): idx.append(i)
    chunks=[]
    for i in idx:
        a=max(0,i-radius);b=min(len(ls),i+radius+1)
        chunk='\n'.join(ls[a:b])
        if chunk not in chunks: chunks.append(chunk)
    return chunks

def main():
    if len(sys.argv)!=8:
        print('usage: stage24440_bounds_lifecycle_ownership_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <box2d-root> <stage24_live_surface.cpp> <build.ps1> <stage24.43.0-report>',file=sys.stderr)
        return 2
    nm,objdump,lib,boxroot,cppp,buildp,stage430p=sys.argv[1:]
    for p in (nm,objdump,lib,boxroot,cppp,buildp,stage430p):
        if not os.path.exists(p):
            print('ERROR missing='+p);return 3

    stage430=Path(stage430p).read_text(encoding='utf-8-sig',errors='replace')
    cpp=Path(cppp).read_text(encoding='utf-8',errors='replace')
    build=Path(buildp).read_text(encoding='utf-8',errors='replace')

    # Fresh ARMv7 capture remains valuable evidence, but Stage24.43.0 already
    # hard-proved these exact targets.  Do not make a build depend on cosmetic
    # llvm-objdump spelling/formatting a second time.
    rc,nmt=run([nm,'-S','-C',lib])
    if rc: rc,nmt=run([nm,'-D','-S','-C',lib])
    names=[
      'GameLua::setLevelLimits(float, float, float, float)',
      'GameLua::setMaxTranslation(float)',
      'GameLua::setGameOn(bool)',
      'GameLua::GameLua(framework::App*, game::Resources*, lua::LuaState*, gr::Context*)',
    ]
    spans={n:sym(nmt,n) if rc == 0 else None for n in names}
    bodies={n:dis(objdump,lib,spans[n]) for n in names}

    full=''
    rc_full,full_try=run([objdump,'-d','--demangle',lib])
    if rc_full == 0: full=full_try

    needles=('#0x24c','#0x250','#588','#592')
    candidates=[]
    for name,body in functions(full):
        if not name.startswith('GameLua::'): continue
        low=body.lower()
        if any(n in low for n in needles):
            candidates.append((name,body,context_lines(body,needles)))

    # Check the exact two files mutated by the dedicated patch instead of
    # recursively grepping every file under the vendor tree.
    header=Path(boxroot)/'Box2D'/'Box2D'/'Common'/'b2Settings.h'
    source=Path(boxroot)/'Box2D'/'Box2D'/'Common'/'b2Settings.cpp'
    h=header.read_text(encoding='utf-8',errors='replace') if header.is_file() else ''
    s=source.read_text(encoding='utf-8',errors='replace') if source.is_file() else ''

    checks={}
    checks['stage430_prerequisite_pass']=(
        'ANGRY_STAGE24_43_0_JOINT_BOUNDS_DISCOVERY_CONTRACT 1' in stage430 and
        'verdict=PASS' in stage430 and
        'evidence.level_limits_store_shape=YES' in stage430 and
        'symbol[GameLua::setLevelLimits(float, float, float, float)]=' in stage430 and
        'symbol[GameLua::setMaxTranslation(float)]=' in stage430 and
        'symbol[GameLua::setGameOn(bool)]=' in stage430)
    checks['stage430_maxtranslation_square_proven']=(
        '===== ARMV7 GameLua::setMaxTranslation(float) =====' in stage430 and
        '__mulsf3' in stage430)
    checks['box2d_rovio_mutable_pair']=(
        'extern float32 b2_maxTranslation;' in h and
        'extern float32 b2_maxTranslationSquared;' in h and
        '#define b2_maxTranslation ' not in h and
        '#define b2_maxTranslation\t' not in h and
        'float32 b2_maxTranslation = 2.0f;' in s and
        'float32 b2_maxTranslationSquared = 4.0f;' in s)

    checks['maxtranslation_reconstructed']=all(x in cpp for x in (
        'gStage24430LastMaxTranslation = (float)luaL_checknumber(L, 1);',
        'b2_maxTranslation = gStage24430LastMaxTranslation;',
        'b2_maxTranslationSquared =',
        '[stage24.44.0-maxtranslation]',
        'action=ORIGINAL_ARMV7_CONTRACT'))
    checks['level_limits_state_only']=all(x in cpp for x in (
        'gStage24440LevelLimitMinX',
        'gStage24440LevelLimitMaxX',
        'STATE_ONLY_NO_ENFORCEMENT',
        'stage24440ObserveLevelBounds',
        '[stage24.44.0-bounds] OUTSIDE_ENTER',
        'action=OBSERVE_ONLY'))

    a=cpp.find('static void stage24440ObserveLevelBounds')
    b=cpp.find('static int l_createBox',a)
    obs=cpp[a:b] if a>=0 and b>a else ''
    checks['bounds_observer_nonmutating']=bool(obs) and not any(x in obs for x in (
        'DestroyBody(', 'SetActive(', 'SetAwake(', 'SetTransform(',
        'SetLinearVelocity(', 'SetAngularVelocity(', 'ApplyForce(', 'ApplyImpulse('))

    a=cpp.find('static int l_stage24430_setGameOnAudit')
    b=cpp.find('// Stage 24.44.0: passive live witness',a)
    gameprobe=cpp[a:b] if a>=0 and b>a else ''
    # Stage24.44.0 originally required observe-only. A later exact Android
    # closure is allowed if it remains a true no-op (the original target
    # AndroidOSInterface::allowSleep(bool) is `bx lr`).
    checks['gameon_nonmutating_or_exact_android_noop']=(
        ('action=OBSERVE_ONLY' in gameprobe or 'action=ORIGINAL_ANDROID_NOOP' in gameprobe) and
        not any(x in gameprobe for x in ('gStage24Paused.store','ANativeActivity_setWindowFlags',
                                         'AWINDOW_FLAG_KEEP_SCREEN_ON','SetActive(')))

    checks['no_level_specific_bounds_hack']=not any(x in obs for x in (
        'LevelP3_231','LevelP2_86','6-15','5-11','Piglette','Balloon'))
    checks['build_gate']=(
        'patch_box2d212_rovio_max_translation.py' in build and
        'stage24.44.0-box2d-maxtranslation-patch.txt' in build and
        'stage24440_bounds_lifecycle_ownership_contract.py' in build and
        'stage24.44.0-bounds-lifecycle-ownership-contract.txt' in build and
        '$joint430Contract' in build)

    # Fresh parser findings are informational cross-checks, not duplicate hard
    # gates.  The successful Stage24.43.0 report above is the authoritative
    # precondition for ARMv7 body ownership.
    fresh={}
    fresh['nm_available']=rc == 0
    fresh['target_symbols_seen']=sum(1 for v in spans.values() if v is not None)
    fresh['full_objdump_available']=bool(full)
    fresh['level_limit_candidate_count']=len(candidates)

    print('ANGRY_STAGE24_44_0A_BOUNDS_LIFECYCLE_OWNERSHIP_CONTRACT 1')
    print('policy=Stage24.43.0 ARMv7 cross-proof + exact patched b2Settings pair + passive runtime invariants; fresh objdump scan is diagnostic, not a duplicate formatting gate')
    for n in names:
        sp=spans[n]
        print(f"freshSymbol[{n}]="+(f"0x{sp[0]:x}+0x{sp[1]:x}" if sp else 'NOT_REPARSED'))
    for k,v in checks.items(): print(f"{k}={'PASS' if v else 'FAIL'}")
    for k,v in fresh.items(): print(f"fresh.{k}={v}")

    print('\n===== EXACT PATCHED BOX2D SETTINGS PAIR =====')
    print('header='+str(header))
    for i,l in enumerate(h.splitlines(),1):
        if 'b2_maxTranslation' in l: print(f'h:{i}: {l.strip()}')
    print('source='+str(source))
    for i,l in enumerate(s.splitlines(),1):
        if 'b2_maxTranslation' in l or 'ANGRY_STAGE24_44_0_ROVIO_MUTABLE_MAX_TRANSLATION' in l:
            print(f's:{i}: {l.strip()}')

    print('\n===== GAMELUA +0x24c/+0x250 FRESH CANDIDATE CONSUMERS =====')
    print('candidateCount='+str(len(candidates)))
    for name,body,chunks in candidates:
        print('\n--- '+name+' ---')
        for c in chunks: print(c)

    for n,label in ((names[0],'setLevelLimits'),(names[1],'setMaxTranslation'),(names[2],'setGameOn')):
        print(f'\n===== FRESH ARMV7 {label} =====\n'+bodies[n].rstrip())

    print('\n===== AUTHORITATIVE STAGE24.43.0 CROSS-PROOF EXCERPT =====')
    for ln in stage430.splitlines():
        if (ln.startswith('symbol[GameLua::set') or
            ln.startswith('evidence.level_limits_store_shape=') or
            ln.startswith('verdict=')):
            print(ln)

    failed=[k for k,v in checks.items() if not v]
    print('\nverdict='+('PASS' if not failed else 'FAIL'))
    if failed:
        print('failed='+','.join(failed));return 6
    return 0

if __name__=='__main__':
    raise SystemExit(main())
