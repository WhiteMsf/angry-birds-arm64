param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '=== Stage24.47.3 High-restitution contact solver cross-proof ===' -ForegroundColor Cyan
Write-Host 'Observe-only: no restitution/contact/joint/body/Lua mutation.'
Write-Host 'Goal: isolate the rubber contact solver from the spring network before changing restitution=5.5.'
Write-Host ''

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
    if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }
}

Write-Host ''
Write-Host 'On the phone:' -ForegroundColor Yellow
Write-Host '  1. Open Golden Egg 2 (LevelGE_2), the one with the free ExtraRubberBall / beachball objects.'
Write-Host '  2. Make 2-3 clear bird <-> ExtraRubberBall impacts. Do NOT solve the egg; clean impacts matter more.'
Write-Host '  3. If possible, hit a ball that is not simultaneously touching another object. The observer will classify isolation automatically.'
Write-Host '  4. Then open Danger Above 8-3 (LevelP3_306).'
Write-Host '  5. Make one clear bird <-> ExtraTrampoline impact for the joint-network cross-check.'
Write-Host '  6. Stop there; no completion is required.'
Write-Host ''
Read-Host '[stage24.47.3] After those samples (or first failure), press ENTER'

& powershell -ExecutionPolicy Bypass -File .\pull-stage24-live-log.ps1
if ($LASTEXITCODE -ne 0) { throw "diagnostic pull failed exit=$LASTEXITCODE" }

Write-Host ''
Write-Host 'High-restitution contact solver diagnostics collected.' -ForegroundColor Green
Write-Host ' Key reports:'
Write-Host '  - stage24.47.3-high-restitution-contact-solver-native-audit.txt'
Write-Host '  - stage24.47.3-high-restitution-contact-solver-runtime.txt'
