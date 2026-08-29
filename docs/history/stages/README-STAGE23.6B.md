# Stage 23.6B — original 1.4.2 camera on the ARM64 GLES1 scene

Stage 23.6B removes the Stage 23.2 debug camera. It leaves the original camera
controller in `gamelogic.lua` untouched and reconstructs only the two native
publication calls proven by the ARMv7 binary: `setTopLeft(x,y)` and
`setWorldScale(scale)`.

## Recovered camera path

The original Lua path remains authoritative:

- `initCameras()` resolves the active `deviceModel` camera profiles and initializes
  screen/scale state;
- `levelStartCamera(dt)` owns the opening castle hold and transition;
- `doItAllCamera(dt)` owns the later zoom/sweep/follow behavior;
- `defaultCamera(dt)` derives `screen.left/top/right/bottom` and publishes
  `setTopLeft(screen.left + cameraShakeX, screen.top + cameraShakeY)`;
- native `setWorldScale` publishes the Lua-computed zoom to the renderer.

The ARM64 renderer therefore uses:

```
worldX = physicsX * physicsToWorld
worldY = physicsY * physicsToWorld
screenX = (worldX - topLeftX) * worldScale
screenY = (worldY - topLeftY) * worldScale
```

Atlas sprite vertices remain in original source-pixel units, so their model scale
is `worldScale`; their centers are the interpolated Stage 23.6A physics transforms
converted through `physicsToWorld`.

The synthetic touch harness follows the original Lua inverse path separately:
`screenToWorldTransform()` uses `screen.left/top` and `worldScale`, then
`worldToPhysicsTransform()` applies `physicsScale`. Camera shake is deliberately
absent from input conversion, matching the original: shake is only added when
`defaultCamera()` publishes native draw `topLeft`.

## Runtime gate

The stage requires all of the following before PASS:

- `initCameras`, `levelStartCamera`, `doItAllCamera`, `defaultCamera` and
  `repositionScreen` are still original Lua closures, not C replacements;
- `objects.castleCameraData[deviceModel]` and `birdCameraData[deviceModel]` are
  resolved by original `initCameras()`;
- original execution is observed in both `levelStartCamera` and `doItAllCamera`;
- native `setTopLeft` and `setWorldScale` are called repeatedly;
- camera motion is non-zero;
- at GPU snapshots, native `topLeft` agrees with Lua `screen.left/top + shake`
  within 1e-3 and native scale agrees with Lua `worldScale` within 1e-4;
- the complete Stage 22.7 gameplay, Stage 23.5 GLES scene and Stage 23.6A
  interpolation regressions remain green.

Snapshots are taken at frames 70, 125, 180, 220 and 420 in a 480x320 pbuffer,
matching the logical Android screen supplied to the original camera code.

## Still intentionally non-final

- draw order is still deterministic object-name map order;
- `GL_TRIANGLE_STRIP` remains the harness quad topology until original primitive
  topology is tied to the relevant renderer path;
- background/parallax/ground/slingshot/HUD/particles are not yet composed;
- a pbuffer is still used; Stage 24 moves the proven renderer to a real Android
  window/surface.
