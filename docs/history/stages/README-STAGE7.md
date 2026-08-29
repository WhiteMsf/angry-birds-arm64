# Angry ARM64 bootstrap v0.8 — Stage 7

Stage 6 proved that the real Level1 data can be materialized through the
original `createObject()` into real Box2D 2.1.2 bodies.

Stage 7 removes the manual load-level materialization core and calls the
**original `loadLevelInternal()` function from `gamelogic.lua`**.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage7-original-loader-android-arm64.ps1
```

Expected milestone:

```text
[angry-stage7] ORIGINAL loadLevelInternal() LOADED LEVEL1 THROUGH RECONSTRUCTED loadLevel()
[angry-stage7] ORIGINAL filterLoadedLevel/createObject/getNextBird PATH COMPLETED
[angry-stage7] 21 REAL BOX2D LEVEL1 BODIES SURVIVED 120 STEPS ON ANDROID ARM64
[angry-stage7] PASS
```

This is the last major loader barrier before moving to the original per-frame
`update()` / collision-damage loop.
