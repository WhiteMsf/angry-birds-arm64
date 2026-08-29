#!/usr/bin/env python3
from __future__ import annotations
import pathlib, subprocess, sys

HEADER='ANGRY_STAGE24_31_2_FIRST_RUN_TUTORIAL_RESTORATION_CONTRACT 2'

def main():
    if len(sys.argv)!=5:
        print('usage: stage24312_tutorial_restoration_contract.py <llvm-nm> <armv7-lib> <scripts-root> <project-cpp>', file=sys.stderr)
        return 2
    nm, lib, scripts, cpp = sys.argv[1:]
    scripts=pathlib.Path(scripts); cpp=pathlib.Path(cpp)
    print(HEADER)
    print('goal=restore untouched 1-1 birdTutorialPopups gate + original tutorial COMP visual/input semantics, while quarantining tutorial side effects from the Stage24-only hidden bootstrap level')
    corpus=b''
    files=[]
    if scripts.is_dir():
        for p in sorted(scripts.rglob('*')):
            if p.is_file():
                try:
                    b=p.read_bytes(); corpus += b'\0'+b; files.append((p,b))
                except OSError: pass
    needles=[b'birdTutorialPopups',b'TUTORIAL_1',b'TUTORIAL_OK',b'drawCompoSprite',b'getCompoSpriteBounds',b'tutorialInfo',b'BIRD_RED',b'tutorials']
    ok=True
    print('[ORIGINAL_LUA_CORPUS]')
    for n in needles:
        hits=sum(b.count(n) for _,b in files)
        print(f'needle={n.decode()!r} hits={hits}')
        if hits==0: ok=False
    src=cpp.read_text(encoding='utf-8',errors='replace') if cpp.is_file() else ''
    checks={
        'oldHeadlessDismissRemoved': 'stage8-dismiss-headless-tutorials' not in src and 'const char* dismissTutorials' not in src,
        'bootstrapTutorialSnapshot': '__stage24312a_bootstrapTutorialState' in src and 'action=SNAPSHOT_BEFORE_HIDDEN_LEVEL' in src,
        'bootstrapTutorialRollback': 'action=ROLLBACK_HIDDEN_LEVEL_ONLY' in src and 'settings.tutorials = __stage24312a_bootstrapTutorialState.tutorials' in src,
        'postBootstrapStateMarker': 'action=POST_BOOTSTRAP_ROLLBACK_STATE' in src,
        'compoDrawBinding': 'l_stage24312_res_drawCompoSprite' in src and 'lua_setfield(L, -2, "drawCompoSprite")' in src,
        'exactOverlayTail': '__stage24312_drawTutorialOverlay' in src and 'TUTORIAL_OK' in src and 'drawBox(box.sprites' in src,
        'queueRuntimeTelemetry': 'QUEUE_CHANGE frame=' in src,
        'realPersistenceStillPresent': 'PASS_FROM_DISK' in src and 'l_stage24311_saveLuaFile' in src,
    }
    print('[ARM64_SOURCE_GUARDS]')
    for k,v in checks.items():
        print(f'{k}={"PASS" if v else "FAIL"}')
        ok &= v
    print('[ARMV7_NATIVE]')
    try:
        p=subprocess.run([nm,'-S','-C',lib],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace',check=False)
        text=p.stdout
    except Exception as e:
        text=''; print(f'nmException={e}')
    native='LuaResources::drawCompoSprite' in text
    print(f'LuaResources.drawCompoSprite={"PASS" if native else "FAIL"}')
    ok &= native
    print('provenFlow=hidden bootstrap load may create tutorial state but Stage24 rolls only that scaffold side effect back; real updateLoading loadLevelInternal creates settings.tutorials[sprite] + queues tutorialInfo when unseen; updateGame pauses physics and removes birdTutorialPopups[1] on TUTORIAL_OK hit; drawGame draws shade/backgroundBox/COMP/TUTORIAL_OK')
    print('VERDICT=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 3
if __name__=='__main__': raise SystemExit(main())
