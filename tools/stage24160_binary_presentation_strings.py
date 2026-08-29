#!/usr/bin/env python3
import re, sys
from pathlib import Path
if len(sys.argv)!=2:
    print('usage: stage24160_binary_presentation_strings.py <libangrybirds.so>', file=sys.stderr)
    raise SystemExit(2)
p=Path(sys.argv[1]); data=p.read_bytes()
print('ANGRY_STAGE24_16_0_ARMV7_PRESENTATION_STRINGS 1')
print(f'file={p}')
# Printable ASCII runs; retain only strings plausibly tied to display/profile contract.
pat=re.compile(rb'[ -~]{4,}')
needles=(
    'screenwidth','screenheight','viewport','resolution','display','surface','android','egl',
    'setrenderstate','setworldscale','setopleft','480x320','864x480','800x480','854x480',
    '320x240','640x360','960x640','1024x600','1280x720'
)
count=0
for m in pat.finditer(data):
    s=m.group().decode('ascii','replace')
    lo=s.lower()
    if any(n in lo for n in needles) or re.search(r'\b\d{3,4}x\d{3,4}\b', lo):
        print(f'0x{m.start():08x}\t{s}')
        count+=1
print(f'matches={count}')
