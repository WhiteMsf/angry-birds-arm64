# Angry ARM64 bootstrap v0.11 — Stage 10

Stage 9 proved the real Box2D contact-listener boundary and captured the
Level1 settling collision corpus.

Stage 10 reconstructs the **non-destructive ARMv7 block/block damage core** and
feeds those real contacts into the original Lua `blockCollision()`.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage10-block-damage-android-arm64.ps1
```

Expected interesting output:

```text
[stage10-damage] frame=... WoodBlock... strength=... -> ... defence=... metric=...
[stage10-callback] ... blockCollision(..., true) sprites: ...
[stage10] pig: strength 4.000000 -> ~2.56 sprite 'PIGLETTE_SMALL_01' -> 'PIGLETTE_SMALL_02'
```

Target milestone:

```text
[angry-stage10] ARMV7 NON-DESTRUCTIVE STRENGTH/DEFENCE DAMAGE CORE REPRODUCED
[angry-stage10] ORIGINAL blockCollision() RECEIVED REAL BOX2D CONTACTS
[angry-stage10] SMALL PIGLETTE ADVANCED TO ORIGINAL DAMAGED SPRITE
[angry-stage10] 21 LEVEL1 BODIES SURVIVED; DESTRUCTION QUEUE NOT FAKED
[angry-stage10] PASS
```

This stage deliberately stops if a collision would destroy an object. Native
destruction queue/removal and the still more complicated controllable/bird
collision branch come next.
