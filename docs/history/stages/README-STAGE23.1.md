# Stage 23.1 — corrected original PVR v2 pixel-format/payload audit

The first 23.1 run deliberately failed instead of guessing: both Level1 atlases used legacy PVR v2 `pixelType=0x10`, which the initial auditor did not decode.

The recovered header is not PVRTC. In the official Imagination Technologies legacy PVR enum, `0x10` is `GL_RGBA_4444`. The observed headers also carry:

- `bitCount=16`;
- channel masks `R=0xF000 G=0x0F00 B=0x00F0 A=0x000F`;
- alpha flag `0x8000`;
- no mipmap flag (`0x0100` absent);
- no vertical-flip flag (`0x10000` absent);
- one surface.

Stage 23.1 now recognizes the legacy PVR format enum instead of assuming every texture payload is PVRTC. For uncompressed formats it computes the exact raw byte count; for PVRTC formats it retains the compressed-size audit.

For the two Level1 atlases, passing this stage establishes the byte-preserving GLES upload contract:

```cpp
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
             GL_RGBA, GL_UNSIGNED_SHORT_4_4_4_4, payload);
```

No conversion, decompression or `glCompressedTexImage2D` is used for these textures. Texture filtering/wrap state is intentionally left for the next renderer audit rather than guessed here.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage23-1-pvr-payload-audit-android-arm64.ps1
```
