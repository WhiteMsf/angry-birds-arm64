#!/usr/bin/env python3
import pathlib, re, sys

if len(sys.argv) != 2:
    print('usage: patch_box2d212_rovio_tolerances.py <box2d-v2.1.2-root>', file=sys.stderr)
    raise SystemExit(2)

root = pathlib.Path(sys.argv[1])
settings = root / 'Box2D' / 'Box2D' / 'Common' / 'b2Settings.h'
if not settings.is_file():
    print(f'ERROR settings not found: {settings}', file=sys.stderr)
    raise SystemExit(3)

text = settings.read_text(encoding='utf-8')

# Stage24.22.8: values are not guessed. Each replacement is directly recovered
# from untouched ARMv7 libangrybirds.so and is applied only after the stock-source
# audits have run against the pristine pinned 2.1.2 tree.
replacements = [
    (r'(#define\s+b2_linearSlop\s+)0\.005f\b', r'\g<1>0.05f', 'b2_linearSlop', '0.005f', '0.05f', 'SolvePositionConstraints literal 0x3d4ccccd; return threshold -0.075 = -1.5*0.05'),
    (r'(#define\s+b2_timeToSleep\s+)0\.5f\b', r'\g<1>0.25f', 'b2_timeToSleep', '0.5f', '0.25f', 'b2Island::Solve ARMv7 minSleepTime comparison'),
    (r'(#define\s+b2_linearSleepTolerance\s+)0\.01f\b', r'\g<1>0.1f', 'b2_linearSleepTolerance', '0.01f', '0.1f', 'b2Island::Solve compares linear-speed-squared against 0.01 => tolerance 0.1'),
]

out = text
rows = []
for pattern, repl, name, old, new, evidence in replacements:
    out2, n = re.subn(pattern, repl, out, count=1)
    if n != 1:
        print(f'ERROR expected exactly one stock definition for {name}; matches={n}', file=sys.stderr)
        raise SystemExit(4)
    out = out2
    rows.append((name, old, new, evidence))

# Verify constants intentionally left stock because ARMv7 proved they match.
checks = [
    (r'#define\s+b2_velocityThreshold\s+1\.0f\b', 'b2_velocityThreshold=1.0f'),
    (r'#define\s+b2_maxLinearCorrection\s+0\.2f\b', 'b2_maxLinearCorrection=0.2f'),
    (r'#define\s+b2_contactBaumgarte\s+0\.2f\b', 'b2_contactBaumgarte=0.2f'),
    (r'#define\s+b2_polygonRadius\s+\(2\.0f\s*\*\s*b2_linearSlop\)', 'b2_polygonRadius=2*b2_linearSlop'),
]
for pattern, label in checks:
    if not re.search(pattern, out):
        print(f'ERROR expected stock-compatible definition missing: {label}', file=sys.stderr)
        raise SystemExit(5)

settings.write_text(out, encoding='utf-8', newline='\n')

print('ANGRY_STAGE24_22_8_ROVIO_BOX2D_TOLERANCE_PATCH 1')
print('policy=PROVEN_ARMV7_CONSTANTS_ONLY; no Lua lifecycle threshold changes; no restitution/material hacks')
print(f'settings={settings}')
for name, old, new, evidence in rows:
    print(f'patched {name}: {old} -> {new} evidence={evidence}')
print('derived b2_polygonRadius=2*b2_linearSlop=0.1f (now coherent with recovered GameLua polygon m_radius=0.1f)')
print('kept b2_velocityThreshold=1.0f evidence=ARMv7 contact-solver comparison against -1.0f')
print('kept b2_maxLinearCorrection=0.2f evidence=ARMv7 SolvePositionConstraints clamp literal -0.2f')
print('kept b2_contactBaumgarte=0.2f evidence=ARMv7 b2Island::Solve argument literal 0.2f')
print('kept b2_angularSleepTolerance stock evidence=ARMv7 squared literal 0.0012184699 ~= (2deg in rad)^2')
print('expectedEffect=restore internally coherent Rovio tolerance scale so resting contacts can converge/sleep and original Lua speed<0.05 removal/failure lifecycle can operate unchanged')
