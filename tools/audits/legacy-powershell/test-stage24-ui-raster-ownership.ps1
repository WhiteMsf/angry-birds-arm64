$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.4e - ORIGINAL 1:1 RASTER OWNERSHIP A/B TEST'
Write-Host '============================================================'
Write-Host ''
Write-Host 'This is intentionally NOT the final presentation.'
Write-Host 'The 854x480 game will appear small and centered with large black borders.'
Write-Host 'That is the point: one logical pixel maps to exactly one framebuffer pixel,'
Write-Host 'matching the WVGA-era ARMv7 rasterization contract before any modern scaling.'
Write-Host ''
Write-Host 'UVs remain edge-to-edge, sampler remains LINEAR, and POT backing remains enabled.'
Write-Host 'No half-texel correction is used.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'reset-stage24-tutorial-first-run.ps1')
if ($LASTEXITCODE -ne 0) { throw "Tutorial first-run reset failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone inspect:'
Write-Host '  1) Play -> Episode Selection -> Poached Eggs card.'
Write-Host '  2) Enter 1-1, let the story finish, inspect the tutorial popup.'
Write-Host ''
Write-Host 'IGNORE the tiny overall presentation. Look ONLY for the straight UI seams.'
Read-Host '[raster-ownership] After inspecting both, press ENTER here'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.4e capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip and tell me whether the seams vanished.'
Write-Host '============================================================'
