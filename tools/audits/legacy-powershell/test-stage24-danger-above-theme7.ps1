$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.45.0 - DANGER ABOVE PAGE 2 / THEME 7'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline carried forward:'
Write-Host '  - Danger Above 6-1..6-15 / Theme6 complete'
Write-Host '  - original distance joints reconstructed'
Write-Host '  - original level-limit frozen consumer live-proven'
Write-Host '  - original Android setGameOn -> allowSleep(!gameOn) closure live-proven (shipping no-op)'
Write-Host ''
Write-Host 'This pass resumes stock progression at the next untouched 15-level page: 7-1..7-15.'
Write-Host 'Danger Above page 2 original map:'
Write-Host '  7-1  LevelP3_166  7-2  LevelP3_237  7-3  LevelP3_216  7-4  LevelP3_298  7-5  LevelP3_303'
Write-Host '  7-6  LevelP3_214  7-7  LevelP3_159  7-8  LevelP3_164  7-9  LevelP3_299  7-10 LevelP3_302'
Write-Host '  7-11 LevelP3_219  7-12 LevelP3_163  7-13 LevelP3_160  7-14 LevelP3_161  7-15 LevelP3_304'
Write-Host ''
Write-Host 'Theme7 exact transport: INGAME_SKIES_2 + INGAME_PARALLAX_7 + INGAME_GROUNDS_1 + INGAME_THEME_GROUND_7.'
Write-Host 'No Theme7 gameplay hack is added; original Lua/Box2D ownership is retained.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open Danger Above and enter 7-1.'
Write-Host '  2. Let any stock Theme7 story/start transition run normally.'
Write-Host '  3. Play 7-1 through 7-15 using stock Next.'
Write-Host '  4. Finish 7-15 and press stock Next exactly once; let theme7Complete/selection settle.'
Write-Host '  5. Stop immediately on first crash, Lua error, missing scene/object, frozen load, bad joint/bounds behavior, or file-not-found.'
Write-Host ''
Read-Host '[stage24.45.0] When 7-1 -> 7-15 + one stock Next are done (or first failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.45.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.45.0-danger-above-theme7-runtime.txt'
Write-Host '============================================================'
