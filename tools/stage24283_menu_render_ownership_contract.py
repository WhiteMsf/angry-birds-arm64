#!/usr/bin/env python3
from __future__ import annotations
import pathlib, re, subprocess, sys

TARGETS = [
    'NEW_HIGHSCORE_PT','SCORE_PT','GOLDEN_EGG_STAR_EFFECT','SETTINGS_BG',
    'MENU_SLIDER_BG_BOTTOM_MIDDLE','MENU_SLIDER_BG_BOTTOM_LEFT','MENU_SLIDER_BG_BOTTOM_RIGHT',
    'LS_THEME_1_LEFT','LS_THEME_1_RIGHT',
]
SYMBOL_NEEDLES = ['GameLua::drawBackground()', 'GameLua::drawForegroundNative()', 'GameLua::setBGColor(float, float, float)']

def run(args):
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, errors='replace').stdout

def parse_symbols(nm_text):
    out=[]
    # llvm-nm -C -S: addr size type name
    for line in nm_text.splitlines():
        m=re.match(r'^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\S\s+(.+)$', line.strip())
        if m:
            out.append((int(m.group(1),16), int(m.group(2),16), m.group(3)))
    return out

def main():
    if len(sys.argv)!=6:
        print('usage: stage24283_menu_render_ownership_contract.py <llvm-nm> <llvm-objdump> <lib.so> <image-root> <scripts-root>', file=sys.stderr)
        return 2
    nm,objdump,lib,image_root,scripts_root=sys.argv[1:]
    image_root=pathlib.Path(image_root); scripts_root=pathlib.Path(scripts_root)
    nm_text=run([nm,'-C','-S',lib])
    syms=parse_symbols(nm_text)
    print('ANGRY_STAGE24_28_3_MENU_RENDER_OWNERSHIP_CONTRACT 1')
    print('policy=static-audit; no Rovio payload is copied into the project package')
    print('observedBug=updateMenu frame was previously preceded by native gameplay world/HUD while untouched drawMenu native background/foreground calls were stubbed')

    print('\n[ARMV7_NATIVE_OWNERSHIP]')
    found=0
    for needle in SYMBOL_NEEDLES:
        matches=[x for x in syms if x[2]==needle]
        if not matches:
            print(f"symbol={needle!r} status=NOT_FOUND")
            continue
        for addr,size,name in matches:
            found+=1
            stop=addr+size
            dis=run([objdump,'-d','-C',f'--start-address=0x{addr:x}',f'--stop-address=0x{stop:x}',lib])
            calls=[]
            for line in dis.splitlines():
                if re.search(r'\bblx?\b', line):
                    calls.append(line.strip())
            print(f"symbol={name!r} start=0x{addr:x} size=0x{size:x} calls={len(calls)}")
            for c in calls[:80]: print('  '+c)
            if name=='GameLua::drawBackground()':
                print('  EXPECT=setBGColor before Resources::drawSprite loop')
            if name=='GameLua::drawForegroundNative()':
                print('  EXPECT=ground-color draw + repeated fg layer sprite loop')
    print(f'armv7TargetSymbolsFound={found}/{len(SYMBOL_NEEDLES)}')

    print('\n[REMAINING_RUNTIME_MISS_CORPUS]')
    dats=list(image_root.rglob('*.dat'))
    luas=list(scripts_root.rglob('*.lua')) if scripts_root.exists() else []
    for target in TARGETS:
        hits=[]
        tb=target.encode('ascii')
        for p in dats+luas:
            try: b=p.read_bytes()
            except OSError: continue
            if tb in b:
                hits.append(str(p.relative_to(image_root if p.is_relative_to(image_root) else scripts_root)))
        print(f"target={target!r} hits={len(hits)} files={';'.join(hits[:24])}")

    comp=[p.name for p in dats if 'composprite' in p.name.lower()]
    print('\n[COMPOSPRITE_FILES]')
    print(f'count={len(comp)} names={";".join(sorted(comp))}')

    # This audit is intentionally tolerant of missing UI names: the point is to
    # classify them, not synthesize an owner. The ownership symbols, however,
    # are required because Stage24.28.3 reuses their already-recovered semantics.
    if found < 2:
        print('VERDICT=FAIL required drawBackground/drawForeground ARMv7 symbols not found')
        return 3
    print('VERDICT=PASS menu frame ownership boundary and remaining miss provenance inventoried')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
