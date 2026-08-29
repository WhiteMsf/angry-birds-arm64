# Angry Birds Classic 1.4.2 ARM64 bootstrap v0.3

Stage 0 PASS: KA3D ancestor executes on Android ARM64.
Stage 1 PASS: all six original Lua 5.1 chunks decode exactly to EOF on Android ARM64.
Stage 2: patched real Lua 5.1.5 VM loads those chunks as functions, without executing them.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage2-lua51-load-android-arm64.ps1
```

Expected ending:

```text
[angry-stage2] gamelogic.lua    LOAD OK ... type=function
[angry-stage2] ALL SIX ORIGINAL CHUNKS ARE REAL LUA FUNCTIONS ON ARM64
[angry-stage2] PASS
Stage 2 real Lua 5.1 ARM64 load PASS.
```
