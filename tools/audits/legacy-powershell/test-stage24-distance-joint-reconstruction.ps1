$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.43.1 - ORIGINAL DISTANCE-JOINT RECONSTRUCTION'
Write-Host '============================================================'
Write-Host ''
Write-Host 'New evidence from the Stage24.43.0a run:'
Write-Host '  - Danger Above 6-15 (LevelP3_231) calls createJoint NINE times per load.'
Write-Host '  - Every live joint is type=1 / coordType=2 / local anchors=(0,0)->(0,0).'
Write-Host '  - Each joint connects a pig body to a static balloon body.'
Write-Host '  - With createJoint headless, score rose to ~55,920 before ANY bird was shot.'
Write-Host '  - ARMv7 proves type=1 -> b2DistanceJointDef, 4 Hz, damping 0.5.'
Write-Host ''
Write-Host 'This build reconstructs createJoint(type=1) + destroyJoint generically.'
Write-Host 'setLevelLimits/setMaxTranslation/setGameOn remain OBSERVE_ONLY.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone - focused QA:'
Write-Host '  1. Open Danger Above 6-15 (LevelP3_231).'
Write-Host '  2. DO NOT TOUCH THE SLING for ~10 seconds.'
Write-Host '     Expected: balloon pigs remain tethered; no ~55k automatic massacre.'
Write-Host '  3. Make at least one normal shot / let an attached pig die if convenient.'
Write-Host '     This exercises destroyJoint lifecycle. Full completion is NOT required.'
Write-Host '  4. Restart 6-15 once and wait a few seconds again (joint recreate hygiene).'
Write-Host '  5. Then open Mighty Hoax 5-11 (LevelP2_86).'
Write-Host '     Watch the flag-like suspended structure for ~5-10 seconds.'
Write-Host '     If it now stays attached, the same distance-joint contract owned it.'
Write-Host '     If it still falls, do NOT grind the level: telemetry will reveal its type.'
Write-Host ''
Write-Host '6-14 and the stock Theme6 completion flow do NOT need replay: the previous'
Write-Host 'diagnostic already reached theme6Complete, persisted theme6Completed=true,'
Write-Host 'and returned to levelSelectionPagesPack3.'
Write-Host ''
Read-Host '[stage24.43.1] After 6-15 stability/restart + 5-11 visual check, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.43.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports:'
Write-Host '   stage24.43.1-distance-joint-contract.txt'
Write-Host '   stage24.43.1-distance-joint-runtime.txt'
Write-Host '   stage24.43.0-joint-bounds-discovery-runtime.txt'
Write-Host '============================================================'
