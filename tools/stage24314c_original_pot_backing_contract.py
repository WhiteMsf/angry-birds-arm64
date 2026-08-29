#!/usr/bin/env python3
"""Stage 24.31.4c — canonical EGL_Image POT-backing reconstruction guard."""
from __future__ import annotations
import pathlib,sys
HEADER='ANGRY_STAGE24_31_4C_ORIGINAL_EGL_IMAGE_POT_BACKING_CONTRACT 1'

def main():
    if len(sys.argv)!=2:
        print('usage: stage24314c_original_pot_backing_contract.py <project-cpp>',file=sys.stderr); return 2
    src=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8',errors='replace')
    checks={
        'halfTexelDisabled':'STAGE24314_APPLY_HALF_TEXEL_FIX = false' in src,
        'logicalBackingSeparated':'uint32_t backingWidth = 0;' in src and 'uint32_t backingHeight = 0;' in src,
        'nextPow2Recovered':'stage24314c_next_pow2' in src and 'x |= x >> 16u' in src,
        'parseAssignsBacking':'atlas->backingWidth = stage24314c_next_pow2' in src and 'atlas->backingHeight = stage24314c_next_pow2' in src,
        'edgeUvUsesBacking':'static_cast<GLfloat>(sp->x) / atlas->backingWidth' in src and 'static_cast<GLfloat>(sp->x + sp->width) / atlas->backingWidth' in src,
        'potAllocate':'static_cast<GLsizei>(backingW)' in src and 'static_cast<GLsizei>(backingH)' in src,
        'logicalSubimage':'static_cast<GLsizei>(logicalW)' in src and 'static_cast<GLsizei>(logicalH)' in src,
        'minFilterContract':'GL_LINEAR_MIPMAP_NEAREST' in src and 'completeMipChain ? GL_LINEAR_MIPMAP_NEAREST : GL_LINEAR' in src,
        'magLinear':'GL_TEXTURE_MAG_FILTER, GL_LINEAR' in src,
        'runtimeTelemetry':'[stage24.31.4c-texture] UPLOAD' in src and '[stage24.31.4c-image] EDGE_POT_BACKING' in src,
        'failClosedEtc1NonPot':'ETC1 non-POT backing unsupported' in src,
        'tutorialPresent':'l_stage24312_res_drawCompoSprite' in src,
        'persistencePresent':'l_stage24311_saveLuaFile' in src,
    }
    print(HEADER)
    print('architecture=EGL_Image keeps logical image size; constructor rounds each dimension to next POT before createTexture; EGL_Image::draw normalizes integer source rectangles by EGL_Texture::width/height')
    print('uv=edge-to-edge; no half-texel correction')
    print('sampler=MIN LINEAR unless full mip chain then LINEAR_MIPMAP_NEAREST; MAG LINEAR')
    print('upload=allocate physical POT backing, then blt logical pixels at origin')
    print('\n[GUARDS]')
    for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
    ok=all(checks.values())
    print('\nVERDICT=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 3
if __name__=='__main__': raise SystemExit(main())
