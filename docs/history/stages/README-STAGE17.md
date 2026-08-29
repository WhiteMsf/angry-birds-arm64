# Angry ARM64 bootstrap v0.18 — Stage 17

Stage 17 replaces the artificial bird teleport/contact injector with the
original Lua slingshot release path.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage17-original-sling-launch-android-arm64.ps1
```

Interesting output should include:

```text
[stage17-input] READY ... -> PRESS
[stage17-state] AFTER PRESS ... selectedBird=table dragStarted=true
[stage17-input] DRAG ...
[stage17-state] AFTER DRAG ... rubberBandLength=... max=...
[stage17-input] RELEASE ...
[stage17-impulse] applyImpulse(...) velocity (...) -> (...)
[stage17-state] AFTER RELEASE ... flyingBird=... shot=true ...
[stage17-flight] +30 render frames ...
```

Expected milestone:

```text
[angry-stage17] ORIGINAL animateBirdToSlingShot() DELIVERED A REAL BIRD TO THE SLING
[angry-stage17] ORIGINAL updateGame() SELECTED THE BIRD FROM LBUTTON/CURSOR INPUT
[angry-stage17] ORIGINAL RUBBER-BAND DRAG COMPUTED rubberBandPos/rubberBandLength/shootMaxLength
[angry-stage17] ORIGINAL RELEASE PATH CALLED setPosition + setVelocity + applyImpulse
[angry-stage17] ORIGINAL Lua SET flyingBird/shot/birdFired AND CLEARED currentBirdName/selectedBird
[angry-stage17] THE RELEASED BIRD FLEW UNDER THE RECOVERED NATIVE 30HZ Box2D DRIVER
[angry-stage17] PASS
```

This is the first stage where the bird launch itself comes from the original
gameplay input state machine rather than a diagnostic body teleport.
