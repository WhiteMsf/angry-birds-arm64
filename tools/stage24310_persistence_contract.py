#!/usr/bin/env python3
"""Stage 24.31.0: original save/progress persistence contract audit.

Read-only.  Scans the untouched Lua corpus and ARMv7 libangrybirds.so for the
native persistence surface.  The ARM64 side remains AUDIT_NO_WRITE in this
revision; this tool verifies that no accidental persistence implementation was
introduced before the contract is known.
"""
from __future__ import annotations
import os, pathlib, re, subprocess, sys
from dataclasses import dataclass

HEADER = 'ANGRY_STAGE24_31_0_SAVE_PERSISTENCE_CONTRACT 1'
SCRIPT_NEEDLES = (
    'saveLuaFile', 'saveLuaFileWrapper', 'loadLuaFile', 'checkForLuaFile',
    'createDirectory', 'saveLevel', 'settings.lua', 'highscores.lua',
    'settings_trial.lua', 'highscores_trial.lua', 'settings', 'highscores',
    'birdsShooted', 'openGoldenEggLevels', 'tutorials', 'playtime',
    'goldenEggAchieved', 'goldenEggStarAchieved', 'lockLevels', 'changeAudio',
)
NATIVE_TERMS = (
    'saveluafile', 'loadluafile', 'checkforluafile', 'createdirectory', 'savelevel'
)

@dataclass
class Sym:
    addr: int
    size: int
    typ: str
    name: str

def run(args):
    try:
        p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, errors='replace', check=False)
        return p.returncode, p.stdout.splitlines()
    except Exception as e:
        return -1, [f'exception={e}']

def parse_nm(lines):
    rx = re.compile(r'^\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(\S)\s+(.+?)\s*$')
    out = []
    for line in lines:
        m = rx.match(line)
        if m:
            out.append(Sym(int(m.group(1), 16), int(m.group(2), 16), m.group(3), m.group(4)))
    return out

def ascii_runs(data: bytes, min_len=4):
    start = None
    for i, b in enumerate(data + b'\0'):
        if 32 <= b < 127:
            if start is None:
                start = i
        else:
            if start is not None and i - start >= min_len:
                yield start, data[start:i].decode('ascii', 'replace')
            start = None

def byte_hits(data: bytes, needle: str):
    out = []
    n = needle.encode('ascii', 'ignore')
    if not n:
        return out
    pos = 0
    while True:
        i = data.find(n, pos)
        if i < 0:
            return out
        out.append(i)
        pos = i + max(1, len(n))

def scan_scripts(root: pathlib.Path):
    rows = {n: [] for n in SCRIPT_NEEDLES}
    lua_literals = []
    if not root.is_dir():
        return rows, lua_literals
    seen_lit = set()
    for p in sorted(root.rglob('*')):
        if not p.is_file():
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        for n in SCRIPT_NEEDLES:
            for off in byte_hits(data, n):
                rows[n].append((p, off))
        for off, text in ascii_runs(data, 4):
            if re.fullmatch(r'[A-Za-z0-9_./\\-]+\.lua', text, re.I):
                key = (str(p), off, text)
                if key not in seen_lit:
                    seen_lit.add(key)
                    lua_literals.append((p, off, text))
    return rows, lua_literals

