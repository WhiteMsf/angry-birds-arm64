$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.5 - MENU TRANSFORM + PASSIVE SCORE AUDIT'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Primary target: recover vanilla RenderState2D semantics for:'
Write-Host '  - Main Menu settings gear rotation/pivot'
Write-Host '  - About/Credits Golden Egg aura rotation/pivot'
Write-Host ''
Write-Host 'Passive target: observe 1-1 scoring WITHOUT changing score,'
Write-Host 'thresholds, scoreTable buckets, highscore, or bird bonus.'
Write-Host 'Your existing save/profile is preserved; this helper does NOT reset tutorial or progress.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1) Main Menu: click the settings gear TWICE.'
Write-Host '  2) About/Credits: trigger the hidden Golden Egg and watch the aura for ~2 seconds.'
Write-Host '  3) Play Poached Eggs 1-1 normally and FINISH the level.'
Write-Host '     Try for 3 stars if you want, but do not restart just to force a particular score.'
Write-Host '     The observer records threshold/max score, every score delta/bucket, completion gate,'
Write-Host '     remaining-bird bonus timing, and the RESULT_STARS sprite automatically.'
Write-Host ''
Read-Host '[stage24.31.5] When all three are done, press ENTER here to collect diagnostics'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.5 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports:'
Write-Host '  stage24.31.5-original-renderstate2d-contract.txt'
Write-Host '  stage24.31.5-menu-transform-runtime.txt'
Write-Host '  stage24.31.5-score-passive-contract.txt'
Write-Host '  stage24.31.5-score-passive-runtime.txt'
Write-Host '============================================================'
