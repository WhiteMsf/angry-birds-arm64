# Fidelity matrix

This document tracks reconstruction fidelity by subsystem rather than assigning
one project-wide accuracy percentage. A single percentage would hide important
differences between systems that have been exercised heavily and systems whose
remaining risk is concentrated in rare or device-sensitive edge cases.

The goal is **behavioral compatibility with Angry Birds 1.4.2**, not bit-exact
identity with the historical ARMv7 binary.

## Status definitions

- **Validated** - representative behavior has been exercised successfully in
  the reconstructed ARM64 build, including real-device testing where relevant,
  with no known blocking mismatch in the listed paths.
- **Functional / edge cases remain** - the subsystem is integrated and works in
  normal gameplay, but known fidelity-sensitive cases or broader validation
  remain.
- **Device-sensitive** - the subsystem is functional on tested hardware, but
  Android or hardware differences make broader device coverage especially
  useful.

These labels describe current evidence, not a claim of formal equivalence.

## Subsystem matrix

| Subsystem | Status | Current evidence | Remaining fidelity work |
| --- | --- | --- | --- |
| AArch64 runtime / ABI | **Validated** | The active runtime builds as `arm64-v8a`, runs on modern ARM64 Android hardware, and does not require the original ARMv7 native library at runtime. | No known blocking runtime/ABI gap; continue testing on additional ARM64 devices. |
| Lua 5.1 game bridge | **Validated** | Original game-side Lua drives the reconstructed runtime across the main campaign and supporting systems. | Rare scripts or less-traveled paths may still expose unmodeled native assumptions. |
| Rendering / presentation | **Functional / edge cases remain** | Gameplay, menus, sprites, effects, and the main presentation path are integrated and usable on target hardware. | Subtle rasterization, floating-point, ordering, scaling, or device-presentation differences may remain. |
| Touch / input | **Validated** | Menu interaction, aiming, launching, and normal gameplay input work on tested modern ARM64 hardware. | Broader device/input coverage and unusual gesture or lifecycle transitions remain useful to test. |
| Physics / Box2D bridge | **Functional / edge cases remain** | Main campaign physics behavior is playable through the reconstructed bridge using the historical Box2D 2.1.2 baseline plus compatibility changes. | High-restitution rubber/trampoline behavior and architecture-sensitive floating-point differences deserve targeted comparison. |
| Audio | **Validated** | Music and sound-effect paths are integrated in representative menu and gameplay flows on tested hardware. | Rare lifecycle, interruption, and device-specific audio cases can still be exercised more broadly. |
| Persistence / saves | **Validated** | Save-backed game state and progression work in representative tested flows. | Rare state-transition, corruption, or unusual historical-save edge cases are not claimed to be exhaustively characterized. |
| Progression / menus | **Functional / edge cases remain** | Main campaign progression, supporting menus, completion flows, and Golden Eggs-related paths are integrated. | Rare level-specific, menu-state, and progression edge cases remain useful targets for testing. |
| Android lifecycle / presentation | **Device-sensitive** | Launch, foreground/background lifecycle integration, surface handling, and presentation work on tested modern Android hardware. | OEM-, Android-version-, and device-specific lifecycle or surface behavior may differ from the historical environment. |
| Asset staging / APK packaging | **Validated** | The public build path has been validated on Windows and end-to-end from a clean Ubuntu 24.04 x86_64 clone, including native build, local asset staging, signing, ARM64 payload audit, installation, and device launch. | Broader host/toolchain combinations and clearer failure diagnostics remain infrastructure work rather than game-runtime fidelity work. |

## Highest-value validation areas

The most useful remaining comparisons are currently:

1. high-restitution rubber and trampoline physics;
2. subtle rendering or rasterization differences;
3. Android lifecycle and presentation behavior across additional devices;
4. rare progression, menu, Golden Egg, and level-specific paths;
5. architecture-sensitive floating-point behavior where a visible gameplay
   difference can be demonstrated.

A mismatch is most useful when it is reproducible and can be compared against
observed behavior from the historical ARMv7 release.

## Reporting a fidelity gap

Please include, where possible:

- the exact Git commit tested;
- device model and Android version;
- the level, menu, or state where the difference occurs;
- precise reproduction steps;
- observed reconstructed behavior;
- expected behavior from the historical release and how it was established;
- screenshots, short video, logs, or other evidence when useful;
- whether the difference reproduces consistently.

Do not upload or attach proprietary Angry Birds APKs or game assets to this
repository. See `CONTRIBUTING.md` for contribution guidance and `ROADMAP.md` for
planned follow-up work.