$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.43.0 - JOINT + BOUNDS CONTRACT DISCOVERY'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Poached Eggs complete'
Write-Host '  - Mighty Hoax complete'
Write-Host '  - Danger Above 6-1..6-12 complete in current partial run'
Write-Host '  - Stage24.42.1 deferred Boomerang velocity path survived through 6-12'
Write-Host ''
Write-Host 'This is a DISCOVERY build, not a guessed joint implementation.'
Write-Host 'Build-time audit captures original ARMv7 createJoint/destroyJoint bodies.'
Write-Host 'Runtime captures every createJoint argument + matching body state in 5-11.'
Write-Host 'setLevelLimits/setMaxTranslation/setGameOn are also logged OBSERVE_ONLY.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone - focused capture (no level completion needed):'
Write-Host '  1. Open Mighty Hoax 5-11 (LevelP2_86).'
Write-Host '  2. Let the level settle/start normally; do not immediately restart.'
Write-Host '  3. Watch the flag-like suspended polygon/support structure for ~5-10 seconds.'
Write-Host '  4. It is EXPECTED to still fall in this discovery build; we are capturing WHY.'
Write-Host '  5. Do not waste time finishing 5-11. Once the bad structure has fallen, return here.'
Write-Host ''
Write-Host 'After this capture you may continue Danger Above 6-13..6-15 separately.'
Write-Host 'Do NOT replay 6-1..6-12.'
Write-Host ''
Read-Host '[stage24.43.0] After reproducing the 5-11 structure once, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.43.0 discovery capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports:'
Write-Host '   stage24.43.0-joint-bounds-discovery-contract.txt'
Write-Host '   stage24.43.0-joint-bounds-discovery-runtime.txt'
Write-Host '============================================================'
