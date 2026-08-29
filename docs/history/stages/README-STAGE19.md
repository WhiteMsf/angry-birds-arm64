# Stage 19 — full natural shot lifecycle

Run on the connected ARM64 Android device:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage19-full-turn-android-arm64.ps1
```

Useful log prefixes:

```text
[stage19-blockdamage]
[stage19-lifecycle]
[stage19] full-damage summary
[stage19] lifecycle summary
[angry-stage19]
```

If original Lua reaches another unreconstructed headless subsystem before the
turn finishes, the run fails there rather than fabricating gameplay state.
