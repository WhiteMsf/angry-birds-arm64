param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '=== Stage24.47.0 Golden Eggs discovery ===' -ForegroundColor Cyan
Write-Host 'Campaign baseline: gameCompleted=true / The Big Setup closed.'
Write-Host 'Golden Eggs menu: 19 slots = 15 LevelGE gameplay entries + 4 Lua-owned soundboards.'
Write-Host 'No unlocks are synthesized by this test.'
Write-Host ''

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
    if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }
}

Write-Host ''
Write-Host 'On the phone:' -ForegroundColor Yellow
Write-Host '  1. Open the Golden Eggs page normally.'
Write-Host '  2. Click the SAME egg sampled in the previous run: slot 3 / LevelGE_2.'
Write-Host '  3. Let it load completely. If it behaves normally, interact/finish it naturally.'
Write-Host '  4. Return to Golden Eggs and try the other items that are ALREADY selectable in your save, one by one.'
Write-Host '     Soundboards are valid too; interact with each available one briefly.'
Write-Host '  5. Do NOT modify/unlock save data just for this test.'
Write-Host '  6. Stop immediately on the first missing resource, Lua/GPU error, frozen load, broken special mechanic, or crash.'
Write-Host ''
Read-Host '[stage24.47.0] When the available Golden Eggs sample is done (or first failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File .\pull-stage24-live-log.ps1
if ($LASTEXITCODE -ne 0) { throw "diagnostic pull failed exit=$LASTEXITCODE" }

Write-Host ''
Write-Host 'Golden Eggs diagnostics collected.' -ForegroundColor Green
Write-Host ' Key report: stage24.47.0-golden-eggs-runtime.txt'
