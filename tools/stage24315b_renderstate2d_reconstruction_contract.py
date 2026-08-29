#!/usr/bin/env python3
"""Stage 24.31.5b original RenderState2D consumer reconstruction contract.

Read-only ARMv7 evidence + ARM64 source guards.  Stage24.31.5 established that
untouched Lua supplies the expected angles/pivots for the Main Menu gear and
About Golden Egg star effect.  The remaining mismatch is the consumer: original
EGL_Image::draw rotates image-local corners around the per-image pivot, adds the
per-draw destination/translation, and only then applies RenderState2D scale to
the resulting screen coordinate.  The old ARM64 bridge applied one GL model
matrix to vertices that were already in world/screen coordinates; the initial
Stage24.31.5b reconstruction fixed pivot/rotation but incorrectly folded scale
into the local matrix.  Stage24.37.0 corrects that remaining ordering error.

This tool does not select values by sprite name.  It verifies one global
per-image affine rule and fails if a target-specific branch is introduced in the
new transform functions.
"""
from __future__ import annotations
import pathlib, re, subprocess, sys
from dataclasses import dataclass

HEADER = 'ANGRY_STAGE24_31_5B_RENDERSTATE2D_RECONSTRUCTION_CONTRACT 1'

@dataclass
class Sym:
    addr: int
    size: int
    typ: str
    name: str

def run(args):
    try:
        p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, errors='replace', check=False)
        return p.returncode, p.stdout.splitlines()
    except Exception as e:
        return -1, [f'exception={e}']

def parse_nm(lines):
    rx = re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    out = []
    for ln in lines:
        m = rx.match(ln)
        if m:
            out.append(Sym(int(m.group(1), 16), int(m.group(2), 16), m.group(3), m.group(4)))
    return out

def body(objdump, lib, s, max_size=0x700):
    start = s.addr & ~1
    size = min(max(s.size or 0x80, 0x40), max_size)
    rc, lines = run([objdump, '-d', '--demangle', f'--start-address=0x{start:x}',
                     f'--stop-address=0x{start+size:x}', lib])
    print(f"[ARMV7_BODY] name={s.name!r} start=0x{start:x} size=0x{size:x} objdumpExit={rc} lines={len(lines)}")
    for ln in lines:
        print(ln)
    return rc, lines

def function_slice(src: str, signature_needle: str, max_chars=9000):
    pos = src.find(signature_needle)
    if pos < 0:
        return ''
    brace = src.find('{', pos)
    if brace < 0:
        return src[pos:pos+max_chars]
    depth = 0
    for i in range(brace, min(len(src), pos + max_chars)):
        if src[i] == '{': depth += 1
        elif src[i] == '}':
            depth -= 1
            if depth == 0:
                return src[pos:i+1]
    return src[pos:pos+max_chars]

