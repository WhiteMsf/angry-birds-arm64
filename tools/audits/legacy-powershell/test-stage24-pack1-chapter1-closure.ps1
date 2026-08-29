$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.34.1 - PACK1 CHAPTER 1 CLOSURE (1-17 -> 1-21)'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Pack1 1-1..1-16 stock progression'
Write-Host '  - pinch zoom through untouched doItAllCamera'
Write-Host '  - Blue CLUSTER_BOMB original specialty'
Write-Host '  - Yellow BOOST original specialty'
Write-Host ''
Write-Host 'New untouched Pack1 transport:'
Write-Host '  1-17 Level17   1-18 Level14   1-19 Level16'
Write-Host '  1-20 Level23   1-21 Level44'
Write-Host ''
Write-Host 'Policy: pure level transport. No Next/unlock/save/score/bird behavior override.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Continue from 1-16 using the ORIGINAL Next/level-selection flow.'
Write-Host '  2. Verify 1-17, 1-18, 1-19, 1-20 and 1-21 each load and are playable.'
Write-Host '  3. Ordinary completion is enough; three stars are not required.'
Write-Host '  4. Use Blue/Yellow abilities normally when present; they are regression coverage.'
Write-Host '  5. Finish 1-21 and leave the result/next transition visible for a moment.'
Write-Host '  6. If any level crashes/freezes or Next points somewhere invalid, STOP at first failure.'
Write-Host ''
Read-Host '[stage24.34.1] When the 1-17 -> 1-21 run is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.34.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report:'
Write-Host '  stage24.34.1-pack1-chapter1-closure-runtime.txt'
Write-Host '============================================================'
