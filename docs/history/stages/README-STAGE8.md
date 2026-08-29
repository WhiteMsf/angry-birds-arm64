# Angry ARM64 bootstrap v0.9 — Stage 8

Stage 7 proved the original 941-instruction `loadLevelInternal()` loads Level1
all the way through `filterLoadedLevel`, `createObject` and `getNextBird`.

Stage 8 starts the original frame loop.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage8-original-update-android-arm64.ps1
```

Target milestone:

```text
[angry-stage8] ORIGINAL update(dt,frameTime) RAN 120 FRAMES
[angry-stage8] ORIGINAL updateGame() DROVE LEVEL1 STATE AND ENABLED REAL BOX2D
[angry-stage8] PHYSICS<->LUA OBJECT STATE SYNCHRONIZED FOR THE FRAME LOOP
[angry-stage8] PASS
```

If the original update reaches a native/UI assumption not yet reconstructed,
the harness prints the exact frame, game time and currentFrame of the first
failure. That becomes the next reconstruction boundary rather than hiding it.