def main():
    if len(sys.argv) != 5:
        print('usage: stage24315b_renderstate2d_reconstruction_contract.py <llvm-nm> <llvm-objdump> <armv7-lib> <project-cpp>', file=sys.stderr)
        return 2
    nm, objdump, lib, cpp = sys.argv[1:]
    print(HEADER)
    print('policy=RECOVERED_GLOBAL_CONSUMER; no sprite-name fixes; score observer remains passive')
    print('recoveredSemantic=screen = S(scale) * (drawOrigin + translation + pivot + R(angle)*(localCorner-pivot))')
    print('architecturalDifference=ARMv7 transforms each image-local quad inside EGL_Image::draw; old ARM64 transformed already-world-space vertices with one GL_MODELVIEW matrix')

    rc, nml = run([nm, '-S', '-C', lib])
    if rc != 0 or not nml:
        rc, nml = run([nm, '-D', '-S', '-C', lib])
    syms = parse_nm(nml)
    print(f'[SYMBOLS] nmExit={rc} parsed={len(syms)}')

    want = 'gr::EGL_Image::draw(gr::Context*, float, float, float, float, math::float2 const*)'
    hits = [s for s in syms if s.name == want]
    if not hits:
        hits = [s for s in syms if s.name.startswith('gr::EGL_Image::draw(gr::Context*, float, float, float, float,')]
    print(f'[ARMV7_EGL_IMAGE_FLOAT_DRAW] hits={len(hits)}')
    arm_lines = []
    if hits:
        _, arm_lines = body(objdump, lib, hits[0])

    arm_text = '\n'.join(arm_lines)
    # Offsets recovered in the .101 disassembly: 0x10..0x1c affine matrix,
    # 0x20/0x24 translation, 0x30/0x34 pivot.  Require all of them in the
    # original image-draw body so this preflight cannot silently drift to the
    # wrong overload/layer.
    required_offsets = ['#0x10', '#0x14', '#0x18', '#0x1c', '#0x20', '#0x24', '#0x28', '#0x2c', '#0x30', '#0x34']
    print('[ARMV7_FIELD_EVIDENCE]')
    offset_ok = True
    for off in required_offsets:
        present = off in arm_text
        offset_ok &= present
        print(f'offset_{off[1:]}={"PASS" if present else "FAIL"}')
    has_mul = '__mulsf3' in arm_text
    has_add = '__aeabi_fadd' in arm_text
    has_sub = '__subsf3' in arm_text
    print(f'affineMul={"PASS" if has_mul else "FAIL"}')
    print(f'affineAdd={"PASS" if has_add else "FAIL"}')
    print(f'pivotSubtract={"PASS" if has_sub else "FAIL"}')

    src_path = pathlib.Path(cpp)
    src = src_path.read_text(encoding='utf-8', errors='replace') if src_path.is_file() else ''
    set_fn = function_slice(src, 'void stage24132SetRenderState(')
    xform_fn = function_slice(src, 'void stage24315bTransformQuad(')
    sprite_fn = function_slice(src, 'bool stage24132DrawSprite(')
    rect_fn = function_slice(src, 'void stage24132DrawRect(')
    font_fn = function_slice(src, 'bool stage24134DrawString(')

    checks = {
        'setStateStoresTranslation': 'stage24313RenderX = x' in set_fn and 'stage24313RenderY = y' in set_fn,
        'setStateStoresScaleAnglePivot': 'stage24313RenderSx = sx' in set_fn and 'stage24313RenderAngle = angle' in set_fn and 'stage24313RenderPivotX = pivotX' in set_fn,
        'setStateKeepsModelIdentity': 'glMatrixMode(GL_MODELVIEW)' in set_fn and 'glLoadIdentity()' in set_fn,
        'oldGlobalModelRemovedFromSetState': 'glLoadMatrixf(model)' not in set_fn and 'const GLfloat model[16]' not in set_fn,
        'perDrawHelperExists': bool(xform_fn),
        'perDrawOriginOutsideAffine': 'drawLeft + stage24313RenderX + px' in xform_fn and 'drawTop + stage24313RenderY + py' in xform_fn,
        'localPivotSubtract': 'localX[i] - px' in xform_fn and 'localY[i] - py' in xform_fn,
        'rotationLocalScalePostAffine': 'rotatedX = baseX + c * dx - sn * dy' in xform_fn and 'rotatedY = baseY + sn * dx + c * dy' in xform_fn and 'outVerts[i*2+0] = stage24313RenderSx * rotatedX' in xform_fn and 'outVerts[i*2+1] = stage24313RenderSy * rotatedY' in xform_fn,
        'oldLocalScaleOrderingRemoved': 'm00 = c * stage24313RenderSx' not in xform_fn and 'm01 = -sn * stage24313RenderSy' not in xform_fn,
        'spriteUsesPerDrawHelper': 'stage24315bTransformQuad(left, top, w, h, verts)' in sprite_fn,
        'rectUsesPerDrawHelper': 'stage24315bTransformQuad(x0, y0, x1 - x0, y1 - y0, verts)' in rect_fn,
        'fontUsesPerDrawHelper': 'stage24315bTransformQuad(left, top,' in font_fn,
        # Stage24.37.0 inserts its bounded negative-scale observer earlier in
        # stage24132DrawSprite().  Do not make this inherited guard depend on a
        # fixed character window reaching the older 24.31.3 transformed-corner
        # printf.  Accept either the new semantic screen-bounds observer or the
        # retained legacy transformed-corner telemetry.
        'targetTelemetryHasTransformedCorners': (
            ('[stage24.37.0-renderstate]' in sprite_fn and
             'bounds=(' in sprite_fn and
             'ARMV7_POST_AFFINE_SCREEN_SCALE' in sprite_fn) or
            ('transformedTL=' in sprite_fn and 'transformedBR=' in sprite_fn)
        ),
        'presentationClosureRetained': '[stage24.31.4f-presentation] PRESENT_PASS' in src,
        'passiveScoreObserverRetained': '[stage24.31.5-score-passive]' in src and 'action=OBSERVE_ONLY' in src,
    }
    print('[ARM64_RECONSTRUCTION_GUARDS]')
    for k, v in checks.items():
        print(f'{k}={"PASS" if v else "FAIL"}')

    target_branch_rx = re.compile(r'if\s*\([^\n]*(BUTTON_OPTIONS|GOLDEN_EGG_STAR_EFFECT)', re.I)
    anti_target = not target_branch_rx.search(set_fn + '\n' + xform_fn + '\n' + sprite_fn)
    print(f'antiSpriteNameFix={"PASS" if anti_target else "FAIL"}')
    print('[VALIDATION_EXPECTATION]')
    print('gear=BUTTON_OPTIONS retains local pivot rotation; scale=1 path is unchanged by Stage24.37.0 ordering correction')
    print('goldenEgg=GOLDEN_EGG_STAR_EFFECT retains local pivot rotation; scale=1 path is unchanged by Stage24.37.0 ordering correction')
    print('regressionGuard=menu/cutscene/text rendering must remain correct because the fix is one global image-consumer semantic')

    ok = bool(hits) and offset_ok and has_mul and has_add and has_sub and all(checks.values()) and anti_target
    print('VERDICT=' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 3

if __name__ == '__main__':
    raise SystemExit(main())
