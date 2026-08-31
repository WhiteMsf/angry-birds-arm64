# Contributing

Thanks for taking an interest in the reconstruction.

This project is focused on **behavioral compatibility and software
preservation**. Contributions are most useful when they are tied to observable
behavior, a reproducible mismatch, or a clearly defined build/runtime problem.

## Fidelity reports

When reporting a difference between the reconstructed ARM64 runtime and the
historical Angry Birds 1.4.2 Android release, please include as much of the
following as possible:

- exact Git commit tested;
- device model;
- Android version;
- level, menu, or game state involved;
- precise reproduction steps;
- behavior observed in the reconstructed runtime;
- expected historical behavior and how it was established;
- whether the mismatch reproduces consistently;
- screenshots, short video, logs, or other evidence when useful.

See `FIDELITY.md` for the current subsystem-level status and the highest-value
areas for further validation.

## Pull requests

Compatibility changes should be evidence-driven.

A useful pull request should explain:

1. what behavior is being changed;
2. why the current behavior is believed to be inaccurate or incomplete;
3. what evidence supports the proposed behavior;
4. how the change was tested;
5. whether it affects a narrow edge case or a broader subsystem.

Please avoid mixing unrelated cleanup, refactoring, gameplay changes, and
fidelity fixes in the same pull request when practical.

Experimental mechanics, balance changes, new content, or other non-vanilla
ideas should remain separate from the historical reconstruction.

## Build and test information

For build-system or portability changes, include the relevant host details such
as operating system, Python version, CMake/Ninja versions, Android SDK/NDK
versions, and the command that failed or succeeded.

Changes that affect the native runtime should compile successfully for
`arm64-v8a`. Real-device validation is strongly preferred for changes involving
rendering, input, audio, Android lifecycle behavior, or gameplay.

## Proprietary game data

Do **not** upload, commit, attach, or redistribute:

- original Angry Birds APKs;
- Rovio game assets;
- extracted proprietary game data;
- personal save data;
- signing keys or keystores.

The repository intentionally keeps original proprietary game data outside the
public source tree. Builders provide their own local compatible copy.

## AI-assisted contributions

AI-assisted work is welcome when it is treated as engineering input rather than
authority.

If AI materially contributed to a non-trivial change, transparency is
encouraged. More importantly, the submitted behavior should still be supported
by compilation, inspection, repeatable tests, historical-runtime comparison, or
real-device validation as appropriate.

## Before submitting

Please run, where applicable:

    git diff --check
    python build.py doctor
    python build.py native

Asset-dependent APK assembly requires the contributor's own compatible original
game data and is not required for every documentation-only or tooling-only
change.