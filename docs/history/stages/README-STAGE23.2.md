# Stage 23.2 — original-sprite offline replay

Stage 23.2 is the first visual pass that replaces the Stage 22 debug body fill
with pixels from the original Angry Birds Classic 1.4.2 sprite atlases.

What is proven before this stage:

- Stage 23.0 maps each Level1 sprite to an exact SPRT sheet, texture, rect and pivot.
- `BIRD_RED` is `INGAME_BIRDS_1.pvr`, rect `(182,463,46,45)`, pivot `(27,27)`.
- Stage 23.1 proves both Level1 PVRs are v2, one-level, uncompressed
  `GL_RGBA_4444` payloads with exact lengths and no vertical-flip flag.
- Physics scale is 20 original source pixels per physics world unit.

What this stage does:

1. Extract the untouched `.pvr` files from the original APK asset ZIPs.
2. Decode RGBA4444 to RGBA PNG **only as a browser/debug view**. This does not
   change the final renderer contract; live GLES will upload the original PVR
   payload bytes directly.
3. Run the complete Level1 ARM64 gameplay regression again.
4. Capture the runtime sprite name on every body frame, including damage-sprite
   replacement.
5. Draw the exact SPRT source rectangle at the exact SPRT pivot over the real
   Box2D/Lua transform.
6. Keep debug collision geometry as an optional overlay.
7. Expose a `flip atlas Y` toggle so the remaining KA3D atlas-Y convention is
   resolved visually instead of guessed.
8. Statically inspect the original ARMv7 `libangrybirds.so` with NDK `llvm-readelf`
   and record its GLES/EGL dependencies/imports before any live renderer API is chosen.

## Run

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage23-2-original-sprite-replay-android-arm64.ps1
```

The script opens:

`stage23-2-output\angry-stage23-2-original-sprite-replay.html`

The two adjacent PNG files must stay beside the HTML. The script also writes
`stage23-2-output\original-armv7-gles-imports.txt`.

## Gate

The native run must still complete Level1 and print:

```text
[stage23.2-red] BIRD_RED texture='INGAME_BIRDS_1.pvr' rect=(182,463 46x45) pivot=(27,27)
[angry-stage23.2] PASS
```

Then visually compare the default atlas-Y convention against the `flip atlas Y`
toggle. One should show the expected original birds/blocks; that observation
becomes the next recovered renderer invariant.

This is intentionally still an **offline renderer stage**. It does not choose
GLES1 versus GLES2, texture filtering, blend state or Android EGL lifecycle.
Those remain live-renderer fidelity work after the original binary/API path is
proven.
