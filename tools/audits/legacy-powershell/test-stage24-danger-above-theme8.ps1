$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.45.1 - DANGER ABOVE PAGE 3 / THEME 8'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline carried forward:'
Write-Host '  - Danger Above 7-1..7-15 / Theme7 complete'
Write-Host '  - original distance joints reconstructed'
Write-Host '  - original level-limit frozen consumer live-proven'
Write-Host '  - original Android setGameOn -> allowSleep(!gameOn) closure live-proven (shipping no-op)'
Write-Host ''
Write-Host 'This pass closes stock Danger Above with its third/final 15-level page: 8-1..8-15.'
Write-Host 'Danger Above page 3 original map:'
Write-Host '  8-1  LevelP3_297  8-2  LevelP3_221  8-3  LevelP3_306  8-4  LevelP3_301  8-5  LevelP3_312'
Write-Host '  8-6  LevelP3_309  8-7  LevelP3_168  8-8  LevelP3_311  8-9  LevelP3_308  8-10 LevelP3_310'
Write-Host '  8-11 LevelP3_217  8-12 LevelP3_307  8-13 LevelP3_296  8-14 LevelP3_149  8-15 LevelP3_313'
Write-Host ''
Write-Host 'Theme8 exact transport: INGAME_SKIES_2 + INGAME_PARALLAX_8 + INGAME_GROUNDS_1 + INGAME_THEME_GROUND_8.'
Write-Host 'No Theme8 gameplay hack is added; original Lua/Box2D ownership is retained.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open Danger Above and enter 8-1.'
Write-Host '  2. Let any stock Theme8 story/start transition run normally.'
Write-Host '  3. Play 8-1 through 8-15 using stock Next.'
Write-Host '  4. Finish 8-15 and press stock Next exactly once; let theme8Complete/selection settle.'
Write-Host '  5. Stop immediately on first crash, Lua error, missing scene/object, frozen load, bad joint/bounds behavior, or file-not-found.'
Write-Host ''
Read-Host '[stage24.45.1] When 8-1 -> 8-15 + one stock Next are done (or first failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.45.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.45.1-danger-above-theme8-runtime.txt'
Write-Host '============================================================'
