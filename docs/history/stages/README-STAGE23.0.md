# Stage 23.0 — original SPRT / Level1 sprite manifest audit

Stage 22.7 promoted the recovered ARMv7 polygon skin radius (`0.1f`) into the
normal reconstructed Box2D path and passed a complete Level1 regression with no
pre-input pig damage.

Stage 23.0 begins renderer reconstruction, but deliberately does **not** draw a
single guessed pixel yet.

It extends the existing KA3D `SPRT` parser so the original texture-name list is
preserved instead of discarded. After the original Lua loader materializes
Level1, the ARM64 harness emits a deterministic TSV mapping each native body / Lua
object with a sprite to:

- object name and definition;
- Lua sprite name;
- source `.dat` sheet;
- texture name declared by that sheet;
- atlas `x/y/width/height`;
- sprite pivot `x/y`;
- current `damageSprite` and any `setTexture()` metadata override.

It also records the renderer-facing bindings that remain stubbed or metadata-only.

## Fidelity gate

Stage 23.0 refuses to guess. It fails if:

- either loaded Level1 object sheet has anything other than one unambiguous
  texture declaration;
- a materialized Level1 object names a sprite absent from the loaded original
  SPRT sheets;
- a mapped sprite cannot be assigned an exact texture;
- fewer than 20 Level1 physical objects expose resolvable sprites.

The full Stage 22.7 Level1 gameplay/replay run remains attached as a regression
check after the manifest is written.

## Run

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage23-0-sprite-manifest-audit-android-arm64.ps1
```

Expected new lines include:

```text
[stage23.0-sheet] INGAME_BLOCKS_1.dat ... texture[0]='...'
[stage23.0-sheet] INGAME_BIRDS_1.dat  ... texture[0]='...'
[stage23.0-manifest] ... mapped=20 missing=0 unresolvedTexture=0
[angry-stage23.0] EXACT LEVEL1 SPRITE -> SHEET/TEXTURE/RECT/PIVOT MANIFEST PASS
...
Stage 23.0 original SPRT + Level1 sprite manifest audit ARM64 PASS.
```

The interesting artifact is:

`stage23-0-output/angry-stage23-0-sprite-manifest.tsv`

That file is the input evidence for Stage 23.1 (PVR/PVRTC container + texture
loader proof). Stage 23.1 must use the untouched original texture archive(s) named
by this manifest rather than assuming filenames or formats.
