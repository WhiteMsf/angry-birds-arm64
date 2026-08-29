$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.42.1 - BOOMERANG DEFERRED VELOCITY + PHYSICS AUDIT'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated frontier retained:'
Write-Host '  - Poached Eggs complete'
Write-Host '  - Mighty Hoax complete'
Write-Host '  - Danger Above 6-1..6-4 already passed in the previous run'
Write-Host '  - Theme6 loaded; BOOMERANG Lua specialty activated correctly'
Write-Host ''
Write-Host 'This pass fixes the generic nonlegacy bird-destruction deferred-velocity path.'
Write-Host 'It also adds READ-ONLY glass/wood contact + physics-enable telemetry.'
Write-Host 'No friction/restitution/gravity/sleep/contact constants are changed by the audit.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Go directly to Danger Above 6-5. Do NOT replay 6-1..6-4.'
Write-Host '  2. Launch the Boomerang Bird and activate its specialty at least once.'
Write-Host '  3. Let it hit/destroy wood; the old crash happened on that destruction path.'
Write-Host '  4. If 6-5 survives, continue normally toward 6-15 using stock Next.'
Write-Host '  5. Stop immediately on the first crash/Lua error/frozen load/file-not-found.'
Write-Host '  6. The glass/wood audit runs passively around each physics-enable transition.'
Write-Host ''
Read-Host '[stage24.42.1] When 6-5 -> 6-15 is done (or first failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.42.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.42.1-nonlegacy-bird-velocity-physics-audit-runtime.txt'
Write-Host '============================================================'
