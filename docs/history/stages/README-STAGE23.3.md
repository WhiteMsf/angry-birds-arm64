# Stage 23.3 — real GLES1 pbuffer BIRD_RED (ARM64)

Stage 23.2 proved two things separately:

1. the original 1.4.2 SPRT metadata maps `BIRD_RED` to `INGAME_BIRDS_1.pvr`, rect `(182,463 46x45)`, pivot `(27,27)`;
2. the original ARMv7 library imports `libGLESv1_CM.so` and fixed-function calls (`glVertexPointer`, `glTexCoordPointer`, `glMatrixMode`, client-state arrays) rather than a GLES2 shader pipeline.

Stage 23.3 joins those two discoveries on the real Android GPU without an Activity yet.

It creates an EGL pbuffer and an OpenGL ES 1.x context from a native `arm64-v8a` executable, uploads the **untouched PVR v2 RGBA4444 payload** using:

```
glPixelStorei(GL_UNPACK_ALIGNMENT, 2);
glTexImage2D(GL_TEXTURE_2D, 0,
             GL_RGBA, 1015, 1021, 0,
             GL_RGBA, GL_UNSIGNED_SHORT_4_4_4_4,
             originalPayload);
```

The unpack alignment matters: the birds atlas is 1015 pixels wide, so each packed 16-bit row is 2030 bytes. The default OpenGL unpack alignment of 4 would not describe that tightly packed row layout.

`BIRD_RED` is rendered through the fixed-function vertex/texture-coordinate array path (`glVertexPointer`, `glTexCoordPointer`, `glDrawArrays`). The stage then reads the 46x45 pbuffer back as RGBA8 and compares every channel against a CPU decode of the same original RGBA4444 source crop. A per-channel difference of at most 1 is accepted to tolerate legal normalization/rounding; any pixel with error greater than 1 fails the gate.

This is intentionally **not yet the live game renderer**. Texture filtering, blending policy, render order, background, UI, Android surface lifecycle and exact fixed-function state still need their own fidelity reconstruction. Stage 23.3 proves the byte-preserving texture path, the GLES1 API family and the exact SPRT rectangle on a real ARM64 GPU before those pieces are mixed together.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage23-3-gles1-pbuffer-sprite-android-arm64.ps1
```

Expected terminal gate:

```
[angry-stage23.3] EGL + libGLESv1_CM CONTEXT CREATED NATIVELY ON ARM64
[angry-stage23.3] ORIGINAL INGAME_BIRDS_1 RGBA4444 BYTES UPLOADED WITHOUT TRANSCODING
[angry-stage23.3] ORIGINAL BIRD_RED SPRT RECT RENDERED THROUGH GLES1 FIXED-FUNCTION VERTEX/TEXCOORD ARRAYS
[angry-stage23.3] GPU READBACK MATCHES THE ORIGINAL SOURCE CROP WITH <=1 CHANNEL ERROR
[angry-stage23.3] PASS
```
