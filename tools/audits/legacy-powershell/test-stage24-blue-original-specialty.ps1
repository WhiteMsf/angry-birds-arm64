$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.33.0 - ORIGINAL BLUE SPECIALTY / createCircle META'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Prior run already proved:'
Write-Host '  - 1-10 = original Level8 loads.'
Write-Host '  - two-pointer pinch publishes zoomLevel and stock doItAllCamera changes worldScale.'
Write-Host '  - Blue reaches untouched Lua birdSpecialty=CLUSTER_BOMB.'
Write-Host '  - failure was createCircle arg #6 because flyingBird.density was absent from Lua object metadata.'
Write-Host ''
Write-Host 'This build repairs GENERIC createCircle object metadata only.'
Write-Host 'There is no SmallBlueBird native special-case and no native split implementation.'
Write-Host 'Existing save/profile is preserved, so you can open 1-10 directly.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Open human 1-10 directly.'
Write-Host '  2. Optional quick regression: pinch in/out once; camera should still zoom.'
Write-Host '  3. Pull and launch the first Blue bird.'
Write-Host '  4. TAP ONCE while it is clearly in flight.'
Write-Host '  5. If it splits, watch the children fly/collide for several seconds.'
Write-Host '     We specifically want the untouched Lua branch to create suffixes a/b/c.'
Write-Host '  6. If it crashes, freezes, or behaves incorrectly, STOP at the first failure.'
Write-Host '     Do not retry/work around it; the next missing contract should be in the log.'
Write-Host ''
Read-Host '[stage24.33.0] When the Blue test is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.33.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports:'
Write-Host '  stage24.33.0-createcircle-lua-metadata-contract.txt'
Write-Host '  stage24.32.1-pack1-multitouch-specialty-runtime.txt'
Write-Host '  stage24-native-stderr.log'
Write-Host '============================================================'
