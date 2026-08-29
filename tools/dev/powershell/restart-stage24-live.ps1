$ErrorActionPreference = 'Stop'
$sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$adb = Join-Path $sdk 'platform-tools\adb.exe'
if (!(Test-Path $adb)) { throw 'adb.exe not found.' }
$pkg = 'dev.angryarm64.stage24'
$component = 'dev.angryarm64.stage24/android.app.NativeActivity'

$device = @(& $adb devices | Select-String '\tdevice$')
if (!$device) { throw 'No authorized Android device found.' }

Write-Host '[stage24.31.1] Force-stopping app WITHOUT reinstall/clear-data...'
& $adb shell am force-stop $pkg | Out-Null
Start-Sleep -Milliseconds 500
& $adb logcat -c
Write-Host '[stage24.31.1] Starting a fresh process with the same app-private profile...'
& $adb shell am start -n $component
if ($LASTEXITCODE -ne 0) { throw 'Could not relaunch Stage24 NativeActivity.' }
Write-Host '[stage24.31.1] Restart complete. Do not rebuild/reinstall before checking RUN B.'
