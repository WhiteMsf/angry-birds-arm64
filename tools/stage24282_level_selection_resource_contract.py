#!/usr/bin/env python3
"""Stage 24.28.2 Level Selection resource/registry contract audit.

Read-only against the untouched ARMv7 libangrybirds.so and original 864x480
SPRT metadata.  The immediate question is intentionally narrow:

  Lua Level Selection requests LS_THEME_1_LEFT through BUTTONS_SHEET_1 while
  the retained asset corpus owns that sprite in LEVELSELECTION_SHEET_1.dat.

Do not guess a fallback.  Recover which native registry/sheet path the original
Resources::drawSprite(two-string overload) actually uses and inventory the
exact owner(s) of the Level Selection sprites.
"""
from __future__ import annotations
import os, re, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HEADER = "ANGRY_STAGE24_28_2_LEVEL_SELECTION_RESOURCE_CONTRACT 1"

@dataclass
class Sym:
    addr: int
    size: int
    typ: str
    name: str

def run(args: list[str]):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors="replace")
    return p.returncode, p.stdout.splitlines()

def parse_nm(lines: Iterable[str]):
    out=[]
    rx=re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    for ln in lines:
        m=rx.match(ln)
        if m:
            out.append(Sym(int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(4)))
    return out

def find_exact(syms: list[Sym], names: tuple[str,...]):
    for n in names:
        for s in syms:
            if s.name == n and s.typ in 'TtWw':
                return s
    return None

def disasm(objdump: str, lib: str, s: Sym):
    start=s.addr & ~1
    size=s.size or 0x100
    rc, lines=run([objdump,'-d','--demangle',f'--start-address=0x{start:x}',
                  f'--stop-address=0x{start+size:x}',lib])
    return rc, lines

def calls(lines: list[str]):
    return [ln.strip() for ln in lines if re.search(r'\bblx?\b',ln)]

def printable_strings(data: bytes, minlen: int=3):
    for m in re.finditer(rb'[\x20-\x7e]{%d,}' % minlen, data):
        yield m.start(), m.group().decode('ascii','replace')

