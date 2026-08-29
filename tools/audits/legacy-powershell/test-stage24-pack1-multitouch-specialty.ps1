$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.32.1 - PACK1 1-10 + MULTITOUCH + SPECIALTY AUDIT'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Original Pack1 mapping used by this build:'
Write-Host '  1-1 Level1   1-2 Level57  1-3 Level53  1-4 Level3   1-5 Level6'
Write-Host '  1-6 Level2   1-7 Level4   1-8 Level5   1-9 Level7   1-10 Level8'
Write-Host ''
Write-Host 'Multitouch policy: two-pointer Android compatibility producer -> Lua zoomLevel only.'
Write-Host 'Untouched doItAllCamera remains the camera/scale/clamp owner.'
Write-Host 'Blue policy: NO native split hack. 1-10 exercises the untouched Lua specialty branch.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  A) MULTITOUCH'
Write-Host '     1. Enter any gameplay level.'
Write-Host '     2. With TWO fingers, spread them apart and then pinch them together.'
Write-Host '        Expected: camera zoom changes smoothly; no bird is launched by finger #2.'
Write-Host '     3. Then use one finger normally and confirm sling drag/fire still works.'
Write-Host ''
Write-Host '  B) PACK1 PROGRESSION'
Write-Host '     4. Progress normally through the newly transported early levels.'
Write-Host '        Spot-check that 1-4..1-9 load and are playable; no need to 3-star them.'
Write-Host '     5. Reach/open 1-10. Expected physical filename is original Level8.'
Write-Host ''
Write-Host '  C) BLUE SPECIALTY - IMPORTANT'
Write-Host '     6. Launch the Blue bird in 1-10, then TAP ONCE while it is in flight.'
Write-Host '        If it splits into three: excellent, just continue a few seconds.'
Write-Host '        If it does NOT split, crashes, or behaves oddly: STOP THERE.'
Write-Host '        Do not retry or work around it; the runtime audit is designed to catch the exact frontier.'
Write-Host ''
Write-Host 'Passive score telemetry remains enabled throughout.'
Write-Host ''
Read-Host '[stage24.32.1] When the test above is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.32.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports:'
Write-Host '  stage24.32.1-pack1-multitouch-specialty-contract.txt'
Write-Host '  stage24.32.1-pack1-multitouch-specialty-runtime.txt'
Write-Host '  stage24.31.5-score-passive-runtime.txt'
Write-Host '============================================================'
