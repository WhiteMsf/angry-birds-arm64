$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.46.0 - THE BIG SETUP PAGE 1 / THEME 9 DISCOVERY'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline carried forward:'
Write-Host '  - Danger Above 6-1..8-15 complete through stock Lua progression'
Write-Host '  - original distance joints reconstructed'
Write-Host '  - original level-limit frozen consumer live-proven'
Write-Host '  - original Android setGameOn -> allowSleep(!gameOn) closure live-proven'
Write-Host ''
Write-Host 'This pass enters The Big Setup through its first 15-level page: 9-1..9-15.'
Write-Host 'The Big Setup page 1 original map:'
Write-Host '  9-1  LevelP4_421  9-2  LevelP4_423  9-3  LevelP4_424  9-4  LevelP4_425  9-5  LevelP4_426'
Write-Host '  9-6  LevelP4_427  9-7  LevelP4_428  9-8  LevelP4_429  9-9  LevelP4_431  9-10 LevelP4_432'
Write-Host '  9-11 LevelP4_433  9-12 LevelP4_436  9-13 LevelP4_439  9-14 LevelP4_440  9-15 LevelP4_441'
Write-Host ''
Write-Host 'IMPORTANT: Theme9 scene composition is NOT guessed in this build.'
Write-Host 'The generic setTheme reconstruction will dump the exact original Theme9 color/layer table live.'
Write-Host 'The untouched INGAME_PARALLAX_CRANES sheet is staged only as discovery coverage.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open The Big Setup and enter 9-1 normally.'
Write-Host '  2. Let theme9Start/story transition run normally if it appears.'
Write-Host '  3. First priority: verify 9-1 renders and behaves normally. If scene/resource Lua error appears, STOP immediately.'
Write-Host '  4. If 9-1 is clean, continue 9-1 through 9-15 using stock Next.'
Write-Host '  5. Finish 9-15 and press stock Next once; let theme9Complete/next selection settle.'
Write-Host '  6. Stop on first crash, missing scene/object, bad physics/joint/bounds behavior, file-not-found, or Lua error.'
Write-Host ''
Read-Host '[stage24.46.0] When Theme9 discovery + 9-1..9-15 are done (or first failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.46.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.46.0-big-setup-theme9-runtime.txt'
Write-Host '============================================================'
