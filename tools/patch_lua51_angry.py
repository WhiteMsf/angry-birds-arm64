#!/usr/bin/env python3
from pathlib import Path
import re, sys
root = Path(sys.argv[1])
conf = root/'src'/'luaconf.h'
undump = root/'src'/'lundump.c'
dump = root/'src'/'ldump.c'
gc = root/'src'/'lgc.c'
for p in (conf,undump,dump,gc):
    if not p.exists(): raise SystemExit(f'missing Lua source file: {p}')

s = conf.read_text(encoding='latin-1')
s, n1 = re.subn(r'^#define\s+LUA_NUMBER_DOUBLE\s*$', '/* Angry Birds legacy ABI: LUA_NUMBER_DOUBLE intentionally disabled */', s, flags=re.M)
s, n2 = re.subn(r'^#define\s+LUA_NUMBER\s+double\s*$', '#define LUA_NUMBER\tfloat', s, flags=re.M)
s, n3 = re.subn(r'^#define\s+LUA_NUMBER_SCAN\s+"%lf"\s*$', '#define LUA_NUMBER_SCAN\t\t"%f"', s, flags=re.M)
s, n4 = re.subn(r'^#define\s+LUA_NUMBER_FMT\s+"%\.14g"\s*$', '#define LUA_NUMBER_FMT\t\t"%.7g"', s, flags=re.M)
s, n5 = re.subn(r'^#define\s+lua_str2number\(s,p\)\s+strtod\(\(s\),\s*\(p\)\)\s*$', '#define lua_str2number(s,p)\tstrtof((s), (p))', s, flags=re.M)
if min(n1,n2,n3,n4,n5) != 1: raise SystemExit(f'luaconf patch mismatch: {n1},{n2},{n3},{n4},{n5}')
conf.write_text(s,encoding='latin-1')

s = undump.read_text(encoding='latin-1')
if '#include <stdint.h>' not in s: s=s.replace('#include <string.h>', '#include <string.h>\n#include <stdint.h>',1)
old = 'static TString* LoadString(LoadState* S)\n{\n size_t size;\n LoadVar(S,size);\n if (size==0)'
new = 'static TString* LoadString(LoadState* S)\n{\n uint32_t size32;\n size_t size;\n LoadVar(S,size32);\n size=(size_t)size32;\n if (size==0)'
if old not in s: raise SystemExit('lundump LoadString pattern not found')
s=s.replace(old,new,1)
needle='*h++=(char)sizeof(size_t);'
if needle not in s: raise SystemExit('lundump header size_t pattern not found')
s=s.replace(needle,'*h++=(char)4; /* Angry Birds serialized size_t */',1)
undump.write_text(s,encoding='latin-1')

s = dump.read_text(encoding='latin-1')
if '#include <stdint.h>' not in s: s=s.replace('#include <stddef.h>', '#include <stddef.h>\n#include <stdint.h>',1)
s,nnull=re.subn(r'  size_t size=0;\n  DumpVar\(size,D\);', '  uint32_t size=0;\n  DumpVar(size,D);', s, count=1)
s,nstr=re.subn(r'  size_t size=s->tsv\.len\+1;\s*/\* include trailing \'\\0\' \*/\n  DumpVar\(size,D\);\n  DumpBlock\(getstr\(s\),size,D\);', "  uint32_t size=(uint32_t)(s->tsv.len+1);\t\t/* include trailing '\\0' */\n  DumpVar(size,D);\n  DumpBlock(getstr(s),(size_t)size,D);", s, count=1)
if nnull != 1 or nstr != 1: raise SystemExit(f'ldump patch mismatch: {nnull},{nstr}')
dump.write_text(s,encoding='latin-1')
print('[patch-lua51] Lua 5.1.5 patched for Angry Birds chunk ABI')
print('[patch-lua51] lua_Number=float32, serialized string size=uint32, header size_t=4')

# Modern Android/Bionic FORTIFY can reject strchr(svalue(mode), ...) in Lua 5.1's
# garbage collector. TString payloads are tail-allocated immediately after the
# TString header; the old macro-based pointer can therefore look like a
# zero-sized object to Clang's object-size analysis even though Lua allocated
# the bytes correctly. Keep the original strchr semantics but scan inside a
# noinline helper so Bionic does not apply an incorrect fixed object bound.
s = gc.read_text(encoding='latin-1')
anchor = '#define VALUEWEAK       bitmask(VALUEWEAKBIT)\n'
helper = r"""
#if defined(__GNUC__) || defined(__clang__)
__attribute__((noinline))
#endif
static const char* angry_lua51_strchr(const char* s, int ch)
{
  for (;;) {
    if (*s == (char)ch) return s;
    if (*s == '\0') return NULL;
    ++s;
  }
}
"""
if 'angry_lua51_strchr' not in s:
    if anchor not in s:
        raise SystemExit('lgc helper anchor not found')
    s = s.replace(anchor, anchor + helper, 1)

old = """    weakkey = (strchr(svalue(mode), 'k') != NULL);
    weakvalue = (strchr(svalue(mode), 'v') != NULL);"""
new = """    weakkey = (angry_lua51_strchr(svalue(mode), 'k') != NULL);
    weakvalue = (angry_lua51_strchr(svalue(mode), 'v') != NULL);"""
if old not in s and 'angry_lua51_strchr(svalue(mode)' not in s:
    raise SystemExit('lgc strchr pattern not found')
s = s.replace(old, new, 1)
gc.write_text(s, encoding='latin-1')

print('[patch-lua51] Android FORTIFY compatibility patch applied to Lua 5.1 GC')
