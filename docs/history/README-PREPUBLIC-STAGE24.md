# Angry Birds ARM64 — v0.26.164 / Stage24.49.1

**In-game reconstruction credit.** The original Rovio About/Credits page remains the owner of its layout, scrolling, font and rendering. The ARM64 layer appends one project-owned line — `ARM64 reconstruction by WhiteMsf` — to the end of `TEXT_CREDITS` in memory, without modifying the original localization asset or replacing the original credits screen. Public Release metadata remains `1.0.0`; only the Audit envelope advances to `0.26.164 / 26164`. See `V0.26.164-STAGE24.49.1-IN-GAME-RECONSTRUCTION-CREDIT-NOTES.md`.

# Angry Birds ARM64 — v0.26.163 / Stage24.49.0C

**Release-branding version-contract hotfix.** The Stage24.48.1 preflight no longer hard-codes the old v0.26.160 audit metadata. It derives and cross-checks `versionName`/`versionCode` from the current manifest and the leading release heading, while Stage24.49.0C runs that nested branding contract before prompting for the release key password or building either envelope. Runtime and CMake bytes remain frozen. See `V0.26.163-STAGE24.49.0C-BRANDING-VERSION-CONTRACT-HOTFIX-NOTES.md`.

# Angry Birds ARM64 — v0.26.162 / Stage24.49.0B

Release-manifest staging hotfix for final 1.0 acceptance. Runtime/physics/lifecycle remain frozen; only release tooling changed. See `V0.26.162-STAGE24.49.0B-RELEASE-MANIFEST-STAGING-HOTFIX-NOTES.md`.

# Angry Birds ARM64 — v0.26.161 / Stage24.49.0A

**Final release tooling timestamp hotfix.** A timezone-naive ZIP extracted on Windows can stamp `CMakeLists.txt` ahead of the local clock, making Ninja loop forever on `Re-running CMake`. Stage24.49.0A normalizes only the root CMake input **mtime** to a safe local value immediately before configuring. File contents and the frozen SHA-256 baseline are unchanged. Existing permanent release keys are reused; rerunning `test-angry-birds-1.0.0-final.ps1` does not regenerate the key.

# Angry Birds ARM64 — v0.26.160 / Stage24.49.0

**1.0 release engineering is now staged.** `stage24_live_surface.cpp` and the runtime `CMakeLists.txt` remain frozen on the v0.26.157 homologated engine; Stage24.49.0 changes only packaging/signing/release tooling. Run `test-angry-birds-1.0.0-final.ps1` to create/reuse the permanent release key, build the audited and non-debuggable envelopes, prove identical native payloads, enforce 16 KB ELF alignment, prepare `dist/1.0.0`, and perform the final historical-profile + clean-profile acceptance. See `V0.26.160-STAGE24.49.0-1.0-RELEASE-ENGINEERING-NOTES.md`, `RELEASE-SECURITY.md`, and `UPLOAD-LAYOUT.md`.

Stage24.48.1 performs packaging-only release branding cleanup on top of the proven v0.26.157 engine baseline. The Android application label is now exactly `Angry Birds`, the development version metadata is synchronized to `0.26.159`, and the manifest references `@drawable/app_icon`.

The launcher icon itself is **not** distributed in this source archive. During the local Windows build, `stage24481_find_original_launcher_icon.py` locates the user's own original launcher PNG from the extracted `angry-re` resource tree or an Angry/Rovio APK in Downloads, stages it as `res/drawable/app_icon.png`, and records its source path, dimensions and SHA-256. `aapt dump badging` then fails closed unless the finished APK exposes label `Angry Birds` and the launcher icon resource.

Runtime code and physics remain frozen: `stage24_live_surface.cpp` and `CMakeLists.txt` are still SHA-256-identical to the Stage24.47.6B / v0.26.157 baseline. Package identity, debuggable flag, final `1.0.0` version, distribution signing and final APK filename remain separate release-envelope work.

# Angry Birds ARM64 reconstruction — v0.26.158 / Stage 24.48.0

