# Angry ARM64 bootstrap v0.10 — Stage 9

Stage 8 is complete: the original Angry Birds Level1 frame loop now runs for
120 frames on Android ARM64 and the original Lua logic enables the real Box2D
world at frame 61.

Stage 9 adds a real `b2ContactListener` to the compatibility kernel.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage9-contact-probe-android-arm64.ps1
```

You should see contact rows such as:

```text
[stage9-contact] frame=... WoodBlock... <-> ... relSpeed=... armv7Metric=... class=blockCollision
```

and a final corpus summary.

Target milestone:

```text
[angry-stage9] REAL b2ContactListener RECEIVED LEVEL1 CONTACTS ON ARM64
[angry-stage9] ARMV7 BeginContact MOMENTUM METRIC REPRODUCED FOR THE CONTACT CORPUS
[angry-stage9] COLLISIONS CLASSIFIED FOR ORIGINAL birdCollision/blockCollision DISPATCH
[angry-stage9] PASS
```

Stage 9 intentionally does **not** apply damage yet. That keeps the next step
scientific: reconstruct the original strength/defence mutation from ARMv7
against an observed real contact corpus instead of guessing it.
