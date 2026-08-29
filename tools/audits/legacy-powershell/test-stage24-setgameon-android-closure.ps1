$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.44.3 - ORIGINAL ANDROID setGameOn / allowSleep'
Write-Host '============================================================'
Write-Host ''
Write-Host 'The v0.26.140 live run closed the offscreen-bird regression:'
Write-Host '  - all 3 right-limit crossings wrote frozen=true;'
Write-Host '  - untouched Lua removed the birds in 1, 1 and 2 frames;'
Write-Host '  - the old ~19 s linger disappeared;'
Write-Host '  - LEVEL FAILED reached normally; no Lua/native/GPU fatal error.'
Write-Host ''
Write-Host 'This stage closes the remaining setGameOn stub exactly.'
Write-Host 'ARMv7 setGameOn calls OSInterface virtual slot +0x18 with !gameOn.'
Write-Host 'The original Android vtable resolves that slot to allowSleep(bool),'
Write-Host 'and the shipping Android allowSleep body is exactly bx lr (no-op).'
Write-Host 'No KEEP_SCREEN_ON flag or other modern behavior is invented.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone - very short capture:'
Write-Host '  1. Launch the app and enter Poached Eggs 1-1.'
Write-Host '  2. Stay in gameplay for a second, then return to a menu or intentionally fail.'
Write-Host '  3. That is enough to exercise true/false setGameOn transitions.'
Write-Host ''
Read-Host '[stage24.44.3] After the short capture, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.44.3 validation complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key new reports:'
Write-Host '   stage24.44.3-setgameon-android-contract.txt'
Write-Host '   stage24.44.3-setgameon-android-runtime.txt'
Write-Host '============================================================'
