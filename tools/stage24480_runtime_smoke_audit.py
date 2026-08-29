#!/usr/bin/env python3
from __future__ import annotations
import pathlib, re, sys

if len(sys.argv) != 4:
    print('usage: stage24480_runtime_smoke_audit.py <stdout> <stderr> <logcat>')
    raise SystemExit(2)
paths = [pathlib.Path(x) for x in sys.argv[1:]]
texts=[]
for p in paths:
    texts.append(p.read_text(encoding='utf-8-sig', errors='replace') if p.exists() else '')
stdout, stderr, logcat = texts
alltext='\n'.join(texts)

fatal_patterns = {
    'lua_error': r'LUA ERROR|LIVE LUA FAIL',
    'gpu_failure': r'GPU frame FAIL|GPU scene initialization FAIL|LIVE GPU FAIL',
    'fatal_exception': r'FATAL EXCEPTION|Fatal signal',
    'native_signal': r'SIGSEGV|SIGABRT',
    'runtime_exception': r'RuntimeException',
    'lifecycle_rebind_failure': r'\[stage24\.47\.6-lifecycle\] REBIND_(?:FAIL|FATAL)',
}
failures=[]
for name, pat in fatal_patterns.items():
    n=len(re.findall(pat, alltext, re.I))
    if n:
        failures.append((name,n))

nonzero_gl=[]
for m in re.finditer(r'glError=0x([0-9a-fA-F]+)', alltext):
    if int(m.group(1),16)!=0:
        nonzero_gl.append(m.group(0))
if nonzero_gl:
    failures.append(('nonzero_gl_error',len(nonzero_gl)))

bad_thread=[]
for m in re.finditer(r'game thread exited rc=(-?\d+)', alltext, re.I):
    if int(m.group(1))!=0:
        bad_thread.append(m.group(0))
if bad_thread:
    failures.append(('game_thread_nonzero_exit',len(bad_thread)))

term=len(re.findall(r'\[stage24\.47\.6-lifecycle\] TERM_WINDOW .*action=PRESERVE_ENGINE', stdout))
rebind_init=len(re.findall(r'\[stage24\.47\.6-lifecycle\] INIT_WINDOW .*action=REBIND_EXISTING_ENGINE coldBoot=no', stdout))
rebound=len(re.findall(r'\[stage24\.47\.6-lifecycle\] SURFACE_REBOUND', stdout))
cold_init=len(re.findall(r'\[stage24\.47\.6-lifecycle\] INIT_WINDOW .*action=START_ENGINE coldBoot=yes', stdout))
destroy=len(re.findall(r'\[stage24\.47\.6-lifecycle\] DESTROY action=STOP_ENGINE', stdout))
levels=sorted(set(re.findall(r"loadLevel resource path[^\n]*?(?:logical=|path=|')([^'\n ]+)", alltext)))

print('ANGRY_STAGE24_48_0_RELEASE_CANDIDATE_RUNTIME 1')
print('policy=observe-only regression sweep; visual equivalence remains human/oracle-owned')
print(f'fatal_issue_count={sum(n for _,n in failures)}')
for name,n in failures:
    print(f'failure.{name}={n}')
print(f'lifecycle.term_window_preserve_count={term}')
print(f'lifecycle.rebind_existing_init_count={rebind_init}')
print(f'lifecycle.surface_rebound_count={rebound}')
print(f'lifecycle.cold_boot_init_count={cold_init}')
print(f'lifecycle.destroy_count={destroy}')
print(f'levels_seen_count={len(levels)}')
if levels:
    print('levels_seen=' + ','.join(levels[:40]))
print('lifecycle_smoke=' + ('PASS' if cold_init <= 1 and rebind_init >= 1 and term >= 1 and not any(n.startswith('lifecycle_') for n,_ in failures) else 'INCOMPLETE_OR_FAIL'))
print('runtime_safety=' + ('PASS' if not failures else 'FAIL'))
print('visual_verdict=MANUAL_ORACLE_REQUIRED')
print('verdict=' + ('PASS_RUNTIME_WITH_MANUAL_VISUAL_GATE' if not failures else 'FAIL'))
raise SystemExit(0 if not failures else 1)
