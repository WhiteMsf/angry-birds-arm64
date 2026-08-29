$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.40.1 - MIGHTY HOAX 4-6 -> 4-10'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Runtime-validated baseline retained:'
Write-Host '  - Poached Eggs 63/63 completed'
Write-Host '  - Mighty Hoax 4-1..4-5 completed under Theme4'
Write-Host '  - generic clearVertices/addVertex/createPolygon native contract validated live'
Write-Host ''
Write-Host 'Untouched Pack4 continuation:'
Write-Host '  4-6 LevelP2_88   4-7 LevelP2_64   4-8 LevelP2_80'
Write-Host '  4-9 LevelP2_108  4-10 LevelP2_85'
Write-Host ''
Write-Host 'Policy: transport + passive map/Next telemetry only. No per-level gameplay override.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open Mighty Hoax and enter 4-6 directly; 4-1..4-5 are already validated.'
Write-Host '  2. Play 4-6 through 4-10 using the stock Next button.'
Write-Host '  3. Stop at the FIRST crash, Lua error, missing scene/object, or frozen load.'
Write-Host '  4. If 4-10 completes normally, leave the result screen visible and capture.'
Write-Host ''
Read-Host '[stage24.40.1] When the 4-6 -> 4-10 run is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.40.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.40.1-mighty-hoax-4-10-runtime.txt'
Write-Host '============================================================'
