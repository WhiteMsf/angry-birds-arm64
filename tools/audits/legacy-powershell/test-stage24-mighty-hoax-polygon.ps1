$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.40.0 - MIGHTY HOAX POLYGON NATIVE RECONSTRUCTION'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Poached Eggs 1-1..3-21 all completed through stock progression'
Write-Host '  - Stock gameComplete after 3-21 + real save profile'
Write-Host '  - Original LEVEL FAILED menu regression fixed/validated in 24.38.2'
Write-Host ''
Write-Host 'Untouched Mighty Hoax frontier from levelOrder.pack4:'
Write-Host '  4-1 LevelP2_103   4-2 LevelP2_91   4-3 LevelP2_65'
Write-Host '  4-4 LevelP2_96    4-5 LevelP2_69'
Write-Host ''
Write-Host 'Theme4 exact asset family from retained Stage24.15.0 inventory:'
Write-Host '  sky      = INGAME_SKIES_1 / BACKGROUND_4_LAYER_1'
Write-Host '  parallax = INGAME_PARALLAX_4 / BACKGROUND_4_LAYER_2 + _3 / FOREGROUND_4_LAYER_2'
Write-Host '  ground   = INGAME_GROUNDS_1 / FOREGROUND_4_LAYER_1'
Write-Host '  fill     = INGAME_THEME_GROUND_4'
Write-Host ''
Write-Host 'Policy: original assets/Lua only. No Mighty Hoax gameplay or progression override.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. From Episode Selection open "2. Mighty Hoax".'
Write-Host '  2. Enter 4-1 and first inspect sky/parallax/foreground/terrain.'
Write-Host '  3. Play 4-1 through 4-5 using the stock Next flow.'
Write-Host '  4. Let any stock story/cutscene transition run normally if it appears.'
Write-Host '  5. STOP on the FIRST crash, Lua error, black/missing scene, frozen frame, or impossible progression.'
Write-Host '  6. If 4-5 completes normally, stop on its result screen.'
Write-Host ''
Read-Host '[stage24.40.0] Enter Mighty Hoax 4-1. Confirm the full level appears. Play through 4-1 and continue toward 4-5 until first failure, then press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.40.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.40.0-polygon-native-runtime.txt'
Write-Host '============================================================'
