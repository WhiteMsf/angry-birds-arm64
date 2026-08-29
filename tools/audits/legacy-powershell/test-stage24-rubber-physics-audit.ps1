param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '=== Stage24.47.1 Rubber / beachball physics audit ===' -ForegroundColor Cyan
Write-Host 'Observe-only: no restitution, damping, impulse, geometry, save or unlock changes.'
Write-Host 'Cross-repro: Golden Egg 2 + Danger Above 8-3.'
Write-Host ''

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
    if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }
}

Write-Host ''
Write-Host 'On the phone:' -ForegroundColor Yellow
Write-Host '  1. Open Golden Egg 2 (LevelGE_2). You do NOT need to solve it.'
Write-Host '  2. Fire/split a Blue so a bird clearly hits one of the beachball/rubber objects 2-3 times.'
Write-Host '  3. Once the wrong bounce is obvious, leave the level.'
Write-Host '  4. Open Danger Above 8-3 (LevelP3_306). You do NOT need to solve it.'
Write-Host '  5. Make one clear bird <-> rubber/beachball impact that reproduces the old mismatch.'
Write-Host '  6. Stop there. If either level crashes/errors first, stop immediately instead.'
Write-Host ''
Read-Host '[stage24.47.1] After those samples (or first failure), press ENTER'

& powershell -ExecutionPolicy Bypass -File .\pull-stage24-live-log.ps1
if ($LASTEXITCODE -ne 0) { throw "diagnostic pull failed exit=$LASTEXITCODE" }

Write-Host ''
Write-Host 'Rubber physics diagnostics collected.' -ForegroundColor Green
Write-Host ' Key report: stage24.47.1-rubber-physics-audit-runtime.txt'
