#!/usr/bin/env python3
from __future__ import annotations
import pathlib, sys, zipfile

if len(sys.argv) != 2:
    print('usage: stage24480_apk_payload_audit.py <apk>')
    raise SystemExit(2)
apk = pathlib.Path(sys.argv[1])
with zipfile.ZipFile(apk) as z:
    names = z.namelist()
libs = sorted(n for n in names if n.startswith('lib/') and n.endswith('.so'))
armv7 = [n for n in libs if n.startswith('lib/armeabi/') or n.startswith('lib/armeabi-v7a/')]
arm64 = [n for n in libs if n.startswith('lib/arm64-v8a/')]
expected = ['lib/arm64-v8a/libangryarm64.so']
print('ANGRY_STAGE24_48_0_APK_PAYLOAD_AUDIT 1')
print('native_lib_entries=' + (','.join(libs) if libs else '<none>'))
print('armv7_runtime_entries=' + str(len(armv7)))
print('arm64_runtime_entries=' + str(len(arm64)))
print('expected_single_runtime_lib=' + ('PASS' if libs == expected else 'FAIL'))
print('no_armv7_runtime=' + ('PASS' if not armv7 else 'FAIL'))
print('verdict=' + ('PASS' if libs == expected and not armv7 else 'FAIL'))
raise SystemExit(0 if libs == expected and not armv7 else 1)
