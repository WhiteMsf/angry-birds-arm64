$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.44.0 - BOUNDS / LIFECYCLE OWNERSHIP DISCOVERY'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Danger Above Theme6 progression complete.'
Write-Host '  - createJoint(type=1) distance joints now reconstruct correctly.'
Write-Host '  - 6-15 no longer self-massacres before the first shot.'
Write-Host '  - Mighty Hoax 5-11 suspended structure is owned by the same joint contract.'
Write-Host ''
Write-Host 'This build does TWO narrowly-scoped things:'
Write-Host '  1. Reconstructs setMaxTranslation exactly, including the Rovio-mutable'
Write-Host '     max/max^2 pair that stock Box2D 2.1.2 exposes only as macros.'
Write-Host '  2. Mirrors only the two ints ARMv7 setLevelLimits actually stores and'
Write-Host '     OBSERVES dynamic bodies crossing those horizontal limits.'
Write-Host ''
Write-Host 'setLevelLimits does NOT remove/clamp/sleep anything yet.'
Write-Host 'setGameOn also remains OBSERVE_ONLY.'
Write-Host 'The build-time report scans all ARMv7 GameLua methods for the actual'
Write-Host 'GameLua+0x24c/+0x250 consumer before we synthesize any bounds behavior.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone - SHORT capture only:'
Write-Host '  1. Open any already-unlocked gameplay level (6-15 is fine).'
Write-Host '  2. Make 1-2 normal shots. If convenient, send a bird/object far to one side.'
Write-Host '  3. If you naturally hit the old case where nothing is visible but the level'
Write-Host '     keeps waiting/moving, PERFECT: leave it like that for ~10 seconds.'
Write-Host '  4. Otherwise do NOT grind for it. ~10-20 seconds of ordinary gameplay is enough.'
Write-Host ''
Read-Host '[stage24.44.0] After the short gameplay capture, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.44.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports:'
Write-Host '   stage24.44.0-bounds-lifecycle-ownership-contract.txt'
Write-Host '   stage24.44.0-bounds-lifecycle-runtime.txt'
Write-Host '============================================================'
