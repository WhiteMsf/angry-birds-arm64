#!/usr/bin/env python3
import shutil, sys, zipfile
if len(sys.argv) != 5:
    raise SystemExit('usage: apk_add_native_lib.py input.apk output.apk lib.so apk/path.so')
src, dst, lib, arc = sys.argv[1:]
shutil.copyfile(src, dst)
with zipfile.ZipFile(dst, 'a', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    # Reject accidental duplicate entry if the packaging method changes later.
    if arc in z.namelist():
        raise SystemExit(f'duplicate APK entry already exists: {arc}')
    z.write(lib, arc)
print(f'[stage24-apk] added {lib} -> {arc}')
