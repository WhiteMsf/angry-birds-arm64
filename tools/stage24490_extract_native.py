#!/usr/bin/env python3
import pathlib, sys, zipfile
if len(sys.argv) != 3:
    raise SystemExit('usage: stage24490_extract_native.py <apk> <output.so>')
apk,out=sys.argv[1],pathlib.Path(sys.argv[2])
arc='lib/arm64-v8a/libangryarm64.so'
with zipfile.ZipFile(apk,'r') as z:
    data=z.read(arc)
out.parent.mkdir(parents=True,exist_ok=True)
out.write_bytes(data)
print(f'extracted={arc} bytes={len(data)} output={out}')
