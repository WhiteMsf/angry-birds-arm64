#!/usr/bin/env python3
from __future__ import annotations
import pathlib, re, subprocess, sys
if len(sys.argv) != 3:
    raise SystemExit('usage: stage24490_elf_16k_audit.py <llvm-readelf> <lib.so>')
readelf, so = sys.argv[1], sys.argv[2]
p=subprocess.run([readelf,'-lW',so],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print('ANGRY_STAGE24_49_0_ELF_16K_AUDIT 1')
print(p.stdout.rstrip())
if p.returncode:
    print(f'readelf_exit={p.returncode}')
    raise SystemExit(1)
aligns=[]
for line in p.stdout.splitlines():
    if re.match(r'^\s*LOAD\s', line):
        m=re.search(r'\s(0x[0-9a-fA-F]+)\s*$', line)
        if m: aligns.append(int(m.group(1),16))
if not aligns:
    print('load_segments=0')
    print('verdict=FAIL_NO_LOAD_SEGMENTS')
    raise SystemExit(1)
print('load_alignments=' + ','.join(hex(x) for x in aligns))
ok=all(x >= 0x4000 for x in aligns)
print('all_load_segments_at_least_16k=' + ('PASS' if ok else 'FAIL'))
if not ok: raise SystemExit(1)
print('verdict=PASS')