def main() -> int:
    if len(sys.argv) != 5:
        print('usage: stage24282_level_selection_resource_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <imageRoot>', file=sys.stderr)
        return 2
    nm,objdump,lib,image_root=sys.argv[1:]
    print(HEADER)
    print('policy=READ_ONLY; NO cross-sheet fallback is assumed from asset filenames')
    print('question=two-string Resources::drawSprite registry/sheet semantics + LS_THEME owner provenance')
    print(f'lib={lib}')
    print(f'imageRoot={image_root}')
    for p in (nm,objdump,lib,image_root):
        if not os.path.exists(p):
            print(f'ERROR missing={p}')
            return 3

    rc,nml=run([nm,'-S','-C',lib])
    if rc != 0 or not nml:
        rc,nml=run([nm,'-D','-S','-C',lib])
    syms=parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')

    targets={
        'draw2': (
            'game::Resources::drawSprite(lang::String const&, lang::String const&, float, float, game::Anchor) const',
        ),
        'draw2scaled': (
            'game::Resources::drawSprite(lang::String const&, lang::String const&, float, float, float, float, game::Anchor) const',
        ),
        'findSprite': ('game::Resources::findSprite(lang::String const&) const',),
        'findSheet': ('game::Resources::findSheet(lang::String const&) const',),
        'getSheet': ('game::Resources::getSpriteSheet(lang::String const&) const',),
        'sheetDraw': ('game::SpriteSheet::drawSprite(gr::Context*, lang::String const&, float, float, game::Anchor) const',),
        'spriteDraw': ('game::Sprite::draw(gr::Context*, float, float, game::Anchor) const',),
        'width2': ('game::Resources::getSpriteWidth(lang::String const&, lang::String const&) const',),
        'height2': ('game::Resources::getSpriteHeight(lang::String const&, lang::String const&) const',),
        'pivotX2': ('game::Resources::getSpritePivotX(lang::String const&, lang::String const&) const',),
        'pivotY2': ('game::Resources::getSpritePivotY(lang::String const&, lang::String const&) const',),
        'addRegistry': ('game::Resources::addSpritesToRegistry(game::SpriteSheet*)',),
        'removeRegistry': ('game::Resources::removeSpritesFromRegistry(game::SpriteSheet*)',),
    }
    resolved={k:find_exact(syms,v) for k,v in targets.items()}
    print('\n--- REQUIRED_SYMBOLS ---')
    for k,s in resolved.items():
        print(f'{k}=' + (f'0x{s.addr:x}+0x{s.size:x} {s.name}' if s else 'NOT_FOUND'))

    print('\n--- NATIVE_BODIES ---')
    bodies={}
    for k in ('draw2','draw2scaled','findSprite','findSheet','getSheet','width2','height2','pivotX2','pivotY2','addRegistry'):
        s=resolved.get(k)
        if not s: continue
        drc,body=disasm(objdump,lib,s)
        bodies[k]=body
        print(f'\nFUNCTION {k} symbol={s.name!r} start=0x{s.addr & ~1:x} size=0x{s.size:x} objdumpExit={drc}')
        for ln in body: print(ln)
        print(f'CALLS {k} count={len(calls(body))}')
        for ln in calls(body): print('  '+ln)

    draw_lines='\n'.join(bodies.get('draw2',[]))
    has_global_find='Resources::findSprite(' in draw_lines
    has_find_sheet='Resources::findSheet(' in draw_lines
    has_get_sheet='Resources::getSpriteSheet(' in draw_lines
    has_sheet_draw='SpriteSheet::drawSprite(' in draw_lines
    has_sprite_draw='Sprite::draw(' in draw_lines

    # If llvm-objdump demangles a call via a thunk/PLT and the direct body does
    # not spell the callee, use exact symbol addresses as a second detector.
    call_text='\n'.join(calls(bodies.get('draw2',[]))).lower()
    def addr_hit(key: str) -> bool:
        s=resolved.get(key)
        if not s: return False
        a=s.addr & ~1
        return (f'0x{a:x}' in call_text) or re.search(rf'\b{a:x}\b', call_text) is not None
    has_global_find = has_global_find or addr_hit('findSprite')
    has_find_sheet = has_find_sheet or addr_hit('findSheet')
    has_get_sheet = has_get_sheet or addr_hit('getSheet')
    has_sheet_draw = has_sheet_draw or addr_hit('sheetDraw')
    has_sprite_draw = has_sprite_draw or addr_hit('spriteDraw')

    print('\n--- TWO_STRING_DRAW_CLASSIFICATION ---')
    print(f'callsFindSprite={str(has_global_find).lower()}')
    print(f'callsFindSheet={str(has_find_sheet).lower()}')
    print(f'callsGetSpriteSheet={str(has_get_sheet).lower()}')
    print(f'callsSpriteSheetDrawSprite={str(has_sheet_draw).lower()}')
    print(f'callsSpriteDraw={str(has_sprite_draw).lower()}')
    if has_global_find and not (has_find_sheet or has_get_sheet):
        native_mode='GLOBAL_SPRITE_REGISTRY'
    elif (has_find_sheet or has_get_sheet or has_sheet_draw) and not has_global_find:
        native_mode='SHEET_SCOPED'
    elif has_global_find and (has_find_sheet or has_get_sheet or has_sheet_draw):
        native_mode='HYBRID_OR_FALLBACK'
    else:
        native_mode='UNRESOLVED'
    print(f'nativeLookupMode={native_mode}')

    image=Path(image_root)
    needles=('LS_THEME_1_LEFT','LS_THEME_1_RIGHT','LS_MAIN_LEFT','LS_MAIN_RIGHT')
    owners={n:[] for n in needles}
    print('\n--- ORIGINAL_DAT_OWNERS ---')
    dats=sorted(image.glob('*.dat')) if image.is_dir() else []
    for p in dats:
        try: raw=p.read_bytes()
        except OSError: continue
        for n in needles:
            if n.encode('ascii') in raw:
                owners[n].append(p.name)
    for n in needles:
        print(f'sprite={n!r} ownerCount={len(owners[n])} owners={";".join(owners[n]) or "-"}')
    buttons=Path(image)/'BUTTONS_SHEET_1.dat'
    levelsel=Path(image)/'LEVELSELECTION_SHEET_1.dat'
    print(f'buttonsExists={buttons.is_file()} levelSelectionExists={levelsel.is_file()}')
    if buttons.is_file():
        b=buttons.read_bytes()
        print('buttonsContainsLS_THEME_1_LEFT=' + ('yes' if b'LS_THEME_1_LEFT' in b else 'no'))
        print('buttonsContainsLS_THEME_1_RIGHT=' + ('yes' if b'LS_THEME_1_RIGHT' in b else 'no'))
    if levelsel.is_file():
        b=levelsel.read_bytes()
        print('levelSelectionContainsLS_THEME_1_LEFT=' + ('yes' if b'LS_THEME_1_LEFT' in b else 'no'))
        print('levelSelectionContainsLS_THEME_1_RIGHT=' + ('yes' if b'LS_THEME_1_RIGHT' in b else 'no'))
        # Include the exact neighboring printable runs so ownership is human-auditable.
        ss=list(printable_strings(b))
        for idx,(off,s) in enumerate(ss):
            if s in needles:
                print(f'  context sprite={s!r} offset=0x{off:x}')
                for oo,tt in ss[max(0,idx-3):min(len(ss),idx+4)]:
                    print(f'    0x{oo:x} {tt}')

    unique_level_owner=(owners['LS_THEME_1_LEFT']==['LEVELSELECTION_SHEET_1.dat'] and
                        owners['LS_THEME_1_RIGHT']==['LEVELSELECTION_SHEET_1.dat'])
    print('\n--- VERDICT ---')
    print(f'uniqueThemeOwnerLevelSelection={str(unique_level_owner).lower()}')
    print(f'nativeLookupMode={native_mode}')
    if not resolved.get('draw2'):
        print('verdict=FAIL_DRAWSPRITE_SYMBOL_MISSING')
        return 4
    if not unique_level_owner:
        print('verdict=FAIL_THEME_SPRITE_OWNERSHIP_AMBIGUOUS')
        return 5
    if native_mode=='UNRESOLVED':
        print('verdict=PASS_NATIVE_LOOKUP_UNRESOLVED_NO_FALLBACK_AUTHORIZED')
        return 0
    if native_mode=='GLOBAL_SPRITE_REGISTRY':
        print('verdict=PASS_GLOBAL_REGISTRY_AUTHORIZES_CROSS_SHEET_RESOLUTION')
    elif native_mode=='SHEET_SCOPED':
        print('verdict=PASS_SHEET_SCOPED_MISMATCH_IS_ORIGINAL_MISSING_SPRITE_BEHAVIOR')
    else:
        print('verdict=PASS_HYBRID_REQUIRES_RUNTIME_PROVENANCE_BEFORE_FALLBACK')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
