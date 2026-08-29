#!/usr/bin/env python3
import sys
from pathlib import Path

if len(sys.argv) != 3:
    print('usage: stage24285_menu_bg_openurl_contract.py <scripts-root> <stage24_live_surface.cpp>')
    sys.exit(2)

scripts = Path(sys.argv[1])
source = Path(sys.argv[2])
if not scripts.exists() or not source.is_file():
    print(f'FAIL inputs scripts={scripts} source={source}')
    sys.exit(3)

needles = [b'setBGColor', b'bgColor', b'drawLevelSelectionBackground', b'LS_BACKGROUND', b'openURL', b'res']
hits = {n.decode(): [] for n in needles}
files = [p for p in scripts.rglob('*') if p.is_file()]
for p in files:
    try:
        data = p.read_bytes()
    except Exception:
        continue
    for n in needles:
        if n in data:
            hits[n.decode()].append(str(p.relative_to(scripts)))

print('ANGRY_STAGE24_28_5_MENU_BG_OPENURL_CONTRACT 1')
print(f'scriptsRoot={scripts}')
print(f'filesScanned={len(files)}')
for n in needles:
    k=n.decode(); vals=hits[k]
    print(f"corpus needle='{k}' files={len(vals)}")
    for v in vals[:12]: print(f'  {v}')

text = source.read_text(encoding='utf-8', errors='replace')
checks = {
    'setBGColor_handler': 'l_stage24285_setBGColor' in text,
    'page_bgcolor_state': 'gStage24285BgColor' in text,
    'fullframe_uses_page_bgcolor': 'source=ORIGINAL_setBGColor' in text,
    'res_openurl_binding': 'lua_setfield(L, -2, "openURL")' in text,
    'openurl_no_launch': 'action=AUDIT_NO_LAUNCH' in text,
    'lua_contract_dump': 'stage24285DumpMenuBackgroundAndOpenUrlContract' in text,
}
for k,v in checks.items(): print(f'source {k}={"PASS" if v else "FAIL"}')

required_corpus = ['setBGColor','bgColor','drawLevelSelectionBackground','LS_BACKGROUND','openURL','res']
missing=[k for k in required_corpus if not hits[k]]
failed=[k for k,v in checks.items() if not v]
if missing or failed:
    print(f'VERDICT=FAIL missingCorpus={missing} failedSource={failed}')
    sys.exit(1)
print('VERDICT=PASS page-owned BG color + _G.res.openURL contract staged without external launch')
