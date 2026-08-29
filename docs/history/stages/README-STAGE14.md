# Angry ARM64 bootstrap v0.15 — Stage 14

Stage 14 creates the first controlled real contact involving the active
RedBird on the recovered native 30 Hz driver.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage14-bird-contact-probe-android-arm64.ps1
```

Expected interesting lines:

```text
[stage14] bird preflight: name=RedBird_4 controllable=true ...
[stage14-launch] CONTROLLED contact probe frame=67 ...
[stage11-contact] ... RedBird_4 <-> ... class=birdCollision
[stage14] bird-contact summary: ... activeBirdContacts=>0 ...
```

Target:

```text
[angry-stage14] ACTIVE RedBird_4 ENTERED A REAL Box2D CONTACT ON THE NATIVE 30HZ DRIVER
[angry-stage14] CONTACT WAS CLASSIFIED THROUGH THE ORIGINAL CONTROLLABLE/BIRD STATE
[angry-stage14] ONE-BIRD ARMV7 BeginContact BRANCH NOW HAS A RUNTIME CORPUS FOR STATIC RECONSTRUCTION
[angry-stage14] NO birdCollision() DAMAGE SEMANTICS WERE GUESSED
[angry-stage14] PASS
```

This is not the sling yet. It is a controlled collision microprobe designed
to give the static ARMv7 bird branch real runtime values before we implement
its damage/scoring semantics.


## v0.15.1 diagnostic change

The contact microprobe now starts RedBird_4 with a small deliberate overlap
against WoodBlock2_6 and prints pre/post-Step Box2D state. This removes the
last geometric ambiguity from the probe.


## v0.15.2

The controlled overlap is held across native fixed steps 67 and 69. This
accounts for Box2D 2.1.x broadphase/contact staging: candidate creation can
occur at the end of one Step and BeginContact on the following Step.
