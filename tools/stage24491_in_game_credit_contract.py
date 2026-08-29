#!/usr/bin/env python3
from __future__ import annotations
import pathlib, re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: stage24491_in_game_credit_contract.py <root>')
root = pathlib.Path(sys.argv[1]).resolve()
source = (root / 'stage24_live_surface.cpp').read_text(encoding='utf-8', errors='replace')
audit_manifest = (root / 'stage24-android/AndroidManifest.xml').read_text(encoding='utf-8', errors='replace')
release_manifest = (root / 'stage24-android/AndroidManifest.release.xml').read_text(encoding='utf-8', errors='replace')

credit = 'ARM64 reconstruction by WhiteMsf'
checks = []
def ck(name, ok, detail): checks.append((name, bool(ok), detail))

m = re.search(r'static std::string stage2412_resolve_text\([^\)]*\)\s*\{([\s\S]*?)\n\}', source)
body = m.group(1) if m else ''
ck('resolver_found', bool(m), 'stage2412_resolve_text located')
ck('original_localization_prefix', 'std::string value = gStage248Localization.get(id);' in body,
   'original localized value remains the source prefix')
ck('credit_exact', f'value += "{credit}";' in body, f'exact line={credit!r}')
ck('credit_scoped_to_text_credits', 'if (id == "TEXT_CREDITS")' in body,
   'only TEXT_CREDITS receives project attribution')
ck('credit_separated_by_blank_line', 'value += "\\n\\n";' in body,
   'blank line separates original credits from reconstruction attribution')
ck('no_about_replacement', 'TEXT_ABOUT_ANDROID' not in body,
   'About/legal localization is not rewritten by the attribution hook')
ck('audit_version', 'android:versionName="0.26.164"' in audit_manifest and 'android:versionCode="26164"' in audit_manifest,
   'Audit envelope metadata advanced')
ck('release_version_unchanged', 'android:versionName="1.0.0"' in release_manifest and 'android:versionCode="1000000"' in release_manifest,
   'public Release metadata remains 1.0.0')

passed=sum(ok for _,ok,_ in checks)
print('ANGRY_STAGE24_49_1_IN_GAME_CREDIT_CONTRACT 1')
print(f'checks={passed}/{len(checks)}')
for name,ok,detail in checks:
    print(f'{name}={"PASS" if ok else "FAIL"} :: {detail}')
if passed != len(checks):
    print('verdict=FAIL')
    raise SystemExit(1)
print('verdict=PASS')
