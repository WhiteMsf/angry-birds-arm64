$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.36.0 - PACK2 2-6 -> 2-14 + WHITE SPECIALTY AUDIT'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Pack1 1-1..1-21 + theme1Complete'
Write-Host '  - Pack2 2-1..2-5 including theme2 scene/terrain'
Write-Host '  - Blue CLUSTER_BOMB, Yellow BOOST, Bomb BOMB'
Write-Host ''
Write-Host 'Untouched Pack2 continuation:'
Write-Host '  2-6  Level36    2-7  Level31    2-8  Level21'
Write-Host '  2-9  Level41    2-10 Level76    2-11 Level38'
Write-Host '  2-12 Level35    2-13 Level20    2-14 Level26 (White debut)'
Write-Host ''
Write-Host 'Policy: NO native White/egg-drop implementation.'
Write-Host 'Untouched updateGame DROPPABLE_EGG -> createCircle/setVelocity/flyingGrenades remains authoritative.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open Poached Eggs page 2 and enter 2-6 (2-1..2-5 are already validated).'
Write-Host '  2. Play 2-6 through 2-13 using the original Next flow.'
Write-Host '  3. Enter 2-14 and verify the original White tutorial if it appears.'
Write-Host '  4. Launch White and tap once during flight to request the egg-drop specialty.'
Write-Host '  5. Watch for the egg dropping downward and White being kicked upward.'
Write-Host '  6. Let the egg/body aftermath run a few seconds for collision/score/audio.'
Write-Host '  7. On any crash/Lua error/freeze or obviously broken specialty, STOP at first failure.'
Write-Host ''
Read-Host '[stage24.36.0] When the 2-6 -> 2-14/White run is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.36.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.36.0-pack2-white-runtime.txt'
Write-Host '============================================================'
