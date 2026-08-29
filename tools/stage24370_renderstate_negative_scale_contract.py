#!/usr/bin/env python3
"""Stage 24.37.0 RenderState2D negative-scale / menu-background contract.

Re-audits the original ARMv7 EGL_Image::draw evidence after the live 854x480
trace proved drawLevelSelectionBackground composes LS_BACKGROUND from two
427px draws, one at x=-854 under scaleX=-1.  The contract rejects a
sprite-specific LS_BACKGROUND fix and verifies the generic consumer applies
RenderState2D scale after local rotation/pivot + draw-origin translation.
"""
from __future__ import annotations
from pathlib import Path
import math, re, sys

HEADER='ANGRY_STAGE24_37_0_RENDERSTATE_NEGATIVE_SCALE_CONTRACT 1'

def fn_slice(src: str, needle: str, cap: int=12000) -> str:
    pos=src.find(needle)
    if pos < 0: return ''
    brace=src.find('{',pos)
    if brace < 0: return src[pos:pos+cap]
    depth=0
    for i in range(brace,min(len(src),pos+cap)):
        if src[i]=='{': depth+=1
        elif src[i]=='}':
            depth-=1
            if depth==0: return src[pos:i+1]
    return src[pos:pos+cap]

def transform(draw_left, draw_top, w, h, tx, ty, sx, sy, angle, px, py):
    c=math.cos(angle); sn=math.sin(angle)
    base_x=draw_left+tx+px; base_y=draw_top+ty+py
    out=[]
    for lx,ly in ((0,0),(w,0),(0,h),(w,h)):
        dx=lx-px; dy=ly-py
        rx=base_x+c*dx-sn*dy
        ry=base_y+sn*dx+c*dy
        out.append((sx*rx,sy*ry))
    return out

def bounds(v):
    xs=[p[0] for p in v]; ys=[p[1] for p in v]
    return min(xs),min(ys),max(xs),max(ys)

def old_local_scale_bounds(draw_left,w,sx):
    # identity angle/pivot/translation, old Stage24.31.5b ordering
    xs=[draw_left+sx*0,draw_left+sx*w]
    return min(xs),max(xs)

def main():
    if len(sys.argv)!=3:
        print('usage: stage24370_renderstate_negative_scale_contract.py <stage24.31.4a-armv7-report> <stage24.cpp>',file=sys.stderr)
        return 2
    arm=Path(sys.argv[1]).read_text(encoding='utf-8-sig',errors='replace')
    cpp=Path(sys.argv[2]).read_text(encoding='utf-8',errors='replace')
    xform=fn_slice(cpp,'void stage24315bTransformQuad(')
    sprite=fn_slice(cpp,'bool stage24132DrawSprite(')
    print(HEADER)
    print('policy=GENERIC_RENDERSTATE_CONSUMER; no LS_BACKGROUND geometry special-case')
    print('liveTrigger=drawLevelSelectionBackground emits x=-854,width=427,scaleX=-1 plus x=0,width=427,scaleX=+1 on 854x480')
    print('recoveredSemantic=screen=S(scale)*(drawOrigin+translation+pivot+R(angle)*(localCorner-pivot))')

    arm_checks={
        'eglImageFloatDraw': 'gr::EGL_Image::draw(gr::Context*, float, float, float, float, math::float2 const*)' in arm,
        'rotationMatrixFields': all(x in arm for x in ('#0x10','#0x14','#0x18','#0x1c')),
        'translationFields': all(x in arm for x in ('#0x20','#0x24')),
        'screenScaleFields': all(x in arm for x in ('#0x28','#0x2c')),
        'pivotFields': all(x in arm for x in ('#0x30','#0x34')),
        'affineOps': all(x in arm for x in ('__mulsf3','__aeabi_fadd','__subsf3')),
    }
    print('[ARMV7_EVIDENCE]')
    for k,v in arm_checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')

    src_checks={
        'genericHelperPresent': bool(xform),
        'localRotation': 'rotatedX = baseX + c * dx - sn * dy' in xform and 'rotatedY = baseY + sn * dx + c * dy' in xform,
        'postAffineScaleX': 'outVerts[i*2+0] = stage24313RenderSx * rotatedX' in xform,
        'postAffineScaleY': 'outVerts[i*2+1] = stage24313RenderSy * rotatedY' in xform,
        'oldLocalScaleRemoved': 'm00 = c * stage24313RenderSx' not in xform and 'm01 = -sn * stage24313RenderSy' not in xform,
        'pivotRetained': 'localX[i] - px' in xform and 'localY[i] - py' in xform,
        'drawOriginRetained': 'drawLeft + stage24313RenderX + px' in xform and 'drawTop + stage24313RenderY + py' in xform,
        'spriteUsesGenericHelper': 'stage24315bTransformQuad(left, top, w, h, verts)' in sprite,
        'noBackgroundSpecialCaseInTransform': 'LS_BACKGROUND' not in xform,
        'observerOnlyBackgroundMention': '[stage24.37.0-renderstate] DRAW' in sprite,
    }
    print('[ARM64_SOURCE_GUARDS]')
    for k,v in src_checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')

    right=bounds(transform(-854,0,427,480,0,0,-1,1,0,0,0))
    left=bounds(transform(0,0,427,480,0,0,1,1,0,0,0))
    union=(min(right[0],left[0]),min(right[1],left[1]),max(right[2],left[2]),max(right[3],left[3]))
    old=old_local_scale_bounds(-854,427,-1)
    eps=1e-5
    math_checks={
        'mirroredHalf': abs(right[0]-427)<eps and abs(right[2]-854)<eps,
        'normalHalf': abs(left[0]-0)<eps and abs(left[2]-427)<eps,
        'full854Coverage': abs(union[0]-0)<eps and abs(union[2]-854)<eps and abs(union[1]-0)<eps and abs(union[3]-480)<eps,
        'oldOrderingReproducesBug': abs(old[0]+1281)<eps and abs(old[1]+854)<eps,
    }
    print('[MATH_PROOF]')
    print(f'newMirroredBounds=({right[0]:.3f},{right[1]:.3f})-({right[2]:.3f},{right[3]:.3f}) expectedX=427..854')
    print(f'newNormalBounds=({left[0]:.3f},{left[1]:.3f})-({left[2]:.3f},{left[3]:.3f}) expectedX=0..427')
    print(f'newUnionBounds=({union[0]:.3f},{union[1]:.3f})-({union[2]:.3f},{union[3]:.3f}) expected=0..854 x 0..480')
    print(f'oldMirroredXBounds=({old[0]:.3f},{old[1]:.3f}) expectedBug=-1281..-854 offscreen')
    for k,v in math_checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')

    anti_hack=not re.search(r'if\s*\([^\n]*(LS_BACKGROUND)',xform,re.I)
    print(f'antiLSBackgroundTransformHack={"PASS" if anti_hack else "FAIL"}')
    ok=all(arm_checks.values()) and all(src_checks.values()) and all(math_checks.values()) and anti_hack
    print('VERDICT='+('PASS' if ok else 'FAIL'))
    return 0 if ok else 3

if __name__=='__main__':
    raise SystemExit(main())
