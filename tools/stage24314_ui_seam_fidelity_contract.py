#!/usr/bin/env python3
"""Stage 24.31.4 historical seam experiment / canonical supersession guard.

Stage24.31.4 originally introduced target-sized +0.5/-0.5 center sampling as
an A/B experiment. Stage24.31.4a later disproved that UV formula as canonical.
Stage24.31.4c supersedes the experiment with the recovered EGL_Image physical
POT-backing architecture. This guard accepts either the historical experiment
(for old packages) or the canonical 24.31.4c reconstruction.
"""
from __future__ import annotations
import pathlib,sys
HEADER='ANGRY_STAGE24_31_4_UI_SEAM_FIDELITY_CONTRACT 2'

def main():
    if len(sys.argv)!=2:
        print('usage: stage24314_ui_seam_fidelity_contract.py <project-cpp>',file=sys.stderr); return 2
    p=pathlib.Path(sys.argv[1]); src=p.read_text(encoding='utf-8',errors='replace')
    historical = (
        'STAGE24314_APPLY_HALF_TEXEL_FIX = true' in src and
        'STAGE24314_APPLY_HALF_TEXEL_FIX && haveTargetSize' in src and
        'sp->x + 0.5f' in src and
        'sp->x + sp->width - 0.5f' in src
    )
    canonical = (
        'STAGE24314_APPLY_HALF_TEXEL_FIX = false' in src and
        'stage24314c_next_pow2' in src and
        'backingWidth' in src and 'backingHeight' in src and
        'sp->x) / atlas->backingWidth' in src and
        'sp->y) / atlas->backingHeight' in src and
        '[stage24.31.4c-image] EDGE_POT_BACKING' in src
    )
    common = {
        'linearSamplerPresent':'GL_TEXTURE_MAG_FILTER, GL_LINEAR' in src,
        'tutorialPresent':'l_stage24312_res_drawCompoSprite' in src,
        'persistencePresent':'l_stage24311_saveLuaFile' in src,
    }
    print(HEADER)
    if canonical:
        print('mode=CANONICAL_24_31_4C_SUPERSEDES_HALF_TEXEL_EXPERIMENT')
        print('policy=edge-to-edge UVs normalized by physical POT EGL_Texture backing; half-texel experiment disabled')
    elif historical:
        print('mode=HISTORICAL_24_31_4_CENTER_SAMPLE_EXPERIMENT')
        print('policy=center-of-first-texel to center-of-last-texel for target-sized quads; noncanonical A/B only')
    else:
        print('mode=UNRECOGNIZED')
    print('\n[GUARDS]')
    print('historicalOrCanonical=' + ('PASS' if (historical or canonical) else 'FAIL'))
    for k,v in common.items(): print(f'{k}={"PASS" if v else "FAIL"}')
    ok=(historical or canonical) and all(common.values())
    print('\nVERDICT=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 3
if __name__=='__main__': raise SystemExit(main())
