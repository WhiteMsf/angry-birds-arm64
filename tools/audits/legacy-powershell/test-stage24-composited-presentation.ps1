$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.4f - COMPOSITED MODERN PRESENTATION TEST'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Expected architecture:'
Write-Host '  KA3D/game raster: 854x480 at literal 1:1 pixels'
Write-Host '  presentation: finished frame scaled once to the modern Surface'
Write-Host '  touch: visible output viewport mapped back to 854x480'
Write-Host ''
Write-Host 'Unlike the .105 proof, the game should now be large again.'
Write-Host 'Black side mattes are expected on wider-than-16:9 displays.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'reset-stage24-tutorial-first-run.ps1')
if ($LASTEXITCODE -ne 0) { throw "Tutorial first-run reset failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone verify:'
Write-Host '  1) Boot/Main Menu is large and centered; buttons respond where they are drawn.'
Write-Host '  2) Play -> Episode Selection -> Poached Eggs card has NO straight seam lines.'
Write-Host '  3) Enter 1-1, let the story finish; tutorial popup has NO straight seam lines.'
Write-Host '  4) Tap tutorial OK and make one slingshot interaction to prove touch mapping.'
Write-Host ''
Read-Host '[presentation] After checking those four items, press ENTER here'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.4f capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip.'
Write-Host '============================================================'
