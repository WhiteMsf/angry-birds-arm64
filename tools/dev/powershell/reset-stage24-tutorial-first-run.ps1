$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$adb = $null
$candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'),
    'adb.exe', 'adb'
)
foreach ($c in $candidates) {
    try {
        if (Test-Path $c) { $adb = $c; break }
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) { $adb = $cmd.Source; break }
    } catch {}
}
if (-not $adb) { throw 'adb not found' }
$pkg = 'dev.angryarm64.stage24'
Write-Host '[stage24.31.2] Resetting ONLY settings.lua so first-run tutorial can be tested...'
& $adb shell am force-stop $pkg | Out-Null
& $adb shell run-as $pkg rm -f files/stage24/appdata/settings.lua
if ($LASTEXITCODE -ne 0) { throw 'Could not remove app-private settings.lua with run-as.' }
Write-Host '[stage24.31.2] settings.lua removed. highscores.lua was left untouched.'
& $adb shell am start -n "$pkg/android.app.NativeActivity" | Out-Null
Write-Host '[stage24.31.2] App started. Navigate to Poached Eggs 1-1; the Red tutorial should appear.'
