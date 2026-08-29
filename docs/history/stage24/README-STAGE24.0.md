# Stage 24.0 — live Android Surface + real touch smoke

> v0.26.3 physics correction: the original ARMv7 `GameLua` constructor loads `b2Vec2(0.0f, 20.0f)` before constructing `b2World`; Stage 24 now uses the recovered `(0,20)` gravity. The v0.26.2 Unicode-path packaging fix and v0.26.1 `<android/window.h>` fix remain included.

This is the first build that stops using an EGL pbuffer as the primary output.
It packages the reconstructed ARM64 engine as `libangryarm64.so`, loads it via
`android.app.NativeActivity`, creates a real `EGL_WINDOW_BIT` surface from the
activity's `ANativeWindow`, and swaps gameplay frames directly to the phone.

The game logic remains the same chain already proven by Stage 23.6C:

- patched Angry-compatible Lua 5.1.5;
- original 1.4.2 gameplay Lua / Level1;
- reconstructed Box2D bridge and fixed 30 Hz physics schedule;
- two-slot RenderObjectData interpolation;
- original Lua camera;
- original KA3D Hashtable iteration / ARMv7 drawGame pass predicates;
- original RGBA4444 block/bird atlases through GLES1 fixed function.

Stage 24.0 also replaces the **synthetic** LBUTTON drag script with Android
`MotionEvent` input. The native-app-glue callback stores DOWN/MOVE/UP state;
the game thread maps the physical window coordinate into the logical 480x320
camera viewport and publishes only the original `cursor`, `touchcount`,
`keyPressed.LBUTTON`, `keyHold.LBUTTON`, and `keyReleased.LBUTTON` surface.
Original `updateGame()` still performs selection, rubber-band math, launch and
bird-specialty routing.

This is a smoke boundary, not the final presentation layer. It intentionally
still omits background/parallax/theme ground, slingshot resource sprites/HUD,
audio, menus, save/progression and complete Android lifecycle fidelity. The
first-run tutorial queue also remains dismissed because its popup renderer has
not been reconstructed yet.

## Run

From Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
```

The script locally builds and debug-signs an APK **using the user's own extracted
1.4.2 assets**. Those assets are not included in this bootstrap archive.
It installs and launches the APK over ADB.

After launch, wait for the original level-start camera sweep. Touch the visible
Red bird, drag backward/downward and release. The exact sling visuals are not
rendered yet, but the real original input path should move and launch the body.

After playing, collect logs with:

```powershell
.\pull-stage24-live-log.ps1
```

Important logcat markers:

```text
Stage24 NativeActivity entered: ARM64 live Surface + real touch
LIVE EGL Surface ready: ... logical=480x320
GLES1 ready: ...
Recovered GL state active: ...
LIVE frame=...
TOUCH DOWN ... logical=(...)
LIVE state ... selected=yes ...
TOUCH UP ... logical=(...)
LIVE state ... flyingBird=RedBird_... birdsShot=...
```

## Fidelity boundary

Stage 24.0 proves a real Android window and direct touch routing. It does **not**
claim final modern-display scaling, back/pause/resume behavior, GUI hitboxes,
slingshot presentation resources, particles, audio, menus or package parity.
Those remain explicit subsequent gates.

The APK is deliberately marked `debuggable=true` for this reconstruction smoke so
`pull-stage24-live-log.ps1` can retrieve the app-private native stdout/stderr via
`run-as`. This is not intended as a release packaging choice.


## v0.26.5 / Stage 24.1 diagnostic continuation

The live touch run proved Level1 completion but exposed a later Lua failure after the original game switched into post-level UI/menu flow. v0.26.5 traces that transition and quarantines only post-completion faults so the exact missing UI boundary can be recovered without killing the live Surface. It also rejects letterbox-start touches while preserving drags that begin inside the game viewport.

## v0.26.6 / Stage 24.3 update

The live completion path now restores the clean-profile `highscores` root and
probes the untouched original `initializeMenu()` closure under traced error
handling. This is a state/bootstrap recovery step; the result page is not yet
visually rendered by the Stage 24 custom GLES1 renderer.


## v0.26.7 / Stage 24.4 update

v0.26.6 proved that the clean-profile `highscores` root is now correct: the
original `updateLevelEnding()` populated one level entry before the next fault.
The original `initializeMenu()` probe then exposed the next platform boundary:
`createMenuPages()` PC 496 concatenates the externally supplied `levelPath`.

Stage 24.4 publishes the logical original-resource root `data/levels`, yielding
paths such as `data/levels/pack1/`.  This string is derived from the untouched
APK asset hierarchy plus the recovered Lua bytecode concatenation; the exact
ARMv7 native literal remains a separate provenance item.  No other path globals
are guessed in this release.


## v0.26.8 / Stage 24.5 update

Stage 24.5 restores the menu SPRT metadata surface needed by the original `createMenuPages()`.
The build stages the original local `LEVELSELECTION_SHEET_1.dat`, `BUTTONS_SHEET_1.dat`, and
`POPUPS_SHEET_1.dat`, loads them into `SpriteDB`, and requires
`LS_LEVEL_BG_NORMAL_OPEN_1` to resolve before menu bootstrap. This is metadata/bootstrap only;
visual result/menu rendering remains a later step.



## v0.26.10 / Stage 24.7 update

The v0.26.9 preflight assumption that every `getSpriteBounds` name must have a
SPRT owner was wrong. A full local asset-tree probe found `SETTINGS_BG` only in
`gamelogic.lua`, with no file or DAT owner. Static ARMv7 recovery explains why
that is legal: `LuaResources::getSpriteBounds` calls `Resources::getSpriteWidth`
and `getSpriteHeight`, and both return `0` when the requested sheet/sprite is
absent. The original Lua binding still pushes two numbers. `getSpritePivotX/Y`
have the same zero-on-miss behavior.

Stage 24.7 therefore:

- removes the false `SETTINGS_BG` asset-owner build gate;
- changes the reconstructed `res.getSpriteBounds` missing-sprite path from a
  Lua exception to `(0,0)`, matching ARMv7;
- changes `res.getSpritePivot` missing-sprite behavior to `(0,0)`, also matching ARMv7;
- removes the fatal startup requirement that `SETTINGS_BG` exist in the loaded
  SPRT database;
- keeps the Stage23 object-sheet audit scoped to the two Level1 object sheets,
  so menu metadata cannot kill the already-proven live gameplay path.

This does **not** claim that `SETTINGS_BG` is a drawable sprite. It records the
opposite: in this asset dump it has no SPRT owner, and the original native
resource API is explicitly tolerant of that case.

## v0.26.9 / Stage 24.6 update

Fixes the v0.26.8 black-screen regression caused by the historical Stage23.0 total-sheet-count gate, and restores the broader original 864x480 MENU/OTHER SPRT metadata surface needed by createMenuPages().

## v0.26.11 / Stage 24.8 update

The v0.26.10 trace proved the next missing field at `createMenuPages` PC 2635
is `res.getString`. Stage 24.8 stages the untouched local
`localization/TEXTS_BASIC.dat`, parses the recovered KA3D/TEXT
LDAT/LIDS/TXGP structure at runtime, and exposes `res.getString` with the
Android configuration language. Missing localization IDs fall back to the ID
string, matching recovered `TextGroup::get` behavior.

The menu bootstrap remains diagnostic/non-fatal; visual menu/result rendering
is still outside this stage.

## v0.26.12 / Stage 24.9 update

The v0.26.11 live completion trace proves that original menu creation now
passes, then `updateLevelEnding()` reaches `setFont(fontBasic)` and calls the
missing native field `res.useFont`. Stage 24.9 replays the untouched original
`loadFonts()` closure before `initialize()`, stages the local 480x320 font DATs,
and restores diagnostic `createBitmapFont` registration plus the recovered
non-throwing `useFont` select/default-fallback semantics. The visible bitmap
font renderer and result/menu drawing remain intentionally deferred.


### v0.26.13 / Stage 24.10 — `starTable` namespace recovery
The v0.26.12 trace passed `res.useFont(FONT_BASIC)` and exposed `starTable` as the next missing native bootstrap object. Stage 24.10 mirrors the recovered ARMv7 non-empty `GameLua::loadLuaFile` path: a fresh Lua table is used as the chunk function environment, then installed under the requested name. Local `starLimits.lua` therefore populates `starTable` without hard-coded score thresholds. Visual result rendering remains open.

### v0.26.15.2 / Stage 24.12.1

First live Stage 24.12 run exposed `imagePath == nil` in original
`releaseImages()` reached through `initializeMenu -> createMenuPages ->
prepareMenuPage`.  Restore the layout-derived logical root `data/images` and
retest before touching the later font-current-state failure.

### v0.26.15.3 / Stage 24.12.2

The v0.26.15.2 live trace advanced `releaseImages()` past the recovered
`imagePath` concatenation and stopped one instruction later at missing native
`res.releaseSpriteSheet`. Register the original void release surface only. In
the current harness the corresponding native Resources SpriteSheet cache is
empty, so release is non-fatal and traced; the independent SPRT metadata DB is
not destroyed. Do not pre-register the next resource API.

## Stage 24.12.7 / v0.26.15.8
Restores the original tutorial composprite geometry boundary exposed at `prepareMenuPage pc=9178`: packages/parses `TUTORIALS_composprites.dat` and implements four-value `res.getCompoSpriteBounds` from real child sprite offsets + SPRT dimensions/pivots.