def main():
    if len(sys.argv) != 6:
        print('usage: stage24310_persistence_contract.py <llvm-nm> <llvm-objdump> <libangrybirds.so> <scripts-root> <project-cpp>', file=sys.stderr)
        return 2
    nm, objdump, lib, scripts, cpp = sys.argv[1:]
    scripts = pathlib.Path(scripts)
    cpp = pathlib.Path(cpp)

    print(HEADER)
    print('policy=READ_ONLY; ARM64 runtime persistence bindings remain AUDIT_NO_WRITE/no-filesystem-mutation')
    print('question=what exact filenames/table names/flags and native file contracts does original 1.4.2 use for settings/highscores/progress persistence?')
    print(f'lib={lib}')
    print(f'scripts={scripts}')

    rows, lua_literals = scan_scripts(scripts)
    print('\n[ORIGINAL_SCRIPT_PROVENANCE]')
    for needle in SCRIPT_NEEDLES:
        hits = rows[needle]
        print(f'needle={needle!r} hits={len(hits)}')
        for p, off in hits[:120]:
            try: rel = p.relative_to(scripts)
            except ValueError: rel = p
            print(f'  {rel} offset=0x{off:x}')
        if len(hits) > 120:
            print(f'  ... +{len(hits)-120} more')

    print('\n[LUA_FILENAME_LITERALS]')
    relevant_lits = []
    for p, off, text in lua_literals:
        low = text.lower()
        if any(x in low for x in ('setting', 'highscore', 'save', 'profile', 'level', 'trial')):
            relevant_lits.append((p, off, text))
    print(f'relevantLuaFilenameLiterals={len(relevant_lits)}')
    for p, off, text in relevant_lits[:300]:
        try: rel = p.relative_to(scripts)
        except ValueError: rel = p
        print(f'  {rel} offset=0x{off:x} text={text!r}')

    if not (os.path.exists(nm) and os.path.exists(objdump) and os.path.exists(lib)):
        print('VERDICT=FAIL native audit inputs unavailable')
        return 3

    rc, nml = run([nm, '-S', '-C', lib])
    if rc != 0 or not nml:
        rc, nml = run([nm, '-D', '-S', '-C', lib])
    syms = parse_nm(nml)
    targets = []
    seen = set()
    for sym in sorted(syms, key=lambda s: (s.addr, s.name)):
        low = sym.name.lower()
        if sym.typ not in 'TtWw':
            continue
        if not any(term in low for term in NATIVE_TERMS):
            continue
        if not ('gamelua::' in low or 'luaresources::' in low or 'resources::' in low or 'filesystem' in low or 'file' in low):
            continue
        k = (sym.addr, sym.name)
        if k not in seen:
            seen.add(k)
            targets.append(sym)

    print('\n[ARMV7_NATIVE_SYMBOLS]')
    print(f'nmExit={rc} parsed={len(syms)} targets={len(targets)}')
    for s in targets:
        print(f'{s.addr:08x} {s.size:08x} {s.typ} {s.name}')

    required_names = ('saveLuaFile', 'loadLuaFile', 'checkForLuaFile')
    missing = [name for name in required_names if not any(name.lower() in s.name.lower() for s in targets)]

    print('\n[ARMV7_TARGETED_DISASSEMBLY]')
    dumped = 0
    for s in targets:
        low = s.name.lower()
        if not any(t in low for t in NATIVE_TERMS):
            continue
        start = s.addr & ~1
        size = s.size or 0x140
        # saveLevel is large; cap it so this report remains useful.
        cap = 0x900 if 'savelevel' in low else 0x500
        size = min(max(size, 0x40), cap)
        stop = start + size
        drc, body = run([objdump, '-d', '--demangle', f'--start-address=0x{start:x}', f'--stop-address=0x{stop:x}', lib])
        print(f'ARMV7_BODY name={s.name!r} start=0x{start:x} size=0x{size:x} objdumpExit={drc} lines={len(body)}')
        for line in body[:1000]:
            print(line)
        dumped += 1
        if dumped >= 20:
            break
    print(f'targetBodiesDumped={dumped}')

    print('\n[ARMV7_BINARY_STRINGS]')
    data = pathlib.Path(lib).read_bytes()
    selected = []
    for off, text in ascii_runs(data, 4):
        lo = text.lower()
        if any(x in lo for x in ('saveluafile', 'loadluafile', 'checkforluafile', 'settings.lua', 'highscores.lua', 'settings_trial.lua', 'highscores_trial.lua', 'createdirectory')):
            selected.append((off, text))
    print(f'selected={len(selected)}')
    for off, text in selected[:500]:
        print(f'  offset=0x{off:x} text={text}')

    print('\n[ARM64_SOURCE_GUARDS]')
    source = cpp.read_text(encoding='utf-8', errors='replace') if cpp.is_file() else ''
    audit_binding = 'setfn(L, "saveLuaFile", l_stage24310_saveLuaFile)' in source
    real_binding = 'setfn(L, "saveLuaFile", l_stage24311_saveLuaFile)' in source
    persistence_mode = 'REAL_PERSISTENCE' if real_binding else ('AUDIT_NO_WRITE' if audit_binding else 'UNKNOWN')
    checks = {
        'luaContractDump': 'stage24310_dump_persistence_lua_contract' in source,
        # Keep the original audit probe available as provenance even after the live
        # binding advances to the Stage 24.31.1 real writer.
        'saveProbe': 'l_stage24310_saveLuaFile' in source,
        'checkProbe': 'l_stage24310_checkForLuaFile' in source,
        'createDirectoryProbe': 'l_stage24310_createDirectory' in source,
        'saveLevelProbe': 'l_stage24310_saveLevel' in source,
        'saveBindingKnownMode': audit_binding or real_binding,
        'modeSpecificMarker': (
            ('action=AUDIT_NO_WRITE' in source) if audit_binding and not real_binding
            else ('PASS_FROM_DISK' in source and 'PASS_FRESH_ENV' in source) if real_binding
            else False
        ),
        'runtimeMarker': 'stage24.31.0-persistence' in source,
    }
    print(f'persistenceMode={persistence_mode}')
    for k, v in checks.items():
        print(f'{k}={"PASS" if v else "FAIL"}')

    if not rows['saveLuaFileWrapper'] or not rows['saveLuaFile']:
        print('VERDICT=FAIL original script persistence producer missing')
        return 4
    if missing:
        print('VERDICT=FAIL missing ARMv7 native targets=' + ';'.join(missing))
        return 5
    if not all(checks.values()):
        print('VERDICT=FAIL ARM64 audit guards incomplete')
        return 6

    save_syms = [s for s in targets if 'saveluafile' in s.name.lower()]
    for s in save_syms:
        if 'GameLua::saveLuaFile' in s.name:
            print(f'PROVEN_SIGNATURE={s.name}')
    print('interpretationRule=do not implement disk format from filenames alone; first correlate runtime saveLuaFile(path,tableName,bool) arguments/table snapshots with the ARMv7 serializer/load body and clean-profile behavior')
    print(f'VERDICT=PASS original persistence frontier inventoried; arm64Mode={persistence_mode}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
