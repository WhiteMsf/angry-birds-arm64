#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    print('usage: stage24314f_composited_presentation_contract.py <stage24_live_surface.cpp>')
    raise SystemExit(2)

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8', errors='replace')

checks = [
    ('legacy raster remains 1:1', 'viewportW = std::min(logicalW, surfaceW);' in s and 'viewportH = std::min(logicalH, surfaceH);' in s),
    ('separate presentation viewport exists', 'presentationViewportW' in s and 'presentationViewportH' in s and 'presentScale' in s),
    ('presentation POT texture exists', 'presentationBackingW = stage24314c_next_pow2' in s and 'presentationTextureReady = true;' in s),
    ('frame copied only after legacy raster', 'glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0,' in s and 'viewportX, viewportY, logicalW, logicalH' in s),
    ('single post-composite scale draw exists', 'stage24314fPresentLogicalFrame' in s and 'GL_TRIANGLE_STRIP' in s and 'LEGACY_1TO1_THEN_COMPOSITE_UPSCALE' in s),
    ('presentation texture padding isolated', 'half-texel inset belongs ONLY to the new presentation texture' in s),
    ('legacy atlas half-texel remains disabled', 'static constexpr bool STAGE24314_APPLY_HALF_TEXEL_FIX = false;' in s),
    ('menu path presents before swap', 'stage24314fPresentLogicalFrame("menu", frame)' in s),
    ('boot path presents before swap', 'stage24314fPresentLogicalFrame("boot", frame)' in s),
    ('gameplay path presents before swap', 'stage24314fPresentLogicalFrame("gameplay", frame)' in s),
    ('touch maps visible output back to logical', 'inputMap=OUTPUT_VIEWPORT_TO_LOGICAL' in s and 'usePresentation ? presentationViewportX : viewportX' in s),
    ('menu touch maps visible output back to logical', 'usePresentation ? presentationViewportX : menuViewportX' in s),
    ('presentation resource cleaned up', 'glDeleteTextures(1, &presentationTexture);' in s),
    ('native path bypasses compatibility layer', 'if (!gStage24201DebugDisplay) return true;' in s),
]

print('ANGRY_STAGE24_31_4F_COMPOSITED_PRESENTATION_CONTRACT 1')
print(f'source={p}')
print('policy=legacy renderer rasterizes 1:1; only finished frame may be scaled for modern presentation')
failed = 0
for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'} {name}")
    failed += 0 if ok else 1

# Explicitly forbid regression back to direct logical->physical sprite magnification.
forbidden = [
    'viewportW = presentationViewportW;',
    'menuViewportW = presentationViewportW;',
    'STAGE24314_APPLY_HALF_TEXEL_FIX = true',
]
for token in forbidden:
    ok = token not in s
    print(f"{'PASS' if ok else 'FAIL'} forbidden_absent={token}")
    failed += 0 if ok else 1

print(f'result={"PASS" if failed == 0 else "FAIL"} failures={failed}')
raise SystemExit(1 if failed else 0)
