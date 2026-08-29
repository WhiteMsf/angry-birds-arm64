# Angry Birds Classic 1.4.2 ARM64 — fidelity roadmap

## Final target

A native `arm64-v8a` port of the Android release that behaves like the original
Angry Birds Classic 1.4.2 build, using the original game data/assets and a
semantically reconstructed native engine. The ARMv7 game library must not be
required at runtime and the end product must not depend on ARM emulation.

"Faithful" means more than reaching a win state. The target includes original
Lua behavior, physics constants/order, collision/damage/destruction, object
transforms, sprite selection, pivots/UVs/layering, camera behavior, animations,
particles, input routing, audio events, menus/UI, progression/save behavior and
Android lifecycle/display behavior. Where obsolete external services existed,
their exact historical dependency should be documented rather than silently
changing gameplay.

## Current proven chain

1. modern 64-bit KA3D/Lua bootstrap;
2. Angry-compatible Lua 5.1 chunk ABI;
3. original script loader and initialization;
4. reconstructed GameLua semantic bindings;
5. Box2D 2.1.2-era native world/body bridge;
6. original update/updateGame execution order;
7. native fixed-step/contact/damage/destruction pipeline;
8. original slingshot/input state machine;
9. multiple consecutive birds and complete Level1 terminal lifecycle;
10. debug visual replay from real Box2D bodies + original Lua state;
11. zero-input pig fidelity audit;
12. recovered ARMv7 polygon skin `0.1f` strongly confirmed by A/B runtime test.

## Completed physics gate — Stage 22.7

Promote `shape.m_radius = 0.1f` from the Stage 22.6 experiment into the normal
reconstructed `createBox()` path, then run an idle soak through frame 120 and
play the entire Level1. Required result: zero pre-input pig damage, while the
existing launch/contact/damage/destruction/lifecycle assertions still pass.

Stage 22.7 passed on-device: zero pre-input pig damage through frame 120 and the full original Level1 input/damage/destruction/terminal lifecycle remained intact. This closes the known polygon-skin regression before renderer reconstruction.
Stage 22.7 was originally run with provisional gravity `(0,10)`. After the first live APK comparison, the ARMv7 `GameLua` constructor was re-audited and independently proved to construct `b2World` with gravity `(0,20)` (literal pair `0x00000000`, `0x41a00000`). Stage 24.0 v0.26.3 promotes the recovered gravity. The old Stage 22.7 terminal-frame corpus is therefore historical/provisional and must not be used as a final trajectory oracle. Remaining Rovio-fork behavior stays on the evidence backlog.

## Stage 23 family — original sprite/PVR renderer reconstruction

### 23.0 — sprite/texture manifest audit (closed)
- parse the original SPRT metadata completely, including texture names/indexing;
- map every Level1 object's Lua sprite to atlas texture, rectangle and pivot;
- inventory every renderer-facing binding still stubbed (`setSprite`,
  `setTexture`, `drawTexturedRect`, visibility/layer helpers, etc.);
- emit a deterministic manifest so metadata can be compared to ARMv7 behavior.

### 23.1 — PVR pixel-format/payload proof (closed)
- identify the exact original PVR container/format variants used by 1.4.2;
- load the untouched original texture assets on ARM64;
- validate width/height/mipmap/alpha/orientation and texture-to-SPRT matching;
- determine the exact historical GLES path from the ARMv7 binary/imports rather
  than assuming GLES1 vs GLES2.

### 23.2 — sprite replay (closed)
- replace Stage 22 debug shapes with original sprites in the offline replay;
- reproduce sprite pivots, rotations, scale, flips and atlas UVs;
- preserve the real Box2D/Lua transforms underneath;
- retain debug-geometry toggle as a registration/fidelity overlay.

### 23.3 — real GLES1 single-sprite path (closed)
- create an ARM64 EGL pbuffer and GLES1 context on the real device;
- upload untouched original RGBA4444 PVR bytes;
- render `BIRD_RED` with fixed-function vertex/texcoord arrays;
- require GPU readback to match the source crop exactly.

