$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.46.3 - THE BIG SETUP FINAL PAGE / PACK11'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Stage24.46.2 live-validated:'
Write-Host '  - 10-1..10-15 completed and persisted'
Write-Host '  - LevelP4_462 -> theme10Complete via stock Lua'
Write-Host '  - themes evolved 11 -> 12 -> 13 with no renderer/GPU failure'
Write-Host ''
Write-Host 'This build adds only the exact final The Big Setup page:'
Write-Host '  11-1..11-15 / pack11 / world11 / pageIndex3'
Write-Host 'No per-level, completion, or episode-finish hacks are added.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open The Big Setup page 3 and enter 11-1 normally.'
Write-Host '  2. If 11-1 renders/plays cleanly, continue through 11-15 with stock Next.'
Write-Host '  3. Finish 11-15 and press stock Next once.'
Write-Host '  4. Let every stock end-of-episode screen/transition settle; do not skip it immediately.'
Write-Host '  5. Stop on the first missing resource, Lua error, GPU fail, crash, or obviously broken scene/physics.'
Write-Host ''
Read-Host '[stage24.46.3] When 11-1..11-15 and the final stock transition are done (or first failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.46.3 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.46.3-big-setup-pack11-runtime.txt'
Write-Host '============================================================'
