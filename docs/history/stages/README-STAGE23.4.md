# Stage 23.4 — original ARMv7 GLES1 state/callsite audit

Stage 23.3 proved that the original RGBA4444 atlas can travel through a real
ARM64 OpenGL ES 1.x context with zero pixel error. That does **not** yet prove
that the replacement renderer uses the same fixed-function state as the 1.4.2
ARMv7 binary.

This stage therefore does not draw anything new. It audits the original
`libangrybirds.so` itself with the NDK LLVM tools and captures callsite context
for the fixed-function operations that can materially change the final image:

- texture upload / pixel unpack state;
- min/mag filtering and wrap mode;
- texture environment;
- alpha blending and alpha test;
- enable/disable state;
- projection/model-view matrices and transforms;
- viewport/scissor;
- vertex / UV / color client arrays;
- draw primitive calls.

The report includes 18 instructions before and 4 instructions after each direct
GL call, plus best-effort enum hints. The hints are convenience only: the raw
ARMv7 callsite context is the evidence and must be inspected before promoting a
state into the ARM64 renderer.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage23-4-armv7-gles1-state-audit.ps1
```

Outputs:

- `stage23-4-output/original-armv7-gles1-state-summary.txt`
- `stage23-4-output/original-armv7-gles1-state-callsites.txt`
- `stage23-4-output/original-armv7-libangrybirds-disassembly.txt`

Expected gate:

```text
[angry-stage23.4] FILTER / BLEND / MATRIX / CLIENT-ARRAY CALLSITE CONTEXT CAPTURED
[angry-stage23.4] NO MODERN GLES STATE HAS BEEN ASSUMED FOR THE LIVE ARM64 RENDERER
[angry-stage23.4] PASS
```

The next renderer stage should consume only states supported by this audit, then
render a multi-sprite Level1 scene through GLES1 before the Android window/JNI
lifecycle is introduced.
