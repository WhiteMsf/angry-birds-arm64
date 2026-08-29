$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.34.0 - PACK1 1-16 + ORIGINAL YELLOW BOOST AUDIT'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Already validated and retained:'
Write-Host '  - stock progression through 1-10'
Write-Host '  - Android pinch -> zoomLevel -> untouched doItAllCamera'
Write-Host '  - Blue CLUSTER_BOMB a/b/c children, collisions and score'
Write-Host ''
Write-Host 'New original Pack1 mapping transported by this build:'
Write-Host '  1-11 Level9   1-12 Level13  1-13 Level10'
Write-Host '  1-14 Level39  1-15 Level12  1-16 Level15'
Write-Host ''
Write-Host 'Yellow policy: NO native boost implementation.'
Write-Host 'Untouched updateGame BOOST owns applyImpulse, particles, audio and BIRD_YELLOW_SPECIAL.'
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Continue from 1-10/1-11 using the ORIGINAL level-selection/Next flow.'
Write-Host '  2. Verify 1-11, 1-12, 1-13, 1-14 and 1-15 load and are playable.'
Write-Host '     No need for three stars; ordinary completion is enough.'
Write-Host '  3. Reach 1-16 (physical Level15). Note whether the original Yellow tutorial appears.'
Write-Host '  4. Launch the Yellow bird normally.'
Write-Host '  5. TAP ONCE while it is clearly in flight.'
Write-Host '     Expected if stock BOOST survives: immediate acceleration + special sprite/effects/audio.'
Write-Host '  6. Let it hit something and run for several seconds.'
Write-Host '  7. If anything crashes/freezes or the tap causes a Lua/native error, STOP at first failure.'
Write-Host '     Do not retry/work around it; the diagnostic is the useful result.'
Write-Host ''
Read-Host '[stage24.34.0] When the progression/Yellow test is done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.34.0 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key reports:'
Write-Host '  stage24.34.0-pack1-yellow-boost-contract.txt'
Write-Host '  stage24.34.0-pack1-yellow-boost-runtime.txt'
Write-Host '  stage24.32.1-pack1-multitouch-specialty-runtime.txt'
Write-Host '  stage24-native-stderr.log'
Write-Host '============================================================'
