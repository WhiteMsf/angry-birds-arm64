# Stage 20 — two consecutive original input-driven shots

Run on the connected ARM64 Android device:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage20-two-shots-android-arm64.ps1
```

Most useful output:

```text
[stage20-shot] #1 ...
[stage20-lifecycle] SHOT #1 COMPLETE ...
[stage20-shot] #2 ...
[stage20-lifecycle] AFTER TWO SHOTS ...
[stage20-shot] #1 summary ...
[stage20-shot] #2 summary ...
[angry-stage20] PASS
```

A runtime failure on the second PRESS/DRAG/RELEASE is useful evidence:
Stage 20 deliberately does not manufacture additional lifecycle state.
