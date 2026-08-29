#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit('usage: stage24304_bootstrap_meta_manifest_contract.py <stage24_live_surface.cpp>')
s=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
checks={
 'manifest_name': 'bootstrap-menu-meta.txt' in s,
 'extract_marker': '[stage24.30.4-bootstrap-meta] EXTRACT' in s,
 'load_marker': '[stage24.30.4-bootstrap-meta] LOAD' in s,
 'extract_uses_manifest': 'stage24/sprite-meta/" + name' in s,
 'load_uses_manifest': 'runtimeRoot + "/sprite-meta/" + name' in s,
 'old_fixed_golden2_absent': 'stage24/sprite-meta/GOLDEN_EGGS_SHEET_2.dat' not in s,
}
for k,v in checks.items(): print(f'{k}={str(v).lower()}')
if not all(checks.values()): raise SystemExit('FAIL_BOOTSTRAP_META_MANIFEST_CONTRACT')
print('verdict=PASS_SINGLE_SOURCE_BOOTSTRAP_META_OWNERSHIP')
