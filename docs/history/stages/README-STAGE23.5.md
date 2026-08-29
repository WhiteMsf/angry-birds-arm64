# Stage 23.5 — full Level1 multi-sprite GLES1 GPU scene

Stage 23.5 moves the Stage 23.2 original-sprite replay off HTML canvas and into a real Android ARM64 EGL + OpenGL ES 1.x fixed-function pbuffer.

It reuses the full Level1 gameplay core (original Lua state machine, real Box2D bodies, recovered damage/destruction and the recovered ARMv7 polygon radius 0.1f), while rendering deterministic snapshots from the original `INGAME_BLOCKS_1.pvr` and `INGAME_BIRDS_1.pvr` bytes.

## Recovered ARMv7 state applied

From Stage 23.4 static callsite recovery:

- GLES1 fixed-function / client arrays
- `GL_LINEAR` magnification and non-mipped minification path
- `GL_CLAMP_TO_EDGE` for S/T
- texture storage allocation with `glTexImage2D`, followed by upload through `glTexSubImage2D`
- `glPixelStorei(GL_UNPACK_ALIGNMENT, 1)` on the texture blit/upload path
- recovered normal alpha shader templates use `GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA`
- matrices are submitted with `glMatrixMode + glLoadMatrixf`
- no GLES2 shader pipeline is introduced

The original binary also contains a `GL_ONE, GL_ONE_MINUS_SRC_ALPHA` blend template. Stage 23.5 deliberately uses the normal non-premultiplied alpha template for the original sprite atlases; exact shader-template name -> blend-template association remains a later fidelity audit.

## Snapshots

The ARM64 process captures real GPU readbacks at frames 70, 220 and 420. The latter snapshots exercise movement and damage-sprite state after gameplay has begun.

## Still intentionally non-final

This is not yet the final visual renderer. Two boundaries remain explicit in the report:

- Stage 23.2 debug camera/view is used instead of the recovered original camera.
- bodies are drawn in deterministic object-name map order instead of a claimed original render-layer/order.

Those are the next renderer-fidelity targets before Android window/lifecycle integration.
