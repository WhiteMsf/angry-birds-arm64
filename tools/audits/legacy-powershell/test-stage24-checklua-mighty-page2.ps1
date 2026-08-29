$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.41.0 - CHECKFORLUAFILE + MIGHTY HOAX 5-1 -> 5-10'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Mighty Hoax page 1 / 4-1..4-21 completed'
Write-Host '  - Theme4 + generic polygon native contract validated live'
Write-Host '  - stock theme4Complete returns to levelSelectionPagesExtra'
Write-Host ''
Write-Host 'This pass restores the generic read-only checkForLuaFile boolean contract.'
Write-Host 'Untouched hasLevelPack2/prepareMenuPage remains owner of the episode card.'
Write-Host 'No AVAILABLE_ON_APP_STORE/Ovi visual special-case is installed.'
Write-Host ''
Write-Host 'Mighty Hoax page 2 transport:'
Write-Host '  5-1 LevelP2_78   5-2 LevelP2_100  5-3 LevelP2_92   5-4 LevelP2_94'
Write-Host '  5-5 LevelP2_89   5-6 LevelP2_73   5-7 LevelP2_76   5-8 LevelP2_122'
Write-Host '  5-9 LevelP2_99   5-10 LevelP2_84'
Write-Host ''
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open Episode Selection and inspect the Mighty Hoax card.'
Write-Host '     Expected: stock score/stars UI; no Ovi Store banner now that Pack4 exists.'
Write-Host '  2. Enter Mighty Hoax. Do NOT replay 4-1..4-21.'
Write-Host '  3. Swipe to page 2 and enter 5-1 directly.'
Write-Host '  4. Visually check Theme5 sky/parallax/ground, then play 5-1 through 5-10 using stock Next.'
Write-Host '  5. Finish 5-10 and stop on its normal result screen; do not press Next after 5-10.'
Write-Host '  6. Stop earlier only at the first crash, Lua error, missing scene/object, frozen load, or file-not-found.'
Write-Host ''
Read-Host '[stage24.41.0] When card audit + 5-1 -> 5-10 are done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.41.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.41.0-checkforluafile-mighty-page2-runtime.txt'
Write-Host '============================================================'
