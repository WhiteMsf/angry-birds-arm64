param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '=== Stage24.47.5 FP contraction / rubber order audit ===' -ForegroundColor Cyan
Write-Host 'Numerical-fidelity build: Box2D + live bridge use -ffp-contract=off.'
Write-Host 'No restitution, joint, body, contact, Lua or save mutation.'
Write-Host ''

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
    if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }
}

Write-Host ''
Write-Host 'On the phone:' -ForegroundColor Yellow
Write-Host '  1. Open the visual Golden Egg #2, which the untouched table resolves as LevelGE_3.'
Write-Host '  2. Hit the ExtraTrampoline / BLOCK_SUPER_BALL rubber network 1-2 times.'
Write-Host '  3. Let it wobble for a few seconds. No need to solve the level.'
Write-Host '  4. Open Danger Above 8-3 (LevelP3_306).'
Write-Host '  5. Make one clear impact on the same rubber/trampoline family and let it settle briefly.'
Write-Host '  6. Stop there. We are comparing the visible stiffness/decay against the previous contracted build.'
Write-Host ''
Read-Host '[stage24.47.5] After both samples (or first failure), press ENTER'

& powershell -ExecutionPolicy Bypass -File .\pull-stage24-live-log.ps1
if ($LASTEXITCODE -ne 0) { throw "diagnostic pull failed exit=$LASTEXITCODE" }

Write-Host ''
Write-Host 'FP-contraction / order diagnostics collected.' -ForegroundColor Green
Write-Host ' Key reports:'
Write-Host '  - stage24.47.5-fp-contraction-contract.txt'
Write-Host '  - stage24.47.5-fp-contraction-binary-audit.txt'
Write-Host '  - stage24.47.5-fp-contraction-order-runtime.txt'
Write-Host '  - stage24.47.4-rubber-warmstart-integration-runtime.txt'
