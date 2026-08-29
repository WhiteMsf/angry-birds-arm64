#!/usr/bin/env python3
"""Stage24.44.0: reconstruct Rovio's mutable Box2D max-translation globals."""
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    print('usage: patch_box2d212_rovio_max_translation.py <box2d-v2.1.2-root>', file=sys.stderr)
    raise SystemExit(2)

root=Path(sys.argv[1])
header=root/'Box2D'/'Box2D'/'Common'/'b2Settings.h'
source=root/'Box2D'/'Box2D'/'Common'/'b2Settings.cpp'
if not header.is_file() or not source.is_file():
    print(f'ERROR missing Box2D settings pair header={header} source={source}', file=sys.stderr)
    raise SystemExit(3)

h=header.read_text(encoding='utf-8',errors='replace')
s=source.read_text(encoding='utf-8',errors='replace')
stock_a=re.compile(r'^\s*#define\s+b2_maxTranslation\s+2\.0f\s*$',re.M)
stock_b=re.compile(r'^\s*#define\s+b2_maxTranslationSquared\s+\(b2_maxTranslation\s*\*\s*b2_maxTranslation\)\s*$',re.M)
patched_h=('extern float32 b2_maxTranslation;' in h and
           'extern float32 b2_maxTranslationSquared;' in h)
marker='ANGRY_STAGE24_44_0_ROVIO_MUTABLE_MAX_TRANSLATION'
patched_s=(marker in s and
           'float32 b2_maxTranslation = 2.0f;' in s and
           'float32 b2_maxTranslationSquared = 4.0f;' in s)

if patched_h or patched_s:
    if not (patched_h and patched_s):
        print('ERROR partial prior max-translation patch detected', file=sys.stderr)
        raise SystemExit(4)
    print('ANGRY_STAGE24_44_0_ROVIO_MAX_TRANSLATION_PATCH 1')
    print('status=ALREADY_PATCHED')
    print(f'header={header}')
    print(f'source={source}')
    raise SystemExit(0)

if not stock_a.search(h) or not stock_b.search(h):
    print('ERROR expected pristine Box2D 2.1.2 max-translation macros not found', file=sys.stderr)
    raise SystemExit(5)

h=stock_a.sub('extern float32 b2_maxTranslation;',h,count=1)
h=stock_b.sub('extern float32 b2_maxTranslationSquared;',h,count=1)
append="""

// ANGRY_STAGE24_44_0_ROVIO_MUTABLE_MAX_TRANSLATION
// Untouched ARMv7 GameLua::setMaxTranslation(float) writes value and value^2
// to two writable globals. Stock 2.1.2 used macros; Rovio's shipping fork did not.
float32 b2_maxTranslation = 2.0f;
float32 b2_maxTranslationSquared = 4.0f;
"""
s=s.rstrip()+append+'\n'
header.write_text(h,encoding='utf-8',newline='\n')
source.write_text(s,encoding='utf-8',newline='\n')

print('ANGRY_STAGE24_44_0_ROVIO_MAX_TRANSLATION_PATCH 1')
print('status=PATCHED')
print('stockMacro.b2_maxTranslation=2.0f PASS')
print('stockMacro.b2_maxTranslationSquared=(b2_maxTranslation*b2_maxTranslation) PASS')
print('armv7Evidence=GameLua::setMaxTranslation stores input then __mulsf3(input,input) into second writable global')
print('patchedHeader=extern float32 b2_maxTranslation; extern float32 b2_maxTranslationSquared;')
print('patchedSource=float32 b2_maxTranslation=2.0f; float32 b2_maxTranslationSquared=4.0f;')
print('scope=ONLY_MAX_TRANSLATION_PAIR; no maxRotation/sleep/contact/tolerance changes')
print(f'header={header}')
print(f'source={source}')
