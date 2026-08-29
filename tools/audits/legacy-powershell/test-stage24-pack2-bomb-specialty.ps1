$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.35.2 - THEME2 TERRAIN HOTFIX + 2-1 -> 2-5 + BOMB'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - theme 1 / 1-1..1-21 stock progression + theme1Complete'
Write-Host '  - pinch zoom through untouched doItAllCamera'
Write-Host '  - Blue CLUSTER_BOMB original specialty'
Write-Host '  - Yellow BOOST original specialty'
Write-Host ''
Write-Host 'Stage 24.35.2 fix:'
Write-Host '  - MaskedImage fill now follows original per-object textureName (GROUND_1/GROUND_2)'
Write-Host '  - no Level34 special case; exact original theme-ground PVRs are used'
Write-Host ''
Write-Host 'Untouched theme-2 transport:'
Write-Host '  2-1 Level52   2-2 Level34   2-3 Level42'
Write-Host '  2-4 Level24   2-5 Level88 (Bomb debut / BOMB audit)'
Write-Host ''
Write-Host 'Policy: no Bomb explosion hack. updateGame/makeExplosion/removeBird remain original Lua-owned.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Let the saved theme1Complete/level-selection flow settle normally.'
Write-Host '  2. Enter 2-1 from the original level-selection page.'
Write-Host '  3. Verify 2-1, 2-2, 2-3 and 2-4 load/play and use original Next.'
Write-Host '  4. Enter 2-5 and verify the original Bomb tutorial if it appears.'
Write-Host '  5. Launch Bomb, then tap once during flight / after impact to request manual detonation.'
Write-Host '  6. If it explodes, leave the aftermath running a few seconds for physics/score/particles/audio.'
Write-Host '  7. If any level or Bomb path errors/freezes/crashes, STOP at the first failure.'
Write-Host ''
Read-Host '[stage24.35.2] When the 2-1 -> 2-5/Bomb run is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.35.2 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report:'
Write-Host '  stage24.35.0-pack2-bomb-runtime.txt'
Write-Host '  stage24.35.1-theme2-scene-metadata-contract.txt'
Write-Host '  stage24.35.2-theme-ground-fill-runtime.txt'
Write-Host '============================================================'