### 23.4 — ARMv7 fixed-function state recovery (closed)
- recover texture filtering, wrap, upload alignment, blend templates, matrix
  submission and client-array callsites from the original ARMv7 binary;
- keep raw disassembly context as the authority instead of choosing modern
  defaults by appearance.

### 23.5 — full Level1 multi-sprite GPU scene (closed)
- render the real Level1 body transforms through GLES1 using both original
  RGBA4444 atlases and the recovered fixed-function state contract;
- validate rects, pivots, rotations and dynamic sprite replacement at multiple
  gameplay frames;
- keep debug camera and deterministic name-order drawing explicitly marked as
  temporary audit boundaries.

Stage 23.5 passed on-device: the GPU snapshots progressed from 20 to 19 to 18
drawable Level1 objects while damage-sprite changes progressed from 0 to 1 to 3.

### 23.6A — RenderObjectData interpolation (closed)
- reconstruct the native two-slot `(x,y,angle)` history recovered from ARMv7;
- mirror awake-body capture, catch-up history gating and setter force-publish behavior;
- publish `alpha = accumulator/(1/30)` interpolated transforms to Lua and GLES;
- retain the full Level1 gameplay + GPU regression and require positive runtime
  evidence that interpolation is actually active.

Stage 23.6A passed on-device with alternating 60 Hz / 30 Hz interpolation phases
and measurable raw-Box2D -> published-render transform deltas.

### 23.6B — original camera (passed)
- run original `initCameras`, `levelStartCamera`, `doItAllCamera`, `defaultCamera`
  and `repositionScreen` without native replacement;
- reconstruct only ARMv7 `setTopLeft` / `setWorldScale` publication calls;
- drive both GLES world->screen and touch physics->screen inverse from that state;
- validate camera transitions and Lua/native camera equality numerically.

### 23.6C — render order / object presentation (closed for Level1 object passes)
- recover original draw order/layers, visibility, alpha/color and sprite replacement;
- restore slingshot bands, trails, damage sprites, animations and particles in
  small evidence-backed sub-stages rather than one visual approximation pass.

## Stage 24 family — live Android graphics (live Surface + Level1 loop proven)

- create the real Android EGL/GLES surface/context using the API proven from the
  original binary;
- render Stage 23 frames in real time on-device rather than to HTML;
- recover viewport/aspect/scaling rules for the 864x480 asset family and modern
  displays;
- preserve frame/update ordering relative to physics and Lua;
- add screenshot capture so ARMv7 and ARM64 frames can be compared.

## Stage 25 family — Android input and lifecycle (real single-touch path + basic Surface lifecycle proven)

- replace harness LBUTTON/cursor injection with real touch events;
- reproduce screen-to-world coordinate conversion and drag/tap semantics;
- recover pause/resume/focus/back-button/orientation lifecycle behavior;
- rebuild the native/Java/JNI boundary used by the original Android package.

## Stage 26 family — audio

- inventory original sound/music assets and the Lua/native audio bindings;
- reconstruct playback, channel/mixer rules, volume, looping and event timing;
- verify launch, collision, destruction, bird, pig, UI and music triggers against
  the ARMv7 build.

## Stage 27 family — full game-state/UI coverage

- splash/loading/main menu/episode and level selection;
- HUD, pause, restart, level-complete/failed screens, score/stars;
- every object/material/TNT mechanic and every bird ability present in 1.4.2;
- representative levels from every content pack, not only Level1;
- animations, particles, camera transitions and scripted special cases.

## Stage 28 family — persistence and package behavior

- original save/progression/settings semantics;
- unlock/star/high-score persistence and reset behavior;
- language/resource selection and platform settings used by the release;
- document obsolete network/ad/store hooks separately from the gameplay core.

## Stage 29 — real ARM64 APK

