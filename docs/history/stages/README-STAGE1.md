# Angry ARM64 bootstrap v0.2

Stage 0 already proved the KA3D/Lua ancestor can execute natively on Android `arm64-v8a`.

Stage 1 validates the **real Angry Birds 1.4.2 Lua 5.1 binary chunks** on ARM64.
It intentionally does not execute them yet; it decodes the historical binary format
without assuming the ARM64 host's native 8-byte `size_t`.

## Run Stage 1 on the phone

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage1-android-arm64.ps1
```

Expected ending:

```text
[angry-stage1] ALL SIX CHUNKS DECODED EXACTLY TO EOF
[angry-stage1] PASS
Stage 1 ARM64 chunk decode PASS.
```

## Prepare the actual Lua 5.1 runtime

The project also contains:

```powershell
powershell -ExecutionPolicy Bypass -File .\fetch-and-patch-lua51.ps1
```

That script downloads the official Lua 5.1.5 tarball from lua.org, verifies its official
SHA-256, and patches the runtime to match the original Angry Birds chunk ABI:

- `lua_Number = float32`
- serialized `size_t = uint32`
- Lua 5.1 chunk header stays compatible on ARM64
- `lua_dump` uses the same legacy serialized string length
- compatibility macros are generated for the old KA3D wrapper's `lua_ref` API

The next source milestone is to switch `ka3d_lua` from the bundled Lua 5.0.2 to this
patched Lua 5.1.5, load `gamelogic.lua` through the real VM, but initially **not call it**.
