#!/usr/bin/env python3
"""Stage 24.44.1: exact GameLua::update level-limit consumer capture.

This is an evidence pass, not a synthesized bounds implementation.  Stage24.44.0
proved the setter storage shape (+0x24c/+0x250) and captured a live body lingering
outside those limits.  This pass disassembles the complete ARMv7 GameLua::update
body plus every named GameLua method that references either field, and emits
large context windows around each access so the next patch can reproduce the
real consumer rather than guessing "destroy outside body" or "ignore for motion".
"""
from __future__ import annotations
import os, re, subprocess, sys
from pathlib import Path


def run(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors='replace')
    return p.returncode, p.stdout


def parse_nm(nmt):
    out = {}
    # llvm-nm -S -C: <addr> <size> <type> <demangled name>
    rx = re.compile(r'^\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\S\s+(.+?)\s*$', re.M)
    for m in rx.finditer(nmt):
        try:
            st = int(m.group(1), 16) & ~1
            sz = int(m.group(2), 16)
        except ValueError:
            continue
        out[m.group(3)] = (st, sz)
    return out


def dis(objdump, lib, span):
    if not span:
        return ''
    st, sz = span
    rc, text = run([objdump, '-d', '--demangle',
                    f'--start-address=0x{st:x}', f'--stop-address=0x{st+sz:x}', lib])
    return text if rc == 0 else ''


def accesses(body):
    """Return instruction lines that explicitly access +0x24c/+0x250.

    Accept both llvm-objdump hex immediates and decimal spellings.  Require a
    bracketed memory operand so PC-relative literal offsets are not mistaken for
    GameLua field accesses.
    """
    result = []
    for i, line in enumerate(body.splitlines()):
        low = line.lower()
        if '[' not in low or ']' not in low:
            continue
        if any(tok in low for tok in ('#0x24c]', '#0x250]', '#588]', '#592]',
                                    '#0x24c,', '#0x250,', '#588,', '#592,')):
            result.append((i, line))
    return result


def contexts(body, hits, radius=28):
    ls = body.splitlines()
    out = []
    seen = set()
    for i, _ in hits:
        a = max(0, i-radius)
        b = min(len(ls), i+radius+1)
        key = (a, b)
        if key in seen:
            continue
        seen.add(key)
        out.append((a+1, b, '\n'.join(ls[a:b])))
    return out


def main():
    if len(sys.argv) != 6:
        print('usage: stage24441_level_limit_update_consumer_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <stage24_live_surface.cpp> <pull-stage24-live-log.ps1>', file=sys.stderr)
        return 2
    nm, objdump, lib, cppp, pullp = sys.argv[1:]
    for p in (nm, objdump, lib, cppp, pullp):
        if not os.path.exists(p):
            print('ERROR missing=' + p)
            return 3

    rc, nmt = run([nm, '-S', '-C', lib])
    if rc:
        rc, nmt = run([nm, '-D', '-S', '-C', lib])
    if rc:
        print('ERROR nm_failed')
        return 4

    syms = parse_nm(nmt)
    update_name = 'GameLua::update(float)'
    update_span = syms.get(update_name)
    update_body = dis(objdump, lib, update_span)

    # Scan exact named GameLua spans rather than grepping one giant objdump.
    candidates = []
    for name, span in sorted(syms.items(), key=lambda kv: kv[1][0]):
        if not name.startswith('GameLua::'):
            continue
        body = dis(objdump, lib, span)
        hits = accesses(body)
        if hits:
            candidates.append((name, span, body, hits))

    cpp = Path(cppp).read_text(encoding='utf-8', errors='replace')
    pull = Path(pullp).read_text(encoding='utf-8-sig', errors='replace')

    # Hard gates are intentionally about evidence capture and non-mutation only.
    # Do not fail just because update turns out not to own the fields; that result
    # itself is valid evidence and another GameLua candidate will be printed.
    checks = {
        'update_symbol_found': update_span is not None and bool(update_body),
        'level_limit_setter_remains_state_only': all(x in cpp for x in (
            'STATE_ONLY_NO_ENFORCEMENT', 'gStage24440LevelLimitMinX',
            'gStage24440LevelLimitMaxX', 'stage24440ObserveLevelBounds')),
        'shadow_probe_is_observe_only': all(x in cpp for x in (
            '[stage24.44.1-bounds]', 'shadowInBoundsMoving', 'action=OBSERVE_ONLY')),
        'collector_includes_stage2444_reports': all(x in pull for x in (
            'stage24.44.0-box2d-maxtranslation-patch.txt',
            'stage24.44.0-bounds-lifecycle-ownership-contract.txt',
            'stage24.44.0-bounds-lifecycle-runtime.txt',
            'stage24.44.1-level-limit-update-consumer-contract.txt',
            'stage24.44.1-level-limit-runtime.txt')),
    }

    print('ANGRY_STAGE24_44_1_LEVEL_LIMIT_UPDATE_CONSUMER_CONTRACT 1')
    print('policy=full ARMv7 GameLua::update + every named GameLua +0x24c/+0x250 field-access context; runtime remains observe-only')
    print('updateSpan=' + (f'0x{update_span[0]:x}+0x{update_span[1]:x}' if update_span else 'MISSING'))
    print('candidateCount=' + str(len(candidates)))
    for k, v in checks.items():
        print(f'{k}={"PASS" if v else "FAIL"}')

    print('\n===== CANDIDATE SUMMARY =====')
    for name, span, body, hits in candidates:
        print(f'{name} span=0x{span[0]:x}+0x{span[1]:x} fieldAccesses={len(hits)}')
        for _, line in hits:
            print('  ' + line.strip())

    print('\n===== FULL ARMV7 GameLua::update(float) =====')
    print(update_body.rstrip())

    print('\n===== UPDATE FIELD-ACCESS CONTEXTS =====')
    uhits = accesses(update_body)
    print('updateFieldAccessCount=' + str(len(uhits)))
    for a, b, chunk in contexts(update_body, uhits):
        print(f'\n--- update lines {a}..{b} ---')
        print(chunk)

    print('\n===== ALL GAMELUA FIELD-ACCESS CONTEXTS =====')
    for name, span, body, hits in candidates:
        print(f'\n### {name} ###')
        for a, b, chunk in contexts(body, hits):
            print(f'\n--- lines {a}..{b} ---')
            print(chunk)

    failed = [k for k, v in checks.items() if not v]
    print('\nverdict=' + ('PASS' if not failed else 'FAIL'))
    if failed:
        print('failed=' + ','.join(failed))
        return 6
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
