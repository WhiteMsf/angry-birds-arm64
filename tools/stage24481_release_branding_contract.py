#!/usr/bin/env python3
from pathlib import Path
import re, sys
if len(sys.argv)!=2:
    print('usage: stage24481_release_branding_contract.py <root>',file=sys.stderr); raise SystemExit(2)
root=Path(sys.argv[1])
manifest=(root/'stage24-android/AndroidManifest.xml').read_text(encoding='utf-8-sig',errors='replace')
build=(root/'build-stage24-live-surface-touch-arm64.ps1').read_text(encoding='utf-8-sig',errors='replace')
readme=(root/'README.md').read_text(encoding='utf-8-sig',errors='replace')
checks=[]
def ck(n,c,d): checks.append((n,bool(c),d))
ck('label_exact_angry_birds','android:label="Angry Birds"' in manifest,'application label is exactly Angry Birds')
ck('manifest_icon_resource','android:icon="@drawable/app_icon"' in manifest,'manifest points to @drawable/app_icon')
version_name_match=re.search(r'android:versionName="(\d+)\.(\d+)\.(\d+)"',manifest)
version_code_match=re.search(r'android:versionCode="(\d+)"',manifest)
current_release_heading=re.match(r'# Angry Birds ARM64 — v(\d+\.\d+\.\d+)\b',readme)
version_name='.'.join(version_name_match.groups()) if version_name_match else None
version_code=int(version_code_match.group(1)) if version_code_match else None
expected_code=(int(version_name_match.group(1))*1000000 + int(version_name_match.group(2))*1000 + int(version_name_match.group(3))) if version_name_match else None
ck('version_semver',version_name_match is not None and version_code_match is not None,'development audit version metadata is parseable semantic version')
ck('version_code_semver',version_code == expected_code,f'development versionCode={version_code!r} matches semver-derived code={expected_code!r}')
ck('version_release_heading',current_release_heading is not None and current_release_heading.group(1) == version_name,f'development versionName={version_name!r} matches current README release={current_release_heading.group(1) if current_release_heading else None!r}')
ck('local_original_icon_discovery','stage24481_find_original_launcher_icon.py' in build,'build discovers icon from user-local original APK/extracted res')
ck('icon_staged_to_res',"$resRoot = Join-Path $apkWork 'res'" in build and "$resDrawable = Join-Path $resRoot 'drawable'" in build and "'app_icon.png'" in build,'original icon staged to generated res/drawable/app_icon.png')
ck('aapt_packages_res',re.search(r'aaptAscii package[^\r\n]*\s-S\s+\$resRootAscii',build) is not None,'aapt packages generated res tree')
ck('postpackage_badging','stage24.48.1-apk-branding-audit.txt' in build and 'dump badging' in build,'post-package label/icon audit is wired')
# Do not distribute Rovio art in the source archive.
embedded=list(root.glob('stage24-android/res/**/*app_icon*')) if (root/'stage24-android/res').exists() else []
ck('no_proprietary_icon_in_source',not embedded,'source tree contains no bundled Rovio launcher icon')
print('ANGRY_STAGE24_48_1_RELEASE_BRANDING_CONTRACT 1')
for n,c,d in checks: print(f'{n}={"PASS" if c else "FAIL"} :: {d}')
print(f'checks={sum(c for _,c,_ in checks)}/{len(checks)}')
if not all(c for _,c,_ in checks):
    print('verdict=FAIL')
    raise SystemExit(1)
print('verdict=PASS')
