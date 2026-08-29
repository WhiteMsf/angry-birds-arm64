# Angry ARM64 bootstrap v0.7 — Stage 6

Stage 5 proved the reconstructed GameLua physics API drives real Box2D 2.1.2 on
Android ARM64.

Stage 6 materializes the **actual original Level1**.

It reads the original `Level1.lua`, original `blocks.lua`, and original KA3D
sprite-sheet metadata from the user's extracted APK. No Angry Birds game assets
are redistributed inside this ZIP.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage6-level1-android-arm64.ps1
```

The script expects the extracted APK data at:

```text
%USERPROFILE%\Downloads\angry-re\assets\data
```

The decisive final lines should be:

```text
[angry-stage6] LEVEL1 ORIGINAL DATA -> ORIGINAL createObject() -> REAL GAMELUA PHYSICS -> BOX2D 2.1.2
[angry-stage6] 21 LEVEL1 BODIES MATERIALIZED AND STEPPED ON ANDROID ARM64
[angry-stage6] PASS
```
