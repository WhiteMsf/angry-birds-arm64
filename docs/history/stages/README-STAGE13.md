# Angry ARM64 bootstrap v0.14 — Stage 13

Stage 13 crosses the first real object-destruction boundary.

It deliberately lowers only `WoodBlock6_5.strength` from 70 to 0.75 so the
already-observed corrected-timing collision at about frame 81 kills that one
ordinary block.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage13-destruction-pipeline-android-arm64.ps1
```

The important sequence should look like:

```text
[stage13-damage] ... WoodBlock6_5 DESTROY strength=0.7500 -> negative ...
[stage13-queue] ... deadBlocks['WoodBlock6_5'] = objects.world['WoodBlock6_5']

[stage13-removeBlocks] ENTER ... deadBlocks=1 nativeBodies=21
[stage13-removeObject] DestroyBody('WoodBlock6_5') ... nativeBodiesNow=20
[stage13-removeBlocks] EXIT ... deadBlocks=0 nativeBodies=20 destroyed=yes

[stage13] post-removeBlocks target state:
objects.world=nil deadBlocks=nil levelGoals=nil nativeBody=gone score=...
```

Target proof:

```text
[angry-stage13] ARMV7 <=0 DAMAGE BRANCH QUEUED THE ORIGINAL Lua deadBlocks TABLE
[angry-stage13] ORIGINAL removeBlocks() CONSUMED THE DEAD OBJECT AND CALLED NATIVE removeObject()
[angry-stage13] RECONSTRUCTED removeObject() CALLED b2World::DestroyBody AND REMOVED THE NATIVE OBJECT
[angry-stage13] ORIGINAL Lua CLEANED objects.world/deadBlocks/levelGoals AND AWARDED DESTRUCTION SCORE
[angry-stage13] 20-BODY LEVEL1 WORLD CONTINUED STABLY AFTER THE CONTROLLED DESTRUCTION
[angry-stage13] PASS
```

This is still a controlled probe, not a claim that the full native
`removeObject()` has been reproduced for every joint/special-object case.