- package the reconstructed engine as `arm64-v8a` native code;
- include the original data/assets through the Android app packaging path;
- reproduce manifest/activity/resource/native-library startup behavior;
- boot from launcher into the game with no ADB harness and no ARMv7 runtime code.

## Stage 30 — differential fidelity campaign

Use the original ARMv7 build as the oracle wherever possible:

- deterministic input traces replayed on both builds;
- per-frame body/velocity/contact/damage/state traces;
- screenshot/pixel or feature-registration comparisons;
- sprite/animation/camera event timelines;
- audio event timelines;
- menu/progression/save path comparisons;
- long-run tests over many levels and repeated launches.

Any mismatch becomes a small numbered audit stage instead of being hidden by a
"close enough" workaround.

## 1.0 acceptance rule

The project is done when the ARM64 APK is usable as the original game, not merely
when Level1 works: original assets, original scripted behavior, independently
reconstructed native implementation, no ARMv7 emulation dependency, and no known
material gameplay/render/audio/UI divergence left unexplained.


### Stage 23.1 — PVR/PVRTC payload audit
Decode and validate the exact original PVR texture containers before GLES upload. Stage 23.1 recovered the Level1 atlases as uncompressed legacy GL_RGBA_4444 payloads, so their faithful upload path uses glTexImage2D rather than PVRTC decompression.

## Current renderer frontier (v0.25.4)

- Stage 23.0: exact Level1 `sprite -> sheet -> texture -> rect -> pivot` mapping proven.
- Stage 23.1: original Level1 PVRs proven as uncompressed PVR v2 RGBA4444, one base level.
- Stage 23.2: original sprite pixels replay correctly over the reconstructed ARM64 gameplay; direct `.dat` Y interpretation visually confirmed.
- Stage 23.3: real ARM64 EGL/GLES1 pbuffer upload passed with exact `BIRD_RED` GPU readback (`mismatchPixels=0`, `maxChannelError=0`).
- Stage 23.4: original ARMv7 GLES1 callsites recovered. Confirmed linear filtering, clamp-to-edge, unpack alignment 1 on blit/upload, fixed-function matrices/client arrays and original blend templates.
- Stage 23.5: first complete Level1 multi-sprite GPU snapshots using the recovered state contract.
- Stage 23.6A: original RenderObjectData fixed-step interpolation passed on-device.
- Stage 23.6B: original Lua camera passed end-to-end with zero native/Lua top-left and scale consistency error in captured frames.
- Current: Stage 23.6C restores KA3D Hashtable object iteration and the recovered ARMv7 drawGame pass predicates. v0.25.4 corrects the runtime evidence gate to preserve legal multi-pass redraws (the original pass2 does not exclude pass0 objects); next is a real Android Surface + live touch loop.


### Stage 24.1 — post-completion/UI fault trace (v0.26.5)
The first gravity-corrected live run completed Level1 through real touch and then later exited with Lua `rc=15` while the user interacted after completion. v0.26.5 records the active original `update` closure and exact post-completion Lua fault in logcat, keeps the live renderer alive after that proven-complete boundary, and fixes letterbox-start input leakage. This stage intentionally does not invent a result screen; the trace determines the first concrete Stage 27 UI dependency to reconstruct.

### Stage 24.3 — persistence/menu bootstrap

v0.26.6 restores the clean-profile highscores root and probes the original
initializeMenu/createMenuPages path after live Level1 completion exposed the
missing persistence boundary. Result-page rendering remains the next visual
boundary.


### Stage 24.4 — platform levelPath bridge

v0.26.7 advances the original menu bootstrap by restoring the missing
platform-supplied `levelPath` global as `data/levels`. v0.26.6 runtime evidence
showed `highscores` successfully becoming populated by original
`updateLevelEnding()`; its menu bootstrap failed earlier at `createMenuPages`
PC 496 only because `levelPath` was nil. The bridge is intentionally narrow:
`imagePath`, `audioPath`, `fontPath`, and `localizationPath` are not guessed.
The next runtime trace decides the next reconstruction boundary.


### Stage 24.5 — original menu SPRT metadata

