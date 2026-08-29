$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.32.0 - PACK1 PROGRESSION EXPANSION TO 1-3'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Authority: untouched levelSelectionPagesBasic runtime map.'
Write-Host 'Expected: 1-1=Level1, 1-2=Level57, 1-3=Level53.'
Write-Host 'No Level57 -> Level53 override exists; stock getNextLevel/unlock owns the transition.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1) Navigate normally to human level 1-2 (Level57).'
Write-Host '  2) Complete/replay 1-2 normally.'
Write-Host '  3) Press the ORIGINAL Next button on the result screen.'
Write-Host '     Expected: human 1-3 loads as Level53 without ENOENT/crash.'
Write-Host '  4) In 1-3, make at least one normal shot and inspect the scene/HUD quickly.'
Write-Host '     Full 1-3 completion is optional for this transport pass.'
Write-Host '  5) If convenient, return to level selection and confirm 1-3 is available according to stock progress.'
Write-Host ''
Write-Host 'Passive score telemetry remains OBSERVE_ONLY for any level you play.'
Write-Host ''
Read-Host '[stage24.32.0] When the 1-2 -> 1-3 transition test is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.32.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports:'
Write-Host '  stage24.32.0-progression-expansion-contract.txt'
Write-Host '  stage24.32.0-progression-runtime.txt'
Write-Host '  stage24.31.5-score-passive-runtime.txt'
Write-Host '============================================================'
