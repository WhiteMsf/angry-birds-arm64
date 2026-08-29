# Roadmap

This roadmap tracks work after the main ARM64 reconstruction reached its
release-candidate state. Detailed historical Stage24 development notes live
under `docs/history/`.

## Completed

- Reconstruct the native Android runtime for AArch64 / `arm64-v8a`.
- Restore the main Lua/native gameplay bridge.
- Restore menu, rendering, input, physics, audio, saves, progression, and
  Android lifecycle integration.
- Complete the main chapter-campaign reconstruction path.
- Restore Golden Eggs resource loading and related progression paths.
- Replace the historical monolithic build script with `build.py`,
  CMake, and Ninja.
- Add incremental and clean native builds.
- Add local original-asset staging.
- Add APK packaging, signing, branding, and ARM64 payload verification.
- Separate historical Stage0-Stage23 material from the active runtime build.
- Remove proprietary original game assets and private signing material from
  the public source tree.
- Preserve required Lua and Box2D copyright/license notices.
- Quarantine historical KA3D source material from the public repository.
- Prepare the repository for a clean public Git history.

## Near term

- Perform final public-source documentation review.
- Run a final full `python build.py apk` acceptance after repository cleanup.
- Re-test installation and representative gameplay on modern ARM64 Android.
- Improve build diagnostics and error messages where setup failures remain
  unnecessarily cryptic.
- Make original-game input selection more explicit and less dependent on
  fallback discovery paths.

## Fidelity work

The project is usable as a reconstruction, but additional fidelity work can
continue independently of release engineering.

Areas worth continued validation include:

- high-restitution rubber/trampoline behavior;
- architecture-sensitive floating-point differences;
- subtle rendering and rasterization differences;
- device-specific Android lifecycle and presentation behavior;
- rare progression, menu, or level-specific edge cases.

Changes in these areas should remain evidence-driven rather than becoming
gameplay redesigns.

## Build and portability

Future infrastructure work may include:

- broader host testing across Windows and Linux;
- automated native-build checks that require no proprietary assets;
- clearer supported Python/CMake/Ninja version documentation;
- further reduction of legacy Stage24-specific names in current tooling.

## Out of scope for the vanilla reconstruction

The main repository should remain focused on reproducing the historical game.

Experimental gameplay changes, new mechanics, balance changes, or other
non-vanilla ideas should live separately so that compatibility work and game
modification do not become mixed together.
