$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.38.2 - LEVEL FAILED MENU BOOT REGRESSION'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Why this exists:'
Write-Host '  - The 3-19 stress run exposed a long-latent boot regression.'
Write-Host '  - Stage24.29.0 had overwritten original menu table levelFailed with false.'
Write-Host '  - This build preserves initializeMenu levelFailed.items and leaves'
Write-Host '    levelFailedTimer / updateLevelEnding ownership untouched.'
Write-Host ''
Write-Host 'Poached Eggs 1-1..3-21 is already completed in the existing profile.'
Write-Host 'DO NOT replay the chapter for this test.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Enter any convenient normal level (1-1 is fine).'
Write-Host '  2. Intentionally waste every bird while leaving at least one pig alive.'
Write-Host '  3. DO NOT press Restart immediately. Leave the game alone for ~3 seconds.'
Write-Host '  4. Confirm the original LEVEL FAILED menu appears instead of freezing/erroring.'
Write-Host '  5. Press Restart once and confirm the level reloads normally.'
Write-Host '  6. Stop there. No progression replay is needed.'
Write-Host ''
Read-Host '[stage24.38.2] After the failure-menu + one Restart test, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.38.2 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.38.2-level-failed-menu-boot-regression-runtime.txt'
Write-Host '============================================================'
