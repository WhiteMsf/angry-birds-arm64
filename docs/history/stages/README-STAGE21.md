# Stage 21 — complete Level1 headless run

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage21-full-level-android-arm64.ps1
```

Useful output:

```text
[stage21-shot]
[stage21-lifecycle]
[stage21] full-damage summary
[angry-stage21] ... LEVEL COMPLETE / LEVEL FAILED ...
[angry-stage21] PASS
```

This stage does not require victory specifically. A genuine original
`LEVEL COMPLETE` or `LEVEL FAILED` after all three birds is a valid proof that
Level1 reached a terminal gameplay state without a renderer.


## v0.22.1 note

A ready next bird is pressed only when original `updateGame()`'s LBUTTON
router can reach sling selection:

```text
flyingBird == nil OR birdSpecialtyAvailable == false
```

This avoids accidentally spending a click on the previous flying bird's
specialty.


## v0.22.2 terminal classification

Original `updateGame()` can call both `initLevelComplete()` and
`initLevelFailed(dt)` on the same transition frame because the checks are
sequential. A one-dt `levelFailedTimer` pulse while `levelCompleted=true` is
therefore logged but classified as COMPLETE.
