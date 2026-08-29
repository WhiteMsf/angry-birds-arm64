$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.5b - RENDERSTATE2D VALIDATION + PASSIVE SCORE'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Primary validation: recovered ARMv7 per-image RenderState2D consumer.'
Write-Host 'No BUTTON_OPTIONS / GOLDEN_EGG sprite-name correction exists.'
Write-Host ''
Write-Host 'Passive score telemetry remains enabled and OBSERVE_ONLY.'
Write-Host 'This helper preserves your existing save/profile.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone - UI FIRST:'
Write-Host '  1) Main Menu: click the settings gear TWICE.'
Write-Host '     Expected: it remains in place and rotates around its own pivot.'
Write-Host '  2) About/Credits: trigger the hidden Golden Egg.'
Write-Host '     Let the popup finish moving into the center, then watch the aura for ~2 seconds.'
Write-Host '     Expected: the aura stays attached to the centered egg/popup and rotates in place.'
Write-Host '  3) Quick regression glance: menus/text/cutscene should not have acquired transform drift.'
Write-Host ''
Write-Host 'OPTIONAL score sample:'
Write-Host '  - Play/finish 1-1 normally if you want another passive score sample.'
Write-Host '  - Do NOT chase 3 stars just for this validation; no score values are modified.'
Write-Host ''
Read-Host '[stage24.31.5b] When UI validation (and optional score sample) is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.5b capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports:'
Write-Host '  stage24.31.5b-renderstate2d-reconstruction-contract.txt'
Write-Host '  stage24.31.5-menu-transform-runtime.txt'
Write-Host '  stage24.31.5-score-passive-runtime.txt'
Write-Host '============================================================'
