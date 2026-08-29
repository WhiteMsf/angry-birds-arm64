# Stage 22 — visual debug replay

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage22-visual-replay-android-arm64.ps1
```

Expected end:

```text
[stage22-render] replay finalized: ... status=OK
[angry-stage21] PASS
[angry-stage22] DEBUG GEOMETRY REPLAY RECORDED ...
[angry-stage22] PASS

Stage 22 visual debug renderer ARM64 PASS.
Replay: ...\stage22-output\angry-stage22-level1-replay.html
```

The HTML is completely self-contained and opens locally in a browser.

Stage 23 can start replacing debug geometry with the original sprite/PVR
rendering pipeline while keeping this replay as a reference.
