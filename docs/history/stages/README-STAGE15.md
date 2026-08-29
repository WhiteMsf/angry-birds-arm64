# Angry ARM64 bootstrap v0.16 — Stage 15

Stage 15 applies the recovered ARMv7 exactly-one-bird collision formula to the
controlled RedBird_4 / WoodBlock2_6 contact from Stage 14.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage15-bird-damage-probe-android-arm64.ps1
```

Key output should include:

```text
[stage15] preflight native-table inputs: ...
[stage15-native] ... profile=... material=...
[stage15-native] bird mass=... speed=... => collisionForce=...
[stage15-native] target strength=... actualDamage=... newStrength=...
[stage15-callback] birdCollision(...) sprite ... score ...
```

Expected final milestone:

```text
[angry-stage15] ARMV7 ONE-BIRD damageFactors TABLE WALK RECONSTRUCTED ON ARM64
[angry-stage15] COLLISION FORCE = (BIRD MASS * BIRD SPEED / 10) * damageMultiplier
[angry-stage15] TARGET strength/defence MUTATION MATCHED THE RECOVERED NATIVE BRANCH
[angry-stage15] ORIGINAL Lua birdCollision() RECEIVED (bird,target,force,floor(actualDamage))
[angry-stage15] FIRST BIRD DAMAGE CORPUS REMAINED NON-DESTRUCTIVE AND THE 21-BODY WORLD STAYED STABLE
[angry-stage15] PASS
```

The controlled center-overlap remains a diagnostic contact injector, not the
final reconstructed sling launch.
