#!/usr/bin/env python3
import re, sys
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit('usage: stage24151_theme_binary_strings.py <libangrybirds.so>')
p=Path(sys.argv[1]); data=p.read_bytes()
pat=re.compile(rb'[ -~]{4,}')
want=re.compile(r'(?i)(theme|background|foreground|parallax|ingame_(?:skies|grounds|parallax|theme_ground)|layer_[123]|settheme)')
rows=[]
for m in pat.finditer(data):
    s=m.group().decode('ascii','ignore')
    if want.search(s): rows.append((m.start(),s))
print('binary='+str(p))
print('matches=%d'%len(rows))
for off,s in rows:
    print('0x%08x\t%s'%(off,s))
