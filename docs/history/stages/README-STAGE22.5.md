# Stage 22.5 — pig fidelity audit

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage22-5-pig-fidelity-audit-android-arm64.ps1
```

This test deliberately does not shoot.

Expected successful instrumentation end:

```text
[pig-audit-summary] ...
[pig-audit-warning] ...   # possible finding, NOT a harness failure
[angry-stage22.5] ... ZERO SYNTHETIC SLING INPUT ...
[angry-stage22.5] PASS

Stage 22.5 pig fidelity audit ARM64 PASS.
```

The script opens the text report and an idle visual replay, and leaves a CSV
with every pig contact for detailed comparison.
