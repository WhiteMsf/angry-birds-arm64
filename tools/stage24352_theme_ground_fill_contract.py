#!/usr/bin/env python3
import sys
from pathlib import Path

def need(cond,msg,errs):
    if not cond: errs.append(msg)

def main():
    if len(sys.argv) != 3:
        print('usage: stage24352_theme_ground_fill_contract.py <build.ps1> <runtime.cpp>')
        return 2
    b=Path(sys.argv[1]).read_text(encoding='utf-8-sig',errors='replace')
    c=Path(sys.argv[2]).read_text(encoding='utf-8',errors='replace')
    e=[]
    for token in ['INGAME_THEME_GROUND_2.pvr','themeGround2Direct','themeGround2Zip','themeGround2Pvr']:
        need(token in b, f'build missing theme2 fill transport token: {token}', e)
    need("Copy-Item $themeGround2Pvr" in b, 'build does not stage original theme2 fill PVR', e)
    need('Stage235PvrAtlas blocks, birds, themeGround, themeGround2' in c, 'runtime missing second original fill atlas', e)
    need('{\"stage24/INGAME_THEME_GROUND_2.pvr\", \"INGAME_THEME_GROUND_2.pvr\"}' in c,
         'runtime APK extraction table omits theme2 fill PVR', e)
    need('logical=INGAME_THEME_GROUND_2' in c, 'runtime missing theme2 fill parse telemetry', e)
    need('fillName == "INGAME_THEME_GROUND_1"' in c and 'fillName == "INGAME_THEME_GROUND_2"' in c,
         'MaskedImage consumer does not select fill from producer metadata', e)
    need('m->textureName != "INGAME_THEME_GROUND_1"' not in c,
         'historical hardcoded theme1-only MaskedImage rejection still present', e)
    need('glBindTexture(GL_TEXTURE_2D, fillAtlas->texture);' in c,
         'MaskedImage GPU consumer does not bind selected fill atlas', e)
    need('fillAtlas->width' in c and 'fillAtlas->height' in c,
         'MaskedImage UV producer still uses frozen theme1 dimensions', e)
    # Preserve anti-level-hack boundary.
    for bad in ['Level34") fill', 'Level34\') fill', 'if (levelName == "Level34")']:
        need(bad not in c, f'level-specific fill workaround found: {bad}', e)
    print('ANGRY_STAGE24_35_2_THEME_GROUND_FILL_CONTRACT 1')
    print('policy=producer textureName selects generic MaskedImage fill; original PVR pixels only')
    print('theme1_transport=' + ('PASS' if 'INGAME_THEME_GROUND_1.pvr' in b else 'FAIL'))
    print('theme2_transport=' + ('PASS' if 'INGAME_THEME_GROUND_2.pvr' in b else 'FAIL'))
    print('per_object_fill_selection=' + ('PASS' if 'fillName = m->textureName' in c else 'FAIL'))
    print('theme1_only_rejection_removed=' + ('PASS' if 'm->textureName != "INGAME_THEME_GROUND_1"' not in c else 'FAIL'))
    if e:
        for x in e: print('FAIL:',x)
        return 2
    print('verdict=PASS')
    return 0
if __name__=='__main__': raise SystemExit(main())