Stage24.48.0 starts the 1.0 release-candidate homologation without changing the proven v0.26.157 runtime. The live engine source, CMake runtime policy and Android manifest are SHA-256 frozen against the 47.6B baseline; this stage adds only release auditing/test tooling and documentation.

The first RC pass uses the real existing profile and does **not** clear `settings.lua` or `highscores.lua`. It checks integrated cold boot/menu/gameplay/pause/audio/special-bird/rubber/Golden-Egg/result/lifecycle behavior, then scans the pulled logs for fatal Lua/GPU/native/lifecycle failures. Visual equivalence remains a human/original-footage oracle rather than a synthetic success flag.

The release-envelope audit currently records six known non-gameplay debts for the eventual 1.0 package: `android:debuggable=true`, stale `versionName`, Stage24 application label, Stage24 package identity decision, debug-key signing, and debug APK filename. These are intentionally **not** changed in 48.0 so packaging cleanup cannot be confused with a gameplay regression.

The post-package audit fails closed unless the APK contains exactly `lib/arm64-v8a/libangryarm64.so` and no ARMv7 runtime fallback. Original assets remain sourced only from the user's local extracted 1.4.2 tree during the Windows build.

# Angry Birds ARM64 reconstruction — v0.26.156 / Stage 24.47.6

Stage24.47.6A fixes Android Recents/background lifecycle ownership. `APP_CMD_TERM_WINDOW` no longer destroys the game engine: Lua, Box2D, audio state and the EGL context remain alive while only the temporary Android window surface is released. On `APP_CMD_INIT_WINDOW`, the engine thread creates a new `EGLSurface` on the existing context and continues the exact same game state, so a normal multitasking round-trip must not replay the splash or return to the main menu. `APP_CMD_DESTROY` remains the real engine teardown boundary.
The complete chapter campaign remains live-closed (`gameCompleted=true`, 202 completed chapter levels), and Golden Eggs continue loading through the restored original `data/` resource root.

Stage24.47.4 closed the remaining obvious warm-start/integration-clamp explanations for the long-standing rubber/trampoline mismatch: the recovered 30 Hz step, distance-joint spring parameters, restitution=5.5 contact path, manifold warm-start matching and Box2D linear/angular caps all remain oracle-compatible.

Stage24.47.5 now tests an architecture-level numerical difference instead of tuning a recovered constant. The original ARMv7 physics paths use separate scalar float helper operations (`__mulsf3`, `__aeabi_fadd`, `__subsf3`, etc.), while modern AArch64 Clang may contract multiply+add into FMADD/FMSUB. `box2d212` and the live physics bridge therefore compile with `-ffp-contract=off`, and a post-build disassembly audit fails closed if fused operations survive in relevant physics functions.

The runtime remains observe-only and also records generic Box2D world joint-list order once per rubber level while resetting only diagnostic budgets between levels. The focused A/B remains visual Golden Egg #2 (`LevelGE_3`) versus Danger Above 8-3 (`LevelP3_306`). No restitution, frequency, damping, joint length, body velocity, contact impulse, Lua state, score or save state is directly mutated by Stage24.47.5.

The complete chapter campaign remains live-closed: pack11 finished 15/15, untouched Lua persisted `theme11Completed=true` and `gameCompleted=true`, and the stock final flow reached `gameFinishedLP4 -> levelComplete -> theme11Complete`.

Stage 24.47.2 follows the long-standing rubber "molenga" mismatch into the reconstructed type=1 distance-joint network. It acquires the untouched ARMv7 `b2DistanceJoint` constructor/solver bodies beside the pinned Box2D 2.1.2 source and adds an observe-only runtime witness for rest/current length, strain, anchor velocity and reaction force around rubber impacts. No restitution, frequency, damping, joint length or solver state is changed.

Stage 24.47.1 remains as the contact-level rubber audit; Stage 24.47.0A fixes the original Golden Eggs data-root resource search; Stage 24.47.0 enters the Golden Eggs branch while keeping all unlock/completion/star state Lua/save-owned.

## v0.26.157 / Stage24.47.6B
Tooling-only llvm-objdump CLI/fallback hotfix for the Android lifecycle JNI acquisition gate. Runtime lifecycle code is unchanged from v0.26.155.
