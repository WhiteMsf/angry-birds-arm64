$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.40.2 - MIGHTY HOAX 4-11 -> 4-21 CLOSURE'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Runtime-validated baseline retained:'
Write-Host '  - Poached Eggs 63/63 completed'
Write-Host '  - Mighty Hoax 4-1..4-10 completed under Theme4'
Write-Host '  - generic polygon native contract validated live'
Write-Host ''
Write-Host 'Untouched Pack4 continuation:'
Write-Host '  4-11 LevelP2_82   4-12 LevelP2_66   4-13 LevelP2_104'
Write-Host '  4-14 LevelP2_210  4-15 LevelP2_83   4-16 LevelP2_79'
Write-Host '  4-17 LevelP2_77   4-18 LevelP2_114  4-19 LevelP2_81'
Write-Host '  4-20 LevelP2_68   4-21 LevelP2_95'
Write-Host ''
Write-Host 'Policy: transport + passive map/Next/completion telemetry only.'
Write-Host 'No per-level gameplay or progression override. Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open Mighty Hoax and enter 4-11 directly; 4-1..4-10 are validated.'
Write-Host '  2. Play 4-11 through 4-21 using the stock Next button.'
Write-Host '  3. Finish 4-21 and wait for the normal result screen.'
Write-Host '  4. Press stock Next ONCE after 4-21 and let the untouched transition settle.'
Write-Host '  5. Stop at the FIRST crash, Lua error, missing object/scene, frozen load, or file-not-found.'
Write-Host ''
Read-Host '[stage24.40.2] When the 4-11 -> 4-21 run/transition is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.40.2 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.40.2-mighty-hoax-4-21-closure-runtime.txt'
Write-Host '============================================================'
