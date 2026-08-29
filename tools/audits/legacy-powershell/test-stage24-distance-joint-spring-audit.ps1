param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '=== Stage24.47.2 Distance-joint spring solver audit ===' -ForegroundColor Cyan
Write-Host 'Observe-only: no frequency/damping/restitution/joint-length/impulse mutation.'
Write-Host 'Goal: measure the rubber spring network and compare the original ARMv7 distance-joint solver.'
Write-Host ''

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
    if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }
}

Write-Host ''
Write-Host 'On the phone:' -ForegroundColor Yellow
Write-Host '  1. Open the Golden Egg with the rubber/super-ball trampoline network (the latest run identified LevelGE_3).'
Write-Host '  2. Cause 1-2 clear impacts that visibly make the rubber network flex. You do NOT need to solve it.'
Write-Host '  3. Leave the level once the soft/molenga behavior is obvious.'
Write-Host '  4. Open Danger Above 8-3 (LevelP3_306).'
Write-Host '  5. Cause one clear impact involving the same rubber/spring family.'
Write-Host '  6. Stop there. No need to complete either level.'
Write-Host ''
Read-Host '[stage24.47.2] After those samples (or first failure), press ENTER'

& powershell -ExecutionPolicy Bypass -File .\pull-stage24-live-log.ps1
if ($LASTEXITCODE -ne 0) { throw "diagnostic pull failed exit=$LASTEXITCODE" }

Write-Host ''
Write-Host 'Distance-joint spring diagnostics collected.' -ForegroundColor Green
Write-Host ' Key reports:'
Write-Host '  - stage24.47.2-distance-joint-solver-native-audit.txt'
Write-Host '  - stage24.47.2-distance-joint-spring-runtime.txt'
