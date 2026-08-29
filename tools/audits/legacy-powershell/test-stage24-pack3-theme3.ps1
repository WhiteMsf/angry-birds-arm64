$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.38.0 - PACK3 3-1 -> 3-5 + THEME3 AUDIT'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Poached Eggs 1-1..2-21 + stock theme1Complete/theme2Complete'
Write-Host '  - Blue CLUSTER_BOMB, Yellow BOOST, Bomb BOMB, White DROPPABLE_EGG'
Write-Host '  - Stage24.37.0 full-width menu background / negative-scale RenderState2D'
Write-Host ''
Write-Host 'Untouched Pack3 frontier:'
Write-Host '  3-1 Level43   3-2 Level77   3-3 Level28   3-4 Level29   3-5 Level87'
Write-Host ''
Write-Host 'Theme3 exact asset contract from original Stage24.15 inventory:'
Write-Host '  sky      = INGAME_SKIES_1 / BACKGROUND_3_LAYER_1'
Write-Host '  parallax = INGAME_PARALLAX_3 / BACKGROUND_3_LAYER_2 + _3'
Write-Host '  ground   = INGAME_GROUNDS_1 / FOREGROUND_3_LAYER_1'
Write-Host '  fill     = INGAME_THEME_GROUND_3'
Write-Host ''
Write-Host 'Policy: original level/theme data only. No Level43 or theme3 gameplay override.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open Poached Eggs and swipe to page 3.'
Write-Host '  2. Enter 3-1. First inspect sky/parallax/ground for obvious missing/wrong layers.'
Write-Host '  3. Play 3-1 through 3-5 using the original Next flow.'
Write-Host '  4. Exercise normal birds/specialties when available; no special test is required.'
Write-Host '  5. If the FIRST crash/Lua error/black scene/frozen frame happens, STOP there.'
Write-Host '  6. If 3-5 completes normally, return to the result/selection screen and capture.'
Write-Host ''
Read-Host '[stage24.38.0] When the 3-1 -> 3-5 Theme3 run is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.38.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.38.0-pack3-theme3-runtime.txt'
Write-Host '============================================================'
