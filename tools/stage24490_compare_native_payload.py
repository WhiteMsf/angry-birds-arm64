#!/usr/bin/env python3
import hashlib, sys, zipfile
if len(sys.argv) != 3:
    raise SystemExit('usage: stage24490_compare_native_payload.py <audit.apk> <release.apk>')
arc='lib/arm64-v8a/libangryarm64.so'
def payload(path):
    with zipfile.ZipFile(path,'r') as z:
        names=z.namelist()
        libs=[n for n in names if n.startswith('lib/') and n.endswith('.so')]
        if libs != [arc]:
            raise SystemExit(f'{path}: native payload mismatch libs={libs!r}')
        data=z.read(arc)
        return hashlib.sha256(data).hexdigest(), len(data)
a_sha,a_len=payload(sys.argv[1])
r_sha,r_len=payload(sys.argv[2])
print('ANGRY_STAGE24_49_0_NATIVE_PAYLOAD_EQUIVALENCE 1')
print(f'audit_sha256={a_sha}')
print(f'release_sha256={r_sha}')
print(f'audit_bytes={a_len}')
print(f'release_bytes={r_len}')
print('same_native_payload=' + ('PASS' if a_sha==r_sha and a_len==r_len else 'FAIL'))
if a_sha != r_sha or a_len != r_len:
    raise SystemExit(1)
