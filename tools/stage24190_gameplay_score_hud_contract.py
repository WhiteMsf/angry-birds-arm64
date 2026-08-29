#!/usr/bin/env python3
"""Stage 24.19.0 gameplay score HUD static asset contract audit.

Read-only audit against the untouched Angry Birds 1.4.2 data tree.  It does
not infer coordinates, scale, font, anchor or draw order.  Those are recovered
from the live untouched Lua closure tree by the companion runtime audit.
"""
from __future__ import annotations
import os, re, sys
from pathlib import Path


def printable_strings(data: bytes, minlen: int = 3):
    rx = re.compile(rb'[\x20-\x7e]{%d,}' % minlen)
    for m in rx.finditer(data):
        yield m.start(), m.group().decode('ascii', 'replace')


def main() -> int:
    if len(sys.argv) != 2:
        print('usage: stage24190_gameplay_score_hud_contract.py <dataRoot>', file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    print('ANGRY_STAGE24_19_0_GAMEPLAY_SCORE_HUD_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; untouched 1.4.2 assets; no guessed HUD coordinates/font/anchor')
    print(f'dataRoot={root}')
    if not root.exists():
        print(f'ERROR missing={root}')
        return 3

    keyrx = re.compile(r'(?i)(score|points?|hud|font_score|big_numbers)')
    print('\n--- PROFILE ROOTS ---')
    for rel in ('images/864x480', 'fonts/864x480'):
        p = root / rel
        files = [x for x in p.rglob('*') if x.is_file()] if p.exists() else []
        print(f'PROFILE\t{rel}\texists={p.exists()}\tfiles={len(files)}')

    print('\n--- FILENAME HITS ---')
    name_hits = []
    for rel in ('images/864x480', 'fonts/864x480'):
        p = root / rel
        if not p.exists():
            continue
        for f in p.rglob('*'):
            if f.is_file() and keyrx.search(f.name):
                name_hits.append(f)
                print(f'FILE\t{f.relative_to(root)}\tbytes={f.stat().st_size}')
    print(f'filenameHits={len(name_hits)}')

    print('\n--- METADATA STRING HITS ---')
    metadata = []
    for rel in ('images/864x480', 'fonts/864x480'):
        p = root / rel
        if not p.exists():
            continue
        metadata.extend(f for f in p.rglob('*') if f.is_file() and f.suffix.lower() in ('.dat', '.txt', '.lua'))
    mh = 0
    for f in metadata:
        try:
            raw = f.read_bytes()
        except OSError:
            continue
        strings = list(printable_strings(raw))
        hit_idx = [i for i, (_, s) in enumerate(strings) if keyrx.search(s)]
        if not hit_idx:
            continue
        mh += 1
        print(f'\nMETA\t{f.relative_to(root)}\tbytes={len(raw)}\thits={len(hit_idx)}')
        shown = set()
        for i in hit_idx:
            for j in range(max(0, i - 4), min(len(strings), i + 5)):
                off, s = strings[j]
                if (off, s) in shown:
                    continue
                shown.add((off, s))
                print(f'  STR\t0x{off:06x}\t{s}')
    print(f'metadataFilesWithHits={mh}')

    print('\n--- ORIGINAL SCRIPT RAW STRING HITS ---')
    for rel in ('scripts/gamelogic.lua', 'scripts/loadlist.lua'):
        f = root / rel
        if not f.exists():
            print(f'FILE\t{rel}\tNOT_FOUND')
            continue
        raw = f.read_bytes()
        hits = [(o, s) for o, s in printable_strings(raw) if keyrx.search(s)]
        print(f'FILE\t{rel}\tbytes={len(raw)}\thits={len(hits)}')
        for o, s in hits[:1000]:
            print(f'  0x{o:08x}\t{s}')

    print('\n--- AUDIT_CONCLUSION_GUARD ---')
    print('implementationDecision=DEFERRED_UNTIL_LUA_OWNER_REPORT_REVIEW')
    print('requiredEvidence=score owner closure + draw call + font + anchor + exact screen-relative coordinates/visibility gate')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
