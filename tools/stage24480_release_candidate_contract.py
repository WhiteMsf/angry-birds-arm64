#!/usr/bin/env python3
from __future__ import annotations
import hashlib, pathlib, re, sys

if len(sys.argv) < 2:
    print('usage: stage24480_release_candidate_contract.py <root> [baseline-root]')
    raise SystemExit(2)

root = pathlib.Path(sys.argv[1]).resolve()
baseline = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None


def read(rel: str) -> str:
    return (root / rel).read_text(encoding='utf-8-sig', errors='replace')

def sha(rel: str, base: pathlib.Path | None = None) -> str:
    p = (base or root) / rel
    return hashlib.sha256(p.read_bytes()).hexdigest()

cmake = read('CMakeLists.txt')
build = read('build-stage24-live-surface-touch-arm64.ps1')
manifest = read('stage24-android/AndroidManifest.xml')
source = read('stage24_live_surface.cpp')

checks: list[tuple[str, bool, str]] = []
debt: list[tuple[str, str]] = []

def ck(name: str, cond: bool, detail: str):
    checks.append((name, cond, detail))

def add_debt(name: str, detail: str):
    debt.append((name, detail))

ck('cmake_release_build', '-DCMAKE_BUILD_TYPE=Release' in build, 'build script configures CMAKE_BUILD_TYPE=Release')
ck('arm64_only_build_abi', '-DANDROID_ABI=arm64-v8a' in build, 'build script targets arm64-v8a')
ck('apk_arm64_lib_path', "'lib/arm64-v8a/libangryarm64.so'" in build, 'APK injection path is lib/arm64-v8a/libangryarm64.so')
ck('no_armv7_runtime_injection', not re.search(r"apk_add_native_lib.*(?:armeabi-v7a|armeabi)(?!64)", build, re.I), 'no build-script ARMv7 library injection')
ck('box2d_fp_contract_off', bool(re.search(r'target_compile_options\(box2d212\s+PRIVATE[\s\S]*?-ffp-contract=off', cmake)), 'Box2D compiles with -ffp-contract=off')
ck('live_bridge_fp_contract_off', bool(re.search(r'target_compile_options\(stage24_live_surface\s+PRIVATE\s+-ffp-contract=off\)', cmake)), 'live physics bridge compiles with -ffp-contract=off')
ck('term_window_preserves_engine', 'APP_CMD_TERM_WINDOW' in source and 'PRESERVE_ENGINE' in source, 'Stage24.47.6 lifecycle preservation marker present')
ck('destroy_is_teardown_boundary', 'APP_CMD_DESTROY' in source and 'stage24_stop_engine' in source, 'explicit destroy/teardown path present')
external_asset_contract = (
    "[string]$OriginalRoot = ''" in build
    and 'ANGRY_BIRDS_ORIGINAL_ROOT' in build
    and '$angryReRoot = [IO.Path]::GetFullPath($OriginalRoot)' in build
    and "$dataRoot = Join-Path $angryReRoot 'assets\\data'" in build
    and not re.search(r'\$dataRoot\s*=\s*Join-Path\s+\$root\b', build, re.I)
)
ck(
    'user_assets_external_to_source',
    external_asset_contract,
    'original asset root is caller/environment supplied and dataRoot derives from that external root, never from the source tree'
)

runtime_files = ['stage24_live_surface.cpp', 'CMakeLists.txt']
baseline_manifest = root / 'tools' / 'stage24480_baseline_sha256.txt'
if baseline_manifest.exists():
    expected = {}
    for line in baseline_manifest.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        h, rel = line.split(None, 1)
        expected[rel.strip()] = h.lower()
    for rel in runtime_files:
        cur = sha(rel)
        old = expected.get(rel, '')
        ck('baseline_identical_' + re.sub(r'[^A-Za-z0-9]+', '_', rel).strip('_'), bool(old) and cur == old, f'{rel} current={cur} baseline={old or "<missing>"}')
elif baseline:
    for rel in runtime_files:
        cur = sha(rel)
        old = sha(rel, baseline)
        ck('baseline_identical_' + re.sub(r'[^A-Za-z0-9]+', '_', rel).strip('_'), cur == old, f'{rel} current={cur} baseline={old}')
else:
    ck('baseline_manifest_present', False, 'tools/stage24480_baseline_sha256.txt missing')

# Release-envelope debt: these are intentionally warnings in 48.0, not build failures.
if 'android:debuggable="true"' in manifest:
    add_debt('manifest_debuggable', 'android:debuggable=true must be removed/false for the final release envelope')
m = re.search(r'android:versionName="([^"]+)"', manifest)
if m and m.group(1) != '1.0.0':
    add_debt('manifest_version_name', f'current versionName={m.group(1)!r}; final release should be 1.0.0')
m = re.search(r'android:label="([^"]+)"', manifest)
if m and 'Stage 24' in m.group(1):
    add_debt('manifest_stage_label', f'current application label={m.group(1)!r} still exposes test-stage branding')
m = re.search(r'package="([^"]+)"', manifest)
if m and '.stage24' in m.group(1):
    add_debt('manifest_stage_package', f'current package={m.group(1)!r} is development-stage identity; decide whether to retain or rename before 1.0')
if 'androiddebugkey' in build or 'debugKey' in build:
    add_debt('debug_signing', 'build script signs the APK with the Android debug key; final distribution signing remains open')
if 'angry-arm64-stage24-debug.apk' in build:
    add_debt('debug_apk_filename', 'output filename still carries stage24-debug naming')

passed = sum(1 for _, ok, _ in checks if ok)
failed = [(n,d) for n,ok,d in checks if not ok]
print('ANGRY_STAGE24_48_0_RELEASE_CANDIDATE_CONTRACT 1')
print(f'engine_checks={passed}/{len(checks)}')
for name, ok, detail in checks:
    print(f'{name}={"PASS" if ok else "FAIL"} :: {detail}')
print(f'release_debt_count={len(debt)}')
for name, detail in debt:
    print(f'release_debt.{name}=OPEN :: {detail}')
if failed:
    print('engine_verdict=FAIL')
    print('release_candidate_verdict=FAIL_ENGINE_BASELINE')
    raise SystemExit(1)
print('engine_verdict=PASS')
print('release_packaging_ready=' + ('YES' if not debt else 'NO'))
print('release_candidate_verdict=' + ('PASS' if not debt else 'PASS_WITH_PACKAGING_DEBT'))
