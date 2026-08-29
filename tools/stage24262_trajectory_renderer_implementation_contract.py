#!/usr/bin/env python3
"""Stage 24.26.2 preflight for the recovered original trajectory renderer.

Read-only.  Verifies the exact PIC literal cluster used by untouched ARMv7
GameLua::drawGame and the corresponding retained sprite metadata before the
ARM64 implementation is compiled.
"""
from __future__ import annotations
import re, sys
from pathlib import Path

HEADER='ANGRY_STAGE24_26_2_TRAJECTORY_RENDERER_IMPLEMENTATION_CONTRACT 1'

def cstr(data: bytes, off: int, cap: int=128) -> str:
    if off < 0 or off >= len(data): return '<OOB>'
    end=data.find(b'\0', off, min(len(data), off+cap))
    if end < 0: return '<NO_NUL>'
    return data[off:end].decode('ascii','replace')

def strings(data: bytes, min_len=4):
    for m in re.finditer(rb'[\x20-\x7e]{%d,}'%min_len, data):
        yield m.start(), m.group().decode('ascii','replace')

def main()->int:
    if len(sys.argv)!=3:
        print('usage: stage24262_trajectory_renderer_implementation_contract.py <libangrybirds.so> <INGAME_BIRDS_1.dat>', file=sys.stderr)
        return 2
    lib=Path(sys.argv[1]); dat=Path(sys.argv[2])
    print(HEADER)
    print('policy=FAIL_CLOSED; no guessed trail/puff resource names accepted')
    if not lib.is_file() or not dat.is_file():
        print(f'ERROR missing lib={lib.is_file()} dat={dat.is_file()}')
        return 3
    raw=lib.read_bytes(); meta=dat.read_bytes()
    required=['INGAME_BIRDS_1','TRAIL_WHITE_1','TRAIL_WHITE_2','TRAIL_WHITE_3']
    offs={s:raw.find(s.encode('ascii')) for s in required}
    for s in required:
        print(f'ELF_STRING name={s} fileOff=0x{offs[s]:x}' if offs[s]>=0 else f'ELF_STRING name={s} fileOff=NOT_FOUND')
        if offs[s]<0: return 4
    # Stage24.26.1 recovered the exact drawGame PIC cluster: WHITE strings are
    # 0x10 apart, and the fifth 12-byte lang::String begins 0x10 after WHITE_3.
    if not (offs['TRAIL_WHITE_2']-offs['TRAIL_WHITE_1']==0x10 and offs['TRAIL_WHITE_3']-offs['TRAIL_WHITE_2']==0x10):
        print('ERROR white trail PIC string spacing differs from recovered ARMv7 drawGame contract')
        return 5
    puff_off=offs['TRAIL_WHITE_3']+0x10
    puff=cstr(raw,puff_off)
    print(f'PIC_CLUSTER group={cstr(raw,offs["TRAIL_WHITE_1"]-0x10)} white1={cstr(raw,offs["TRAIL_WHITE_1"])} white2={cstr(raw,offs["TRAIL_WHITE_2"])} white3={cstr(raw,offs["TRAIL_WHITE_3"])} puff={puff} puffFileOff=0x{puff_off:x}')
    if cstr(raw,offs['TRAIL_WHITE_1']-0x10)!='INGAME_BIRDS_1':
        print('ERROR recovered resource-group literal is not INGAME_BIRDS_1'); return 6
    if puff!='BIRD_SPECIAL' or len(puff)!=12:
        print(f"ERROR recovered 12-byte puff literal expected BIRD_SPECIAL, got '{puff}'"); return 7
    metas=[s for _,s in strings(meta,4)]
    for s in ['TRAIL_WHITE_1','TRAIL_WHITE_2','TRAIL_WHITE_3','BIRD_SPECIAL']:
        count=sum(1 for x in metas if x==s)
        print(f'METADATA sprite={s} exactStringCount={count}')
        if count<1: return 8
    print('DRAW_CONTRACT slots=6 order=slot0..slot5 normalThenPuffPerSlot')
    print('NORMAL_PATTERN pointIndexModulo3=TRAIL_WHITE_1,TRAIL_WHITE_2,TRAIL_WHITE_3')
    print('PUFF_PATTERN sprite=BIRD_SPECIAL')
    print('DRAW_PLACEMENT afterNativePass1BeforeNativePass2')
    print('ANCHOR rawARMv7Words=4,3 implementation=retainedSPRTPivotAtStoredWorldPoint evidence=sameAnchorPairAsNativeGameplaySpriteDraws')
    print('TRANSFORM storedXY=worldPixels camera=(xy-topLeft)*worldScale spriteScale=worldScale')
    print('PASS exact ARMv7 PIC resource cluster + original metadata verified')
    return 0
if __name__=='__main__': raise SystemExit(main())
