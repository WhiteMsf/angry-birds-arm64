# Angry ARM64 bootstrap v0.12 — Stage 11

Stage 10 proved the recovered collision damage rule and original Lua
`blockCollision()` / damage-sprite behavior.

Stage 11 corrects the native ARMv7 scheduling:

- Box2D fixed at 30 Hz (`1/30`)
- `Step(..., 10, 10)`
- physics before Lua `update(dt,dt)`
- original `removeBlocks()` after each fixed step
- `ClearForces()` after the fixed-step loop

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage11-native-driver-android-arm64.ps1
```

Key transition:

```text
[stage11] ORIGINAL updateGame enabled Box2D at Lua frame=61 ... fixedStepsThisFrame=0
[stage11] frame=62 ... fixedSteps=0 accumulator≈0.0166667
[stage11] FIRST native-order fixed Step frame=63 ... dt≈0.0333333 iter=10/10
```

Expected final proof:

```text
[stage11] ... firstFixedStepFrame=63 fixedSteps=29 removeBlocksCalls=29 updateCalls=120
[angry-stage11] ARMV7 NATIVE FIXED-STEP ORDER RECONSTRUCTED
[angry-stage11] BOX2D STEPPED AT 1/30 WITH 10/10 ITERATIONS BEFORE LUA update()
[angry-stage11] ORIGINAL removeBlocks() CALLED AFTER EACH PHYSICS STEP
[angry-stage11] FRAME 61 ENABLED PHYSICS; FIRST FIXED STEP OCCURRED AT FRAME 63
[angry-stage11] PASS
```

Collision damage is disabled here on purpose. After this timing pass, Stage
10's recovered damage can be reintroduced on the correct driver, then the
native `deadBlocks` destruction/removeObject pipeline can be reconstructed.
