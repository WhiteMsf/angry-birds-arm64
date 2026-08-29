$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.42.0 - DANGER ABOVE PAGE 1 / THEME 6 + BOOMERANG'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Poached Eggs 1-1..3-21 complete'
Write-Host '  - Mighty Hoax 4-1..5-21 complete'
Write-Host '  - generic checkForLuaFile / polygon / Theme1..5 runtime-proven'
Write-Host ''
Write-Host 'This pass uses one natural page/theme QA boundary: 6-1..6-15.'
Write-Host 'Danger Above page 1 original map:'
Write-Host '  6-1  LevelP3_212  6-2  LevelP3_134  6-3  LevelP3_162  6-4  LevelP3_271  6-5  LevelP3_224'
Write-Host '  6-6  LevelP3_253  6-7  LevelP3_225  6-8  LevelP3_232  6-9  LevelP3_150  6-10 LevelP3_211'
Write-Host '  6-11 LevelP3_223  6-12 LevelP3_226  6-13 LevelP3_215  6-14 LevelP3_220  6-15 LevelP3_231'
Write-Host ''
Write-Host 'Theme6 exact transport: INGAME_SKIES_2 + INGAME_PARALLAX_6 + INGAME_GROUNDS_1 + INGAME_THEME_GROUND_6.'
Write-Host 'Boomerang policy: NO native specialty hack. Untouched updateGame BOOMERANG branch remains owner.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Confirm the Danger Above episode card now appears, then enter it.'
Write-Host '  2. Let any stock theme6Start/story transition run normally.'
Write-Host '  3. Play 6-1 through 6-15 using stock Next. Do not replay earlier campaigns.'
Write-Host '  4. When the Boomerang Bird appears, activate its specialty at least once in flight.'
Write-Host '  5. Finish 6-15 and press stock Next exactly once; let the page-completion/selection transition settle.'
Write-Host '  6. Stop immediately on first crash, Lua error, missing scene/object, frozen load, or file-not-found.'
Write-Host ''
Read-Host '[stage24.42.0] When page 6-1 -> 6-15 + one stock Next are done (or first failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.42.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.42.0-danger-above-theme6-boomerang-runtime.txt'
Write-Host '============================================================'
