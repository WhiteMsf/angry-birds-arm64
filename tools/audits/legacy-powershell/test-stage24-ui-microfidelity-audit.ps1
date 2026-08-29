$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.3 - UI MICRO-FIDELITY AUDIT'
Write-Host '============================================================'
Write-Host ''
Write-Host 'I will build/install/open the game.'
Write-Host 'Then do only these two things on the phone:'
Write-Host '  1) Main Menu: click the settings gear TWICE.'
Write-Host '  2) About/Credits: click the hidden Golden Egg and wait ~2 seconds.'
Write-Host 'If you naturally see one of the straight UI seam lines, leave it visible for a moment too.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '[ui-audit] Game is open. Reproduce gear + Golden Egg now.'
Read-Host '[ui-audit] When finished, press ENTER here to collect the diagnostic ZIP'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' UI audit capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host '============================================================'
