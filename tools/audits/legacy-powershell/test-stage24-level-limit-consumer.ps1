$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.44.1 - LEVEL-LIMIT / UPDATE CONSUMER CAPTURE'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Already proven from the previous live run:'
Write-Host '  - setMaxTranslation reconstruction builds/runs cleanly.'
Write-Host '  - Level1 setLevelLimits stores minX=-66 maxX=104.'
Write-Host '  - RedBird_4 crossed maxX at x=104.447 and stayed outside for ~19 s.'
Write-Host '  - the phase kept hasMovingObjects=true until ordinary bird removal.'
Write-Host ''
Write-Host 'This build does NOT enforce level limits.'
Write-Host 'It captures the full original ARMv7 GameLua::update(float) and every'
Write-Host 'GameLua method that accesses +0x24c/+0x250. Runtime only computes a'
Write-Host 'shadow motion gate with outside bodies omitted; live behavior is untouched.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone - SHORT capture:'
Write-Host '  1. Open Poached Eggs 1-1 (the previous run already reproduced it there).'
Write-Host '  2. If convenient, launch one Red bird hard to the right so it crosses maxX.'
Write-Host '  3. Let the game run about 10-20 seconds. Do not grind if it stays in bounds.'
Write-Host '  4. No need to complete the level.'
Write-Host ''
Read-Host '[stage24.44.1] After the short capture, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.44.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports now guaranteed inside the ZIP:'
Write-Host '   stage24.44.0-box2d-maxtranslation-patch.txt'
Write-Host '   stage24.44.0-bounds-lifecycle-ownership-contract.txt'
Write-Host '   stage24.44.1-level-limit-update-consumer-contract.txt'
Write-Host '   stage24.44.1-level-limit-runtime.txt'
Write-Host '============================================================'
