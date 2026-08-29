$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.4c - ORIGINAL EGL_IMAGE POT-BACKING VISUAL TEST'
Write-Host '============================================================'
Write-Host ''
Write-Host 'This test uses the recovered ARMv7 EGL_Image/EGL_Texture architecture: edge UVs + next-POT physical backing. The old half-texel experiment is OFF.'
Write-Host 'Gear + Golden Egg transform bugs are intentionally left for the next stage.'
Write-Host ''
Write-Host 'I will build/install, then reset ONLY settings.lua so the 1-1 tutorial can be seen.'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'reset-stage24-tutorial-first-run.ps1')
if ($LASTEXITCODE -ne 0) { throw "Tutorial first-run reset failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone, inspect these TWO places:'
Write-Host '  1) Play -> Episode Selection: look closely at the Poached Eggs card borders/straight lines.'
Write-Host '  2) Enter Poached Eggs 1-1, let the story finish, and inspect the tutorial popup.'
Write-Host ''
Write-Host 'Do not worry about the gear or Golden Egg yet.'
Read-Host '[ui-seam] When you have inspected both screens, press ENTER here'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.4c POT-backing visual capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT and tell me whether the lines disappeared.'
Write-Host '============================================================'
