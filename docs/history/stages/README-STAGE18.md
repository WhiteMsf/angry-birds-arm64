# Stage 18 — natural launch to collision damage

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage18-natural-launch-damage-android-arm64.ps1
```

PASS requires the Stage 17 sling path plus a natural launched-bird contact
that mutates a real target through the recovered ARMv7 one-bird damage path
and invokes original Lua `birdCollision()`.
