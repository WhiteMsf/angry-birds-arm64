#!/usr/bin/env python3
import sys
from pathlib import Path

if len(sys.argv) != 4:
    print('usage: stage24290_startup_boot_contract.py <scripts-root> <image-root> <stage24_live_surface.cpp>')
    sys.exit(2)

scripts = Path(sys.argv[1])
image_root = Path(sys.argv[2])
source = Path(sys.argv[3])
if not scripts.exists() or not image_root.exists() or not source.is_file():
    print(f'FAIL inputs scripts={scripts} imageRoot={image_root} source={source}')
    sys.exit(3)

print('ANGRY_STAGE24_29_0_STARTUP_BOOT_CONTRACT 1')
print(f'scriptsRoot={scripts}')
print(f'imageRoot={image_root}')

script_needles = [
    b'updateSplashes', b'SPLASH_CLICKGAMER', b'SPLASH_ROVIO',
    b'SPLASH_ANGRY_BIRDS', b'SPLASH_LOADING', b'currentMainMenuTheme',
    b'updateMenu', b'setBGColor'
]
script_hits = {n.decode(): [] for n in script_needles}
script_files = [p for p in scripts.rglob('*') if p.is_file()]
for p in script_files:
    try: data = p.read_bytes()
    except Exception: continue
    for n in script_needles:
        if n in data:
            script_hits[n.decode()].append(str(p.relative_to(scripts)))
for n in script_needles:
    k=n.decode(); vals=script_hits[k]
    print(f"script needle='{k}' files={len(vals)}")
    for v in vals[:8]: print(f'  {v}')

sprite_names = ['SPLASH_CLICKGAMER','SPLASH_ROVIO','SPLASH_ANGRY_BIRDS','SPLASH_LOADING']
owners = {n: [] for n in sprite_names}
dat_files = [p for p in image_root.rglob('*.dat') if p.is_file()]
for p in dat_files:
    try: data = p.read_bytes()
    except Exception: continue
    for name in sprite_names:
        if name.encode() in data:
            owners[name].append(str(p.relative_to(image_root)))
for name in sprite_names:
    print(f"asset sprite='{name}' owners={len(owners[name])} values={owners[name]}")

text = source.read_text(encoding='utf-8', errors='replace')
checks = {
    'boot_state': 'struct Stage24290BootState' in text,
    'boot_renderer': 'stage24290RenderBootSplash' in text,
    'boot_start_marker': '[stage24.29.0-boot] START' in text,
    'display_marker': '[stage24.29.0-boot] DISPLAY' in text,
    'edition_skip': 'DO_NOT_INVENT_ASSET' in text,
    'hidden_scaffold': 'Level1_materialized_hidden_no_physics_no_update' in text,
    'main_menu_handoff': 'stage24.29.0-startup-main-menu-handoff' in text and 'newMenuPage = mainMenu' in text,
    'original_durations': 'return phase == 2 ? 1.0f : 2.0f' in text,
    'original_colors': 'phase == 2 ? 0.0f : 1.0f' in text,
    'touch_skip': 'source=LBUTTON' in text,
}
for k,v in checks.items():
    print(f'source {k}={"PASS" if v else "FAIL"}')

required_script = ['updateSplashes','SPLASH_CLICKGAMER','SPLASH_ROVIO','SPLASH_ANGRY_BIRDS','currentMainMenuTheme','updateMenu','setBGColor']
missing_script = [k for k in required_script if not script_hits[k]]
core_bad = []
if len(owners['SPLASH_ROVIO']) != 1:
    core_bad.append(f"SPLASH_ROVIO owners={owners['SPLASH_ROVIO']}")
if len(owners['SPLASH_ANGRY_BIRDS']) != 1:
    core_bad.append(f"SPLASH_ANGRY_BIRDS owners={owners['SPLASH_ANGRY_BIRDS']}")
if owners['SPLASH_ROVIO'] and not any('SPLASHES_SHEET_2.dat' in x for x in owners['SPLASH_ROVIO']):
    core_bad.append('SPLASH_ROVIO owner is not SPLASHES_SHEET_2.dat')
if owners['SPLASH_ANGRY_BIRDS'] and not any('SPLASHES_SHEET_1.dat' in x for x in owners['SPLASH_ANGRY_BIRDS']):
    core_bad.append('SPLASH_ANGRY_BIRDS owner is not SPLASHES_SHEET_1.dat')
failed_source = [k for k,v in checks.items() if not v]

print("policy clickgamer=" + ("RUNTIME_OPTIONAL_CONCRETE_OWNER" if not owners['SPLASH_CLICKGAMER'] else "RUNTIME_PRESENT_CONCRETE_OWNER"))
print("policy loading=" + ("ANDROID_ANGRY_BIRDS_OVERLAY_REQUIRED_BUT_OWNER_UNRESOLVED_DEFERRED" if not owners['SPLASH_LOADING'] else "ANDROID_ANGRY_BIRDS_OVERLAY_OWNER_PRESENT_NEEDS_RUNTIME_CLOSURE"))
if missing_script or core_bad or failed_source:
    print(f'VERDICT=FAIL missingScript={missing_script} coreAssetFailures={core_bad} failedSource={failed_source}')
    sys.exit(1)
print('VERDICT=PASS_CORE_SPLASH_BOOT Rovio=2s:white AngryBirds=1s:black Clickgamer=only-if-concrete-owner startup->mainMenu scaffold-hidden')
