# Angry ARM64 bootstrap v0.17 — Stage 16

Stage 16 crosses the first bird-caused destruction boundary.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage16-bird-destruction-probe-android-arm64.ps1
```

Important output should include:

```text
[stage16] armed destructive target WoodBlock2_6: strength 40 -> 4
[stage16-native] ... collisionForce=...
[stage16-queue] ... deadBlocks['WoodBlock2_6'] = ...
[stage16-legacy] ... scale=... birdVelocity ... contactEnabled=false
[stage16-callback] birdCollision(... floorDamage=4 ...)
[stage16-removeObject] DestroyBody('WoodBlock2_6') ...
[stage16-removeBlocks] AFTER frame=67 ... bodies=20 score=...
```

Expected milestone:

```text
[angry-stage16] RED BIRD DROVE WoodBlock2_6 THROUGH THE RECOVERED <=0 DAMAGE BRANCH
[angry-stage16] ARMV7 LEGACY OVERKILL VELOCITY SCALE WAS APPLIED TO THE BIRD
[angry-stage16] THE DESTRUCTIVE CONTACT WAS DISABLED BEFORE THE SOLVER
[angry-stage16] ORIGINAL Lua birdCollision() RAN, THEN ORIGINAL removeBlocks() CONSUMED deadBlocks
[angry-stage16] removeObject() DESTROYED THE Box2D BODY AND THE ORIGINAL Lua AWARDED DESTRUCTION SCORE
[angry-stage16] THE 20-BODY LEVEL1 WORLD CONTINUED AFTER A BIRD-CAUSED DESTRUCTION
[angry-stage16] PASS
```

This still uses the controlled center-overlap contact injector. A real sling
launch remains a later milestone.
