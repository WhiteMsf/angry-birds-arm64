$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.46.2 - THE BIG SETUP PAGE 2 / PACK10'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Stage24.46.1 live-validated:'
Write-Host '  - 9-1..9-15 completed and persisted'
Write-Host '  - LevelP4_441 -> theme9Complete via stock Lua'
Write-Host '  - repeat=false crane layers render exactly once'
Write-Host '  - generic scene renderer survived themes 9, 10 and 11'
Write-Host ''
Write-Host 'This build adds only the exact second The Big Setup page:'
Write-Host '  10-1..10-15 / pack10 / world10 / pageIndex2'
Write-Host 'No per-level or Theme10 visual hacks are added.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open The Big Setup page 2 and enter 10-1 normally.'
Write-Host '  2. If 10-1 renders/plays cleanly, continue through 10-15 with stock Next.'
Write-Host '  3. Finish 10-15 and press stock Next once; let theme10Complete/selection settle.'
Write-Host '  4. Stop on the first missing resource, Lua error, GPU fail, crash, or obviously broken scene/physics.'
Write-Host ''
Read-Host '[stage24.46.2] When 10-1..10-15 are done (or first failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.46.2 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.46.2-big-setup-pack10-runtime.txt'
Write-Host '============================================================'
