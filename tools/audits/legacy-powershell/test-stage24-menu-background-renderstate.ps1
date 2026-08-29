$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.37.0 - MENU BACKGROUND RENDERSTATE RE-AUDIT'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated gameplay baseline retained:'
Write-Host '  - Poached Eggs 1-1..2-21 all played/completed through stock progression'
Write-Host '  - theme1Complete + theme2Complete stock transitions'
Write-Host '  - Blue CLUSTER_BOMB, Yellow BOOST, Bomb BOMB, White DROPPABLE_EGG'
Write-Host ''
Write-Host 'This pass changes only the generic RenderState2D consumer ordering:'
Write-Host '  local pivot rotation -> draw origin/translation -> screen scale'
Write-Host 'No LS_BACKGROUND-specific geometry branch is present.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Let startup reach the Main Menu.'
Write-Host '  2. Open Episode Selection. Verify LS background art covers BOTH halves of the 854x480 game raster.'
Write-Host '  3. Enter Poached Eggs. Verify the level-selection background also covers the full width.'
Write-Host '  4. Swipe between Poached Eggs pages 1, 2 and 3; look for clipping, inversion or a flat-color half.'
Write-Host '  5. Return to Main Menu and click the settings gear once/twice. It must rotate in place, not disappear/drift.'
Write-Host '  6. Optional: if the About Golden Egg aura can still be observed with this save, confirm it remains attached while rotating.'
Write-Host '  7. No levels need to be replayed in this pass.'
Write-Host '  8. On any visual regression/crash/Lua error, STOP at the first failure.'
Write-Host ''
Read-Host '[stage24.37.0] When the menu-background/RenderState2D visual pass is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.37.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.37.0-renderstate-negative-scale-runtime.txt'
Write-Host '============================================================'
