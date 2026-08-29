﻿$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.36.1 - PACK2 2-15 -> 2-21 CHAPTER CLOSURE'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Pack1 1-1..1-21 + theme1Complete'
Write-Host '  - Pack2 2-1..2-14'
Write-Host '  - Blue CLUSTER_BOMB, Yellow BOOST, Bomb BOMB, White DROPPABLE_EGG'
Write-Host ''
Write-Host 'Untouched Pack2 closure:'
Write-Host '  2-15 Level66   2-16 Level85   2-17 Level27'
Write-Host '  2-18 Level32   2-19 Level72   2-20 Level90   2-21 Level96'
Write-Host ''
Write-Host 'Policy: pure original level transport. No progression/theme2Complete override.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open Poached Eggs page 2 and enter 2-15 (2-1..2-14 are validated).'
Write-Host '  2. Play 2-15 through 2-21 using the original Next flow.'
Write-Host '  3. Finish 2-21 and wait for the normal result screen.'
Write-Host '  4. Press the original Next once and observe what untouched Lua does.'
Write-Host '  5. If a theme2Complete/selection transition appears, let it settle completely.'
Write-Host '  6. On any crash/Lua error/freeze, STOP at the first failure.'
Write-Host ''
Read-Host '[stage24.36.1] When the 2-15 -> 2-21 closure run is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.36.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.36.1-pack2-chapter2-closure-runtime.txt'
Write-Host '============================================================'
