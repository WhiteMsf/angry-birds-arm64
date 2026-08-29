$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$build = Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1'
Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage24.48.1 - RELEASE BRANDING / LAUNCHER CHECK'
Write-Host '============================================================'
Write-Host 'Goal: installed app must be named exactly "Angry Birds" and use the original launcher icon.'
Write-Host 'The icon is copied locally from your own angry-re/original APK; it is not bundled in this source ZIP.'
Write-Host ''
& powershell -ExecutionPolicy Bypass -File $build
if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }

$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (!(Test-Path $adb)) { throw "adb not found: $adb" }
& $adb shell input keyevent KEYCODE_HOME | Out-Null
Write-Host ''
Write-Host 'CHECK VISUAL:' -ForegroundColor Cyan
Write-Host '  1. Abra a lista de apps / launcher.'
Write-Host '  2. O nome deve aparecer exatamente como: Angry Birds'
Write-Host '  3. A miniatura deve ser o icone original do Angry Birds, sem placeholder Stage24.'
Write-Host '  4. Abra o jogo pelo icone e confirme que inicia normalmente.'
Write-Host ''
Read-Host 'Quando conferir nome + icone, pressione ENTER'

$out = Join-Path $root 'stage24-output'
$branding = Join-Path $out 'stage24.48.1-apk-branding-audit.txt'
$origin = Join-Path $out 'stage24.48.1-original-launcher-icon.txt'
if (!(Test-Path $branding)) { throw "branding audit missing: $branding" }
if (!(Test-Path $origin)) { throw "original icon provenance report missing: $origin" }
Write-Host 'Stage24.48.1 packaging gates PASS. Visual launcher verdict is yours.' -ForegroundColor Green
