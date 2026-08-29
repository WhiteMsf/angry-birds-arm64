#!/usr/bin/env python3
from __future__ import annotations
import hashlib, pathlib, re, subprocess, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: stage24490_release_engineering_contract.py <root>')
root = pathlib.Path(sys.argv[1]).resolve()

def read(rel: str) -> str:
    return (root / rel).read_text(encoding='utf-8-sig', errors='replace')

def sha(rel: str) -> str:
    return hashlib.sha256((root / rel).read_bytes()).hexdigest()

build = read('build-stage24-live-surface-touch-arm64.ps1')
audit_manifest = read('stage24-android/AndroidManifest.xml')
release_manifest = read('stage24-android/AndroidManifest.release.xml')
cmake = read('CMakeLists.txt')
source = read('stage24_live_surface.cpp')
expected = {}
for line in (root / 'tools/stage24480_baseline_sha256.txt').read_text().splitlines():
    line=line.strip()
    if not line or line.startswith('#'): continue
    h, rel = line.split(None,1)
    expected[rel.strip()] = h.lower()

checks=[]
def ck(name, ok, detail): checks.append((name,bool(ok),detail))

ck('runtime_cpp_frozen', sha('stage24_live_surface.cpp') == expected.get('stage24_live_surface.cpp'), f"sha={sha('stage24_live_surface.cpp')}")
ck('runtime_cmake_frozen', sha('CMakeLists.txt') == expected.get('CMakeLists.txt'), f"sha={sha('CMakeLists.txt')}")
ck('build_flavors', "[ValidateSet('Audit','Release')]" in build and "$BuildFlavor = 'Audit'" in build, 'Audit/Release flavors explicit')
ck('release_package', 'package="dev.angryarm64.angrybirds"' in release_manifest, 'final package id')
ck('release_version_name', 'android:versionName="1.0.0"' in release_manifest, 'final semantic version')
ck('release_version_code', 'android:versionCode="1000000"' in release_manifest, 'monotonic semver-friendly code')
ck('release_not_debuggable', 'android:debuggable="false"' in release_manifest and 'android:debuggable="true"' not in release_manifest, 'release manifest non-debuggable')
ck('release_branding', 'android:label="Angry Birds"' in release_manifest and 'android:icon="@drawable/app_icon"' in release_manifest, 'label/icon final')
ck('release_arm64_nativeactivity', 'android.app.NativeActivity' in release_manifest and 'android:value="angryarm64"' in release_manifest, 'NativeActivity loads reconstructed arm64 engine')
ck('audit_identity_retained', 'package="dev.angryarm64.stage24"' in audit_manifest and 'android:debuggable="true"' in audit_manifest, 'audited lab app remains side-by-side')
ck('release_key_external', "$ReleaseKeystore" in build and 'Release build requires -ReleaseKeystore' in build, 'release key injected from external path')
ck('release_password_env', 'ReleasePasswordEnv' in build and 'env:$ReleasePasswordEnv' in build, 'password is not embedded on command line as literal')
ck('release_signatures', '--v1-signing-enabled true' in build and '--v2-signing-enabled true' in build and '--v3-signing-enabled true' in build, 'v1/v2/v3 signing explicitly enabled')
ck('release_filename', "Angry-Birds-1.0.0-arm64-v8a.apk" in build, 'public artifact filename')
ck('audit_filename', "angry-arm64-stage24-audited.apk" in build, 'audited artifact filename')
ck('fp_contract', '-ffp-contract=off' in cmake, 'physics FP contraction fidelity retained')
ck('lifecycle_contract', 'PRESERVE_ENGINE' in source and 'APP_CMD_TERM_WINDOW' in source, 'multitask resume contract retained')
ck('zip_timezone_timestamp_guard', 'CMake timestamp guard PASS' in build and "LastWriteTime = $cmakeStampSafe" in build and "AddSeconds(-10)" in build, 'timezone-naive ZIP extraction cannot trap Ninja in RERUN_CMAKE')
ck('canonical_manifest_staging', "$packageManifest = Join-Path $packageManifestDir 'AndroidManifest.xml'" in build and 'Canonical manifest staging PASS' in build and '$manifestSourceHash -ne $manifestStagedHash' in build, 'selected flavor manifest is byte-checked then staged with canonical basename for legacy aapt')
ck('aapt_exit_preserved', '$aaptExit = $LASTEXITCODE' in build and 'aapt package failed: $aaptExit' in build, 'aapt failure code captured before SUBST cleanup')
branding_contract = subprocess.run(
    [sys.executable, str(root / 'tools/stage24481_release_branding_contract.py'), str(root)],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    check=False,
)
ck('branding_contract_preflight', branding_contract.returncode == 0, 'nested Stage24.48.1 branding/version contract passes before either envelope is built')
credit_contract = subprocess.run(
    [sys.executable, str(root / 'tools/stage24491_in_game_credit_contract.py'), str(root)],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    check=False,
)
ck('in_game_credit_contract', credit_contract.returncode == 0, 'nested Stage24.49.1 in-game attribution contract passes')
release_orchestrator = read('build-angry-birds-1.0.0-release.ps1')
ck('adb_probe_nonfatal', 'function Test-AdbDevice' in release_orchestrator and "$ErrorActionPreference = 'SilentlyContinue'" in release_orchestrator and 'if (Test-AdbDevice)' in release_orchestrator, 'disconnected adb probe cannot abort release packaging')

# No obvious release password literals in source tree.
secret_patterns=[r'ANGRY_BIRDS_RELEASE_STOREPASS\s*=\s*[\'\"][^\'\"]+', r'--ks-pass\s+pass:(?!android\b)\S+', r'--key-pass\s+pass:(?!android\b)\S+']
secret_hit=False
for pat in secret_patterns:
    if re.search(pat, build, re.I): secret_hit=True
ck('no_release_secret_literal', not secret_hit, 'release password is prompted at orchestration time and kept outside upload tree')

passed=sum(ok for _,ok,_ in checks)
print('ANGRY_STAGE24_49_1_RELEASE_ENGINEERING_CONTRACT 1')
print(f'checks={passed}/{len(checks)}')
for name,ok,detail in checks:
    print(f'{name}={"PASS" if ok else "FAIL"} :: {detail}')
if passed != len(checks):
    print('verdict=FAIL')
    raise SystemExit(1)
print('verdict=PASS')
