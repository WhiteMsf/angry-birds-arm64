# Stage 22.6 — polygon-skin A/B fidelity audit

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-stage22-6-polygon-skin-audit-android-arm64.ps1
```

The script builds once and performs two zero-input Level1 runs:

```text
upstream-default
recovered-armv7-0.1
```

Outputs:

```text
stage22-6-output\
  polygon-skin-comparison.txt
  upstream-default\
    pig-audit-report.txt
    pig-audit.csv
    level1-idle.html
  recovered-armv7-0.1\
    pig-audit-report.txt
    pig-audit.csv
    level1-idle.html
```

The comparison file is the first thing to inspect.

This stage changes only the polygon shape skin radius in the candidate run.
It does not alter pig health, defence, damage math, gravity, input, timestep,
materials or Level1 geometry.