v0.26.8 restores the three sprite metadata sheets referenced directly by `createMenuPages()`
(`LEVELSELECTION_SHEET_1`, `BUTTONS_SHEET_1`, `POPUPS_SHEET_1`). Goal: let the original
`initializeMenu()` construct `levelComplete`/`levelFailed` far enough to expose the next real
platform/resource boundary. Visual menu rendering is intentionally still out of scope here.


### Stage 24.6 — menu metadata surface + Stage23 auditor scope fix

v0.26.9 scopes the Stage23 object-sheet proof to INGAME_BLOCKS_1/INGAME_BIRDS_1 and adds the original MENU/OTHER metadata required by createMenuPages().

### Stage 24.7 — recovered missing-sprite resource semantics

v0.26.10 corrects `res.getSpriteBounds` / `res.getSpritePivot` to match the
original ARMv7 resource layer: missing sprites return zeros rather than raising
Lua errors. This was recovered from `LuaResources::getSpriteBounds` plus
`Resources::getSpriteWidth/Height` and `getSpritePivotX/Y`. It unblocks the
original `createMenuPages()` path at the script-only `SETTINGS_BG` lookup while
keeping menu bootstrap failure non-fatal to the Level1 Surface/gameplay smoke.


### Stage 24.8 — TEXTS_BASIC / original `res.getString` bridge

v0.26.10 advanced `createMenuPages` to PC 2635, recovered exactly as
`res.getString("TEXTS_BASIC", "TEXT_SCORE_SPRITE")`. v0.26.11 stages the
user-local original `TEXTS_BASIC.dat`, parses its recovered KA3D/TEXT v1
LDAT/LIDS/TXGP structure on ARM64, and restores the `res.getString` binding.
Menu-bootstrap failures remain non-fatal until the complete original result
page state exists.

### Stage 24.9 — original `loadFonts` / `res.useFont` boundary

The v0.26.11 device run completed Level1 with the original result pages present
(`levelComplete` 36 items / `levelFailed` 24 items), then reached the original
post-level `setFont(fontBasic)` path and failed only because `res.useFont` was
missing. v0.26.12 restores the untouched Lua `loadFonts()` startup slice,
stages the original local 480x320 font DATs, exposes `res.createBitmapFont`,
and implements the recovered non-throwing `Resources::useFont` selection /
default-fallback semantics. This is still a state-machine/resource bridge:
glyph rasterization and visible result/menu text are deliberately not claimed.


### v0.26.13 / Stage 24.10 — `starTable` namespace recovery
The v0.26.12 trace passed `res.useFont(FONT_BASIC)` and exposed `starTable` as the next missing native bootstrap object. Stage 24.10 mirrors the recovered ARMv7 non-empty `GameLua::loadLuaFile` path: a fresh Lua table is used as the chunk function environment, then installed under the requested name. Local `starLimits.lua` therefore populates `starTable` without hard-coded score thresholds. Visual result rendering remains open.

- Stage 24.11: original level-selection context bridge for direct Level1 smoke boot; fixes the state skipped by bypassing `gotoLevelSelection()` / `handleGameModeChange()`.


## Stage 24.48.0 — 1.0 release-candidate homologation

- freeze the v0.26.157 runtime as the first RC baseline;
- run an integrated real-profile regression without clearing the historical save;
- prove the packaged APK is arm64-only with no ARMv7 runtime fallback;
- inventory release-envelope debt separately from gameplay fidelity;
- next: clean-profile backup/restore regression, then final 1.0 packaging cleanup.


## Stage 24.48.1 — release branding cleanup

- set the installed app label exactly to `Angry Birds`;
- recover the launcher icon only from the user's local original APK/extracted resources at build time;
- package the generated `res/drawable/app_icon.png` through `aapt -S`;
- fail closed on post-package label/icon badging mismatch;
- keep the engine/CMake baseline identical to v0.26.157;
- next: clean-profile backup/restore regression, then final release-envelope/signing cleanup.
