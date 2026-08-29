param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '=== Stage24.47.0A Golden Eggs resource-root hotfix ===' -ForegroundColor Cyan
Write-Host 'Witness: untouched Golden Eggs menu passes levels/goldeneggs1/... while original files live under data/levels/goldeneggs1/...'
Write-Host 'Fix: generic native resource search-root reconstruction; no egg-specific filename hack.'
Write-Host ''

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
    if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }
}

Write-Host ''
Write-Host 'On the phone:' -ForegroundColor Yellow
Write-Host '  1. Open Golden Eggs normally.'
Write-Host '  2. Click the same egg from the crash if convenient (slot 11 / LevelGE_7), or any other egg already selectable in the save.'
Write-Host '  3. Confirm the level gets past loading. Interact with it naturally.'
Write-Host '  4. If it works, sample other already-selectable eggs/soundboards.'
Write-Host '  5. Do NOT synthesize unlocks or edit the save.'
Write-Host '  6. Stop on the first new missing resource, Lua/GPU error, broken mechanic, or crash.'
Write-Host ''
Read-Host '[stage24.47.0A] When the sample is done (or first new failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File .\pull-stage24-live-log.ps1
if ($LASTEXITCODE -ne 0) { throw "diagnostic pull failed exit=$LASTEXITCODE" }

Write-Host ''
Write-Host 'Golden Eggs resource-root diagnostics collected.' -ForegroundColor Green
Write-Host ' Key report: stage24.47.0a-golden-eggs-resource-root-runtime.txt'
