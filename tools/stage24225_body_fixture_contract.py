#!/usr/bin/env python3
"""Stage 24.22.5: untouched ARMv7 circle/body/fixture construction audit.

Diagnostic only. Stage 24.22.4 resolved the Rovio restitution velocity threshold
as the stock Box2D value 1.0f, so the remaining bird/ground settle discrepancy
must be sought elsewhere. This audit follows the original native construction
path around b2World::CreateBody / b2Body::CreateFixture and surfaces candidate
GameLua/createCircle/createBox wrappers, body-def defaults, and fixture material
handling without changing the ARM64 port.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Sym:
    addr: int
    size: int
    typ: str
    name: str


def run(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, errors='replace')
    return p.returncode, p.stdout.splitlines()


def parse_nm(lines):
    rx = re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    out = []
    for line in lines:
        m = rx.match(line)
        if m:
            out.append(Sym(int(m.group(1), 16), int(m.group(2), 16), m.group(3), m.group(4)))
    return out


def find_source(root: Path, basename: str):
    hits = list(root.rglob(basename))
    return hits[0] if hits else None


def print_source_focus(path: Path | None, patterns: list[str], radius: int = 7):
    if path is None:
        print('source=NOT_FOUND')
        return
    print(f'source={path}')
    lines = path.read_text(errors='replace').splitlines()
    wanted = set()
    for i, line in enumerate(lines):
        if any(re.search(p, line, re.I) for p in patterns):
            for j in range(max(0, i - radius), min(len(lines), i + radius + 1)):
                wanted.add(j)
    last = -2
    for j in sorted(wanted):
        if j != last + 1 and last >= 0:
            print('...')
        print(f'{j+1:05d}: {lines[j]}')
        last = j


def dump_symbol(objdump: str, lib: str, s: Sym, max_size: int = 0x5000):
    start = s.addr & ~1
    size = s.size or 0x1000
    if size > max_size:
        size = max_size
    stop = start + size
    rc, lines = run([objdump, '-d', '--demangle',
                     f'--start-address=0x{start:x}', f'--stop-address=0x{stop:x}', lib])
    print(f'--- ARMV7_BODY name={s.name} start=0x{start:x} size=0x{size:x} stop=0x{stop:x} objdumpExit={rc} lines={len(lines)} ---')
    for line in lines:
        print(line)


def main():
    if len(sys.argv) != 5:
        print('usage: stage24225_body_fixture_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <stock-box2d-root>', file=sys.stderr)
        return 2

    nm, objdump, lib, stock = sys.argv[1:]
    print('ANGRY_STAGE24_22_5_BODY_FIXTURE_CONTRACT 1')
    print('policy=DIAGNOSTIC_ONLY; no body/fixture/material/sleep/gameplay mutation')
    print('question=does untouched ARMv7 createCircle/createBox pass Lua material values and body settings directly into Box2D, or does Rovio transform restitution/damping/body flags in a way the current ARM64 bridge does not reproduce?')
    print('priorProof=Stage24.22.4 ARMv7 constructor compares vRel against immediate -1.0f (0xbf800000), so Rovio b2_velocityThreshold is 1.0f and the threshold hypothesis is closed')
    print('runtimeRelevance=terminal shot birds use fixture friction=0.3 restitution=0.43 density=6.0 and can alternate near yVel +1.198/-0.135; current bridge also hardcodes angularDamping=1.0 for dynamic circles/boxes, a field that must be tied back to ARMv7 before further physics changes')
    print(f'lib={lib}')
    print(f'stockBox2D={stock}')

    for p in (nm, objdump, lib, stock):
        if not os.path.exists(p):
            print(f'ERROR missing={p}')
            return 3

    rc, nml = run([nm, '-S', '-C', lib])
    if rc != 0 or not nml:
        rc, nml = run([nm, '-D', '-S', '-C', lib])
    syms = parse_nm(nml)
    print(f'nmExit={rc} parsedSymbols={len(syms)}')

    by_addr = {s.addr & ~1: s for s in syms if s.typ in 'TtWw'}

    candidate_rx = re.compile(
        r'(GameLua|createCircle|createBox|CircleShape|BodyDef|FixtureDef|CreateFixture|CreateBody|Physics)',
        re.I,
    )
    print('\n--- ARMV7_CANDIDATE_SYMBOLS ---')
    candidates = [s for s in syms if s.typ in 'TtWw' and candidate_rx.search(s.name)]
    for s in candidates:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')
    if not candidates:
        print('NO_CANDIDATE_SYMBOLS')

    # Disassemble the full text once and recover concrete caller neighborhoods
    # for Box2D body/fixture construction. This works even when the wrapper itself
    # is not named createCircle/createBox.
    drc, dis = run([objdump, '-d', '--demangle', lib])
    print(f'\nfullObjdumpExit={drc} lines={len(dis)}')
    header_rx = re.compile(r'^\s*([0-9A-Fa-f]+)\s+<(.+)>:\s*$')
    call_rx = re.compile(r'\bblx?\s+0x([0-9A-Fa-f]+)\s+<([^>]+)>')
    target_rx = re.compile(
        r'(b2World::CreateBody|b2Body::CreateFixture|b2Fixture::Create|b2BodyDef::b2BodyDef|b2FixtureDef::b2FixtureDef|b2CircleShape::b2CircleShape|b2PolygonShape::SetAsBox)',
        re.I,
    )

    current_name = '<unknown>'
    current_addr = 0
    hits = []
    for i, line in enumerate(dis):
        hm = header_rx.match(line)
        if hm:
            current_addr = int(hm.group(1), 16)
            current_name = hm.group(2)
            continue
        cm = call_rx.search(line)
        if cm and target_rx.search(cm.group(2)):
            hits.append((i, current_addr, current_name, int(cm.group(1), 16), cm.group(2)))

    print('\n--- BODY_FIXTURE_CALLSITES ---')
    if not hits:
        print('NO_BODY_FIXTURE_CALLSITES')
    else:
        for n, (i, caddr, cname, taddr, tname) in enumerate(hits, 1):
            print(f'callsite={n} caller=0x{caddr:08x} {cname} target=0x{taddr:08x} {tname}')
            a = max(0, i - 20)
            b = min(len(dis), i + 24)
            for line in dis[a:b]:
                print(line)
            print()

    # Dump unique caller bodies surrounding construction. Prefer nm sizes when
    # available; otherwise keep the callsite neighborhood above as evidence.
    caller_addrs = []
    for _, caddr, _, _, _ in hits:
        ca = caddr & ~1
        if ca and ca not in caller_addrs:
            caller_addrs.append(ca)

    print('\n--- UNIQUE_CONSTRUCTION_CALLER_BODIES ---')
    dumped = 0
    for ca in caller_addrs:
        s = by_addr.get(ca)
        if s is None:
            continue
        # Keep report focused. Engine wrappers are usually small; skip giant
        # unrelated functions but retain their local callsite windows above.
        if s.size and s.size > 0x5000:
            print(f'SKIP_LARGE_CALLER addr=0x{ca:x} size=0x{s.size:x} name={s.name}')
            continue
        dump_symbol(objdump, lib, s)
        dumped += 1
    if dumped == 0:
        print('NO_SIZED_CALLER_BODIES_DUMPED')

    # Explicitly dump named GameLua/createCircle/createBox candidates. This is
    # useful when they delegate through one more engine layer than CreateBody.
    print('\n--- NAMED_GAMELUA_CREATE_CANDIDATES ---')
    named = []
    named_rx = re.compile(r'(GameLua.*create(?:Circle|Box)|createCircle|createBox)', re.I)
    for s in candidates:
        if named_rx.search(s.name) and (s.addr & ~1) not in {x.addr & ~1 for x in named}:
            named.append(s)
    if not named:
        print('NO_NAMED_GAMELUA_CREATE_CANDIDATES')
    for s in named[:16]:
        dump_symbol(objdump, lib, s)

    # Raw string offsets are not virtual addresses, but they provide a stable
    # breadcrumb if the registration wrapper is unnamed/stripped.
    blob = Path(lib).read_bytes()
    print('\n--- RAW_API_STRING_FILE_OFFSETS ---')
    for needle in (b'createCircle\x00', b'createBox\x00'):
        pos = 0
        found = []
        while True:
            j = blob.find(needle, pos)
            if j < 0:
                break
            found.append(j)
            pos = j + 1
        print(f"{needle[:-1].decode()} offsets=" + (','.join(f'0x{x:x}' for x in found) if found else 'NOT_FOUND'))

    root = Path(stock)
    print('\n--- PINNED_2_1_2_BODYDEF_DEFAULTS ---')
    print_source_focus(find_source(root, 'b2Body.h'), [
        r'b2BodyDef\(\)', r'linearDamping', r'angularDamping', r'allowSleep', r'awake',
        r'fixedRotation', r'bullet', r'active', r'inertiaScale'
    ], radius=8)

    print('\n--- PINNED_2_1_2_FIXTUREDEF_DEFAULTS_AND_CREATE ---')
    print_source_focus(find_source(root, 'b2Fixture.h'), [
        r'b2FixtureDef\(\)', r'friction', r'restitution', r'density', r'isSensor', r'filter'
    ], radius=7)
    print_source_focus(find_source(root, 'b2Body.cpp'), [
        r'CreateFixture', r'fixture->Create', r'ResetMassData'
    ], radius=8)

    print('\ninterpretationRule=do not change restitution, angularDamping, sleep thresholds, or Lua speed<0.05 yet; first resolve the original createCircle/createBox body/fixture dataflow and identify which currently reconstructed field differs')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
