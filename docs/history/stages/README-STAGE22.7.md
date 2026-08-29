# Stage 22.7 — recovered-physics full-Level1 regression

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage22-7-recovered-physics-regression-android-arm64.ps1
```

## Purpose

Stage 22.6 strongly confirmed that the ARMv7-recovered polygon shape radius
`0.1f` eliminates the suspicious zero-input SmallPiglette damage in Level1.
Stage 22.7 promotes that value from an A/B experiment to the normal reconstructed
GameLua `createBox()` path and reruns the complete three-bird Level1 lifecycle.

The stage is intentionally a regression gate before renderer work begins. It must
prove both sides at once:

- hold the first input until frame 120, past the old frame-83 failure window;
- no pig damage mutation during that entire idle soak;
- all three birds still launch through original Lua input routing;
- natural contacts/damage/destruction still occur after release;
- the original Lua reaches a genuine COMPLETE or FAILED terminal;
- all Box2D bodies remain finite;
- the Stage 22 replay is still generated for visual inspection.

Expected fidelity line:

```text
[stage22.7-fidelity] polygonRadius=0.100000 ... pigDamageMutationsBeforeInput=0 pigDamageBeforeInput=0.000000000
```

Expected end:

```text
[angry-stage22.7] PASS
Stage 22.7 recovered-physics full-Level1 regression ARM64 PASS.
```

Once this passes, Stage 23 can begin the original sprite/PVR rendering pipeline
without carrying the known polygon-skin discrepancy into the renderer era.
