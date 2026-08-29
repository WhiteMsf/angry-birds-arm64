$ErrorActionPreference = 'Stop'

# Fetch the official Lua 5.1.5 source and prepare it for Angry Birds' historical
# bytecode ABI. This script does NOT alter the OS; it only writes under vendor\.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$vendor = Join-Path $root 'vendor'
$archive = Join-Path $vendor 'lua-5.1.5.tar.gz'
$luaDir = Join-Path $vendor 'lua-5.1.5'

New-Item -ItemType Directory -Force -Path $vendor | Out-Null

$url = 'https://www.lua.org/ftp/lua-5.1.5.tar.gz'
$expected = '2640fc56a795f29d28ef15e13c34a47e223960b0240e8cb0a82d9b0738695333'

Write-Host "Downloading official Lua 5.1.5..."
Invoke-WebRequest -Uri $url -OutFile $archive

$actual = (Get-FileHash -Algorithm SHA256 $archive).Hash.ToLowerInvariant()
if ($actual -ne $expected) {
    throw "Lua 5.1.5 SHA256 mismatch. Expected $expected, got $actual"
}

if (Test-Path $luaDir) { Remove-Item $luaDir -Recurse -Force }

Write-Host "Extracting..."
tar -xzf $archive -C $vendor
if ($LASTEXITCODE -ne 0) { throw 'tar extraction failed.' }

$conf = Join-Path $luaDir 'src\luaconf.h'
$undump = Join-Path $luaDir 'src\lundump.c'
$dump = Join-Path $luaDir 'src\ldump.c'

foreach ($p in @($conf, $undump, $dump)) {
    if (!(Test-Path $p)) { throw "Lua source file missing: $p" }
}

# 1) lua_Number must be float32, matching every Angry Birds chunk header.
$s = [IO.File]::ReadAllText($conf)
$s = $s.Replace("#define LUA_NUMBER_DOUBLE`n#define LUA_NUMBER      double",
                "/* Angry Birds 1.4.2 legacy ABI: lua_Number is float32 */`n#define LUA_NUMBER      float")
$s = $s.Replace('#define LUA_NUMBER_SCAN         "%lf"',
                '#define LUA_NUMBER_SCAN         "%f"')
$s = $s.Replace('#define LUA_NUMBER_FMT          "%.14g"',
                '#define LUA_NUMBER_FMT          "%.7g"')
$s = $s.Replace('#define lua_str2number(s,p)     strtod((s), (p))',
                '#define lua_str2number(s,p)     strtof((s), (p))')
[IO.File]::WriteAllText($conf, $s, [Text.UTF8Encoding]::new($false))

# 2) Serialized strings in the original chunks use a 32-bit size_t even though
# the ARM64 host has an 8-byte native size_t.
$s = [IO.File]::ReadAllText($undump)
$s = $s.Replace('#include <string.h>',
                "#include <string.h>`n#include <stdint.h>")
$old = @'
 size_t size;
 LoadVar(S,size);
 if (size==0)
'@
$new = @'
 uint32_t serialized_size;
 size_t size;
 LoadVar(S,serialized_size);
 size=(size_t)serialized_size;
 if (size==0)
'@
if (!$s.Contains($old)) {
    throw 'Could not locate Lua 5.1.5 LoadString pattern in lundump.c.'
}
$s = $s.Replace($old, $new)
$s = $s.Replace('*h++=(char)sizeof(size_t);',
                '*h++=(char)4; /* Angry Birds serialized size_t */')
[IO.File]::WriteAllText($undump, $s, [Text.UTF8Encoding]::new($false))

# 3) Keep lua_dump consistent with the same legacy chunk ABI.
$s = [IO.File]::ReadAllText($dump)
$s = $s.Replace('#include <stddef.h>',
                "#include <stddef.h>`n#include <stdint.h>")
$oldNull = @'
  size_t size=0;
  DumpVar(size,D);
'@
$newNull = @'
  uint32_t size=0;
  DumpVar(size,D);
'@
$oldStr = @'
  size_t size=s->tsv.len+1;             /* include trailing '\0' */
  DumpVar(size,D);
  DumpBlock(getstr(s),size,D);
'@
$newStr = @'
  uint32_t size=(uint32_t)(s->tsv.len+1); /* include trailing '\0' */
  DumpVar(size,D);
  DumpBlock(getstr(s),(size_t)size,D);
'@
if (!$s.Contains($oldNull) -or !$s.Contains($oldStr)) {
    throw 'Could not locate Lua 5.1.5 DumpString patterns in ldump.c.'
}
$s = $s.Replace($oldNull, $newNull)
$s = $s.Replace($oldStr, $newStr)
[IO.File]::WriteAllText($dump, $s, [Text.UTF8Encoding]::new($false))

# Compatibility macros used by the 2007 KA3D wrappers.
$compat = @'
#pragma once
#include "lua.h"
#include "lauxlib.h"

#ifndef lua_ref
#define lua_ref(L,lock) ((lock) ? luaL_ref((L), LUA_REGISTRYINDEX) : \
  (lua_pushliteral((L), "unlocked references are obsolete"), lua_error((L)), 0))
#endif
#ifndef lua_unref
#define lua_unref(L,ref) luaL_unref((L), LUA_REGISTRYINDEX, (ref))
#endif
#ifndef lua_getref
#define lua_getref(L,ref) lua_rawgeti((L), LUA_REGISTRYINDEX, (ref))
#endif
'@
$compatPath = Join-Path $luaDir 'src\ka3d_lua51_compat.h'
[IO.File]::WriteAllText($compatPath, $compat, [Text.UTF8Encoding]::new($false))

Write-Host ""
Write-Host "Lua 5.1.5 prepared:"
Write-Host "  $luaDir"
Write-Host "  lua_Number: float32"
Write-Host "  serialized size_t: uint32"
Write-Host "  SHA256 verified: $actual"
