﻿$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.38.1 - PACK3 3-6 -> 3-21 POACHED EGGS CLOSURE'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Poached Eggs 1-1..2-21 stock progression'
Write-Host '  - Pack3/Theme3 3-1..3-5 runtime validated'
Write-Host '  - Theme3 parallax + terrain fill'
Write-Host '  - Blue, Yellow, Bomb and White specialties'
Write-Host ''
Write-Host 'Untouched Pack3 continuation:'
Write-Host '  3-6 Level18   3-7 Level91   3-8 Level49   3-9 Level45'
Write-Host '  3-10 Level75  3-11 Level51  3-12 Level30  3-13 Level79'
Write-Host '  3-14 Level40  3-15 Level59  3-16 Level58  3-17 Level95'
Write-Host '  3-18 Level82  3-19 Level22  3-20 Level89  3-21 Level81'
Write-Host ''
Write-Host 'Policy: pure original level transport. No progression/theme3Complete override.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open Poached Eggs page 3 and enter 3-6 (3-1..3-5 are validated).'
Write-Host '  2. Play 3-6 through 3-21 using the original Next flow.'
Write-Host '  3. Finish 3-21 and wait for the normal result screen.'
Write-Host '  4. Press the original Next once and observe what untouched Lua does.'
Write-Host '  5. Let any theme3Complete/selection/episode transition settle completely.'
Write-Host '  6. On any crash/Lua error/freeze, STOP at the first failure.'
Write-Host ''
Read-Host '[stage24.38.1] When the 3-6 -> 3-21 closure run is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.38.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.38.1-pack3-chapter3-closure-runtime.txt'
Write-Host '============================================================'
