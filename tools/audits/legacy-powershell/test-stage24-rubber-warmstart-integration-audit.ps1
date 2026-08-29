param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '=== Stage24.47.4 Rubber warm-start / integration audit ===' -ForegroundColor Cyan
Write-Host 'Observe-only: no restitution, joint, contact, body or Lua mutation.'
Write-Host 'Goal: split warm-start manifold carryover from the island linear/angular clamps.'
Write-Host ''

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
    if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }
}

Write-Host ''
Write-Host 'On the phone:' -ForegroundColor Yellow
Write-Host '  1. Open the Golden Egg that loads LevelGE_2 (free ExtraRubberBall / beachballs).'
Write-Host '     - In the untouched menu table it is Golden-Egg levelIndex/pageLevelIndex 3; do not trust the visual item number as the level number.'
Write-Host '  2. Make 2-3 clear bird <-> beachball impacts. No need to solve it.'
Write-Host '  3. Then open Danger Above 8-3 (LevelP3_306).'
Write-Host '  4. Make one clear bird <-> ExtraTrampoline impact and let the rubber network wobble for a few seconds.'
Write-Host '  5. Stop there. If you accidentally open GE3 again, keep the sample anyway; it is still useful for the network side.'
Write-Host ''
Read-Host '[stage24.47.4] After those samples (or first failure), press ENTER'

& powershell -ExecutionPolicy Bypass -File .\pull-stage24-live-log.ps1
if ($LASTEXITCODE -ne 0) { throw "diagnostic pull failed exit=$LASTEXITCODE" }

Write-Host ''
Write-Host 'Warm-start / integration diagnostics collected.' -ForegroundColor Green
Write-Host ' Key reports:'
Write-Host '  - stage24.47.4-rubber-warmstart-integration-native-audit.txt'
Write-Host '  - stage24.47.4-rubber-warmstart-integration-runtime.txt'
