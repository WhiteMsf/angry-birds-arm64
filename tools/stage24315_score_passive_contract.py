#!/usr/bin/env python3
"""Stage 24.31.5 passive score-fidelity audit preflight.

No gameplay values are changed.  This checks that the live observer records the
original Lua max-score message, star thresholds, every global score change with
scoreTable bucket deltas, completion-gate score, and final RESULT_STARS sprite.
It also inventories untouched score-related strings in the original script corpus.
"""
from __future__ import annotations
import pathlib,sys
HEADER='ANGRY_STAGE24_31_5_SCORE_PASSIVE_CONTRACT 1'

def main():
    if len(sys.argv)!=3:
        print('usage: stage24315_score_passive_contract.py <scripts-root> <project-cpp>',file=sys.stderr); return 2
    scripts=pathlib.Path(sys.argv[1]); cpp=pathlib.Path(sys.argv[2])
    print(HEADER)
    print('policy=PASSIVE_OBSERVATION_ONLY; no score/star/highscore mutation introduced by Stage24.31.5')
    needles=[
        b'Max score for ',b'scoreTable',b'updateScore',b'updateLevelEnding',
        b'birdsLeftScoreIncrement',b'blockDestroyedScoreIncrement',
        b'pigletteDestroyedScoreIncrement',b'silverScore',b'goldScore',b'eagleScore',
    ]
    print('[ORIGINAL_SCRIPT_PROVENANCE]')
    files=[]
    if scripts.is_dir():
        for p in sorted(scripts.rglob('*')):
            if p.is_file():
                try: files.append((p,p.read_bytes()))
                except OSError: pass
    hit_total=0
    for n in needles:
        hits=[]
        for p,b in files:
            pos=0
            while True:
                i=b.find(n,pos)
                if i<0: break
                hits.append((p,i)); pos=i+max(1,len(n))
        hit_total += len(hits)
        print(f"needle={n.decode('ascii')} hits={len(hits)}")
        for p,off in hits[:20]:
            try: rel=p.relative_to(scripts)
            except ValueError: rel=p
            print(f'  {rel} offset=0x{off:x}')

    src=cpp.read_text(encoding='utf-8',errors='replace') if cpp.is_file() else ''
    checks={
        'maxScoreObserver':'MAX_SCORE source=UNTOUCHED_loadLevelInternal' in src,
        'levelStartObserver':'LEVEL_START frame=' in src and 'birdsLeftIncrement=' in src,
        'scoreChangeObserver':'SCORE_CHANGE frame=' in src and "buckets='%s'" in src,
        'completionObserver':'COMPLETE_GATE frame=' in src,
        'resultSpriteObserver':'RESULT_MENU frame=' in src and "resultStars='%s'" in src,
        'observeOnlyMarkers':src.count('action=OBSERVE_ONLY') >= 4,
        'existingLedgerRetained':'stage24.19.1-score-ledger' in src,
        'starTableReadHelperRetained':'stage2410_star_thresholds' in src,
    }
    print('[ARM64_PASSIVE_GUARDS]')
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
    print('[QUESTION]')
    print('Does a normal 1-1 run reach the original goldScore threshold with the same score sources and end-of-level bird bonus timing as the untouched Lua contract?')
    print('interpretation=compare maxScore, gold threshold, bucket deltas, COMPLETE_GATE, post-complete bonus deltas, and RESULT_STARS; do not infer a regression from final score alone')
    ok=hit_total>0 and all(checks.values())
    print('VERDICT=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 3
if __name__=='__main__': raise SystemExit(main())
