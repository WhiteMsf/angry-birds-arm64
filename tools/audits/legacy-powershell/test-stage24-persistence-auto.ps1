param(
    [switch]$SkipBuild,
    [int]$SaveTimeoutMinutes = 20,
    [int]$RestartTimeoutSeconds = 60
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$adb = Join-Path $sdk 'platform-tools\adb.exe'
$build = Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1'
$pull = Join-Path $root 'pull-stage24-live-log.ps1'
$out = Join-Path $root 'stage24-output'
$pkg = 'dev.angryarm64.stage24'
$component = 'dev.angryarm64.stage24/android.app.NativeActivity'

if (!(Test-Path $adb)) { throw 'adb.exe not found.' }
if (!(Test-Path $build)) { throw 'build script not found.' }
if (!(Test-Path $pull)) { throw 'pull script not found.' }
New-Item -ItemType Directory -Force -Path $out | Out-Null

$device = @(& $adb devices | Select-String '\tdevice$')
if (!$device) { throw 'No authorized Android device found.' }

function Get-NativeStdout {
    $lines = @(& $adb exec-out run-as $pkg cat 'files/stage24/stage24-native-stdout.log' 2>$null)
    if ($LASTEXITCODE -ne 0) { return '' }
    return ($lines -join "`n")
}

function Get-NativeStderr {
    $lines = @(& $adb exec-out run-as $pkg cat 'files/stage24/stage24-native-stderr.log' 2>$null)
    if ($LASTEXITCODE -ne 0) { return '' }
    return ($lines -join "`n")
}

function Get-ProfileInfo([string]$Leaf) {
    $remote = "files/stage24/appdata/$Leaf"
    $probe = @(& $adb shell run-as $pkg sh -c "if [ -f '$remote' ]; then wc -c '$remote'; sha256sum '$remote' 2>/dev/null || true; else echo MISSING '$remote'; fi" 2>$null)
    $text = ($probe -join "`n")
    $exists = $text -notmatch '(?m)^MISSING\s'
    $bytes = -1L
    $sha = ''
    if ($exists) {
        $mBytes = [regex]::Match($text, '(?m)^\s*(\d+)\s+files/stage24/appdata/')
        if ($mBytes.Success) { $bytes = [int64]$mBytes.Groups[1].Value }
        $mSha = [regex]::Match($text, '(?im)^([0-9a-f]{64})\s+')
        if ($mSha.Success) { $sha = $mSha.Groups[1].Value.ToLowerInvariant() }
    }
    return [pscustomobject]@{
        Leaf = $Leaf
        Remote = $remote
        Exists = $exists
        Bytes = $bytes
        Sha256 = $sha
        Raw = $text
    }
}

function Copy-RemoteProfile([string]$Leaf, [string]$Destination) {
    $remote = "files/stage24/appdata/$Leaf"
    $body = @(& $adb exec-out run-as $pkg cat $remote 2>$null)
    if ($LASTEXITCODE -eq 0 -and $body.Count -gt 0) {
        $body | Set-Content -Encoding UTF8 $Destination
        return $true
    }
    return $false
}

function Pull-And-Preserve([string]$Label) {
    Write-Host "[auto-persistence] Capturing $Label diagnostics..."
    & powershell -ExecutionPolicy Bypass -File $pull
    if ($LASTEXITCODE -ne 0) { throw "pull-stage24-live-log.ps1 failed during $Label." }
    $bundle = Join-Path $out 'stage24-diagnostics.zip'
    if (!(Test-Path $bundle)) { throw "Diagnostic ZIP missing during $Label." }
    $copy = Join-Path $out ("stage24.31.1-auto-$Label-diagnostics.zip")
    Copy-Item $bundle $copy -Force
    return $copy
}

function Wait-ForRunAWrites {
    $deadline = (Get-Date).AddMinutes($SaveTimeoutMinutes)
    $last = ''
    while ((Get-Date) -lt $deadline) {
        $stdout = Get-NativeStdout
        $settings = $stdout -match "\[stage24\.31\.1-persistence\] WRITE .*file='settings\.lua'.*action=PASS"
        $highscores = $stdout -match "\[stage24\.31\.1-persistence\] WRITE .*file='highscores\.lua'.*action=PASS"
        $fail = $stdout -match "\[stage24\.31\.1-persistence\] (WRITE|VALIDATE).*action=FAIL"
        if ($fail) { throw 'Persistence write/validation failure appeared in native stdout.' }
        $status = "settings=" + $(if ($settings) {'PASS'} else {'waiting'}) + " highscores=" + $(if ($highscores) {'PASS'} else {'waiting'})
        if ($status -ne $last) {
            Write-Host "[auto-persistence] RUN A $status"
            $last = $status
        }
        if ($settings -and $highscores) { return $stdout }
        Start-Sleep -Seconds 2
    }
    throw "Timed out after $SaveTimeoutMinutes minute(s) waiting for both profile writes. Complete 1-1 normally and return to the menus."
}

function Wait-ForRunBLoads {
    $deadline = (Get-Date).AddSeconds($RestartTimeoutSeconds)
    $last = ''
    while ((Get-Date) -lt $deadline) {
        $stdout = Get-NativeStdout
        $settings = $stdout -match "\[stage24\.31\.1-persistence\] LOAD file='settings\.lua'.*action=PASS_FROM_DISK"
        $highscores = $stdout -match "\[stage24\.31\.1-persistence\] LOAD file='highscores\.lua'.*action=PASS_FROM_DISK"
        $bad = $stdout -match "\[stage24\.31\.1-persistence\] LOAD .*action=(FAIL_KEEP_EXISTING_DEFAULT|MISSING_CLEAN_PROFILE)"
        if ($bad) { throw 'RUN B did not load both profiles from disk.' }
        $status = "settings=" + $(if ($settings) {'PASS_FROM_DISK'} else {'waiting'}) + " highscores=" + $(if ($highscores) {'PASS_FROM_DISK'} else {'waiting'})
        if ($status -ne $last) {
            Write-Host "[auto-persistence] RUN B $status"
            $last = $status
        }
        if ($settings -and $highscores) { return $stdout }
        Start-Sleep -Seconds 1
    }
    throw "Timed out after $RestartTimeoutSeconds second(s) waiting for PASS_FROM_DISK after restart."
}

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.1 - AUTOMATED SAVE / RESTART PERSISTENCE TEST'
Write-Host '============================================================'
Write-Host ''
Write-Host 'You only need to do ONE manual thing:'
Write-Host '  -> On the phone, enter Poached Eggs 1-1 and COMPLETE IT.'
Write-Host ''
Write-Host 'You do NOT need to pull logs, press Enter, restart the app, or toggle audio.'
Write-Host 'This script will detect both saves, capture RUN A, restart the process,'
Write-Host 'wait for PASS_FROM_DISK, capture RUN B, and print PASS/FAIL.'
Write-Host ''

if (!$SkipBuild) {
    Write-Host '[auto-persistence] Building/installing/launching v0.26.97b...'
    & powershell -ExecutionPolicy Bypass -File $build
    if ($LASTEXITCODE -ne 0) { throw 'Stage24 build/install failed.' }
} else {
    Write-Host '[auto-persistence] -SkipBuild selected; using the currently installed app.'
    & $adb logcat -c | Out-Null
    & $adb shell am force-stop $pkg | Out-Null
    Start-Sleep -Milliseconds 500
    & $adb shell am start -n $component | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not launch Stage24 NativeActivity.' }
}

Write-Host ''
Write-Host '[auto-persistence] App is running. Complete 1-1 on the phone; I am watching the save calls...'
$runAStdout = Wait-ForRunAWrites
Start-Sleep -Seconds 1

$settingsA = Get-ProfileInfo 'settings.lua'
$highscoresA = Get-ProfileInfo 'highscores.lua'
if (!$settingsA.Exists -or !$highscoresA.Exists) {
    throw 'RUN A logged successful writes but one or both profile files are missing.'
}

$runASettings = Join-Path $out 'stage24.31.1-auto-runA-settings.lua'
$runAHighscores = Join-Path $out 'stage24.31.1-auto-runA-highscores.lua'
[void](Copy-RemoteProfile 'settings.lua' $runASettings)
[void](Copy-RemoteProfile 'highscores.lua' $runAHighscores)
$runABundle = Pull-And-Preserve 'runA'

Write-Host ''
Write-Host '[auto-persistence] RUN A is saved. Restarting WITHOUT reinstall and WITHOUT clearing app data...'
& $adb shell am force-stop $pkg | Out-Null
Start-Sleep -Milliseconds 700
# Remove only diagnostic logs so RUN B cannot accidentally match RUN A markers.
& $adb shell run-as $pkg rm -f 'files/stage24/stage24-native-stdout.log' 'files/stage24/stage24-native-stderr.log' 2>$null | Out-Null
& $adb logcat -c | Out-Null
& $adb shell am start -n $component | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not start fresh RUN B process.' }

$runBStdout = Wait-ForRunBLoads
Start-Sleep -Seconds 1

$settingsB = Get-ProfileInfo 'settings.lua'
$highscoresB = Get-ProfileInfo 'highscores.lua'
if (!$settingsB.Exists -or !$highscoresB.Exists) {
    throw 'RUN B loaded from disk but one or both profile files are now missing.'
}

$runBSettings = Join-Path $out 'stage24.31.1-auto-runB-settings.lua'
$runBHighscores = Join-Path $out 'stage24.31.1-auto-runB-highscores.lua'
[void](Copy-RemoteProfile 'settings.lua' $runBSettings)
[void](Copy-RemoteProfile 'highscores.lua' $runBHighscores)
$runBBundle = Pull-And-Preserve 'runB'

$stderrB = Get-NativeStderr
$luaFault = ($runBStdout -match 'LUA ERROR|LIVE LUA FAIL') -or ($stderrB -match 'LUA ERROR|LIVE LUA FAIL')
if ($luaFault) { throw 'RUN B loaded the profile but a Lua fault was observed.' }

$settingsSame = ($settingsA.Sha256 -ne '' -and $settingsA.Sha256 -eq $settingsB.Sha256)
$highscoresSame = ($highscoresA.Sha256 -ne '' -and $highscoresA.Sha256 -eq $highscoresB.Sha256)

$report = Join-Path $out 'stage24.31.1-automated-persistence-test.txt'
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('ANGRY_STAGE24_31_1_AUTOMATED_PERSISTENCE_TEST 1')
$lines.Add(('generated=' + (Get-Date).ToString('o')))
$lines.Add('verdict=PASS')
$lines.Add('proof=RUN_A_WRITE_PASS + force-stop/start without reinstall/clear + RUN_B_PASS_FROM_DISK')
$lines.Add('')
$lines.Add("runA.settings bytes=$($settingsA.Bytes) sha256=$($settingsA.Sha256)")
$lines.Add("runA.highscores bytes=$($highscoresA.Bytes) sha256=$($highscoresA.Sha256)")
$lines.Add("runB.settings bytes=$($settingsB.Bytes) sha256=$($settingsB.Sha256) sameAsRunA=$settingsSame")
$lines.Add("runB.highscores bytes=$($highscoresB.Bytes) sha256=$($highscoresB.Sha256) sameAsRunA=$highscoresSame")
$lines.Add('note=hash equality is informational only; startup may legitimately rewrite settings later. PASS depends on PASS_FROM_DISK.')
$lines.Add('')
$lines.Add('--- RUN A persistence markers ---')
foreach ($line in ($runAStdout -split "`n")) {
    if ($line -match 'stage24\.31\.1-persistence') { $lines.Add($line) }
}
$lines.Add('')
$lines.Add('--- RUN B persistence markers ---')
foreach ($line in ($runBStdout -split "`n")) {
    if ($line -match 'stage24\.31\.1-persistence') { $lines.Add($line) }
}
$lines | Set-Content -Encoding UTF8 $report

$finalBundle = Join-Path $out 'stage24.31.1-automated-persistence-test.zip'
if (Test-Path $finalBundle) { Remove-Item $finalBundle -Force }
$finalFiles = New-Object System.Collections.Generic.List[string]
foreach ($p in @($report, $runABundle, $runBBundle, $runASettings, $runAHighscores, $runBSettings, $runBHighscores)) {
    if (Test-Path $p) { $finalFiles.Add($p) }
}
Compress-Archive -Path $finalFiles.ToArray() -DestinationPath $finalBundle -CompressionLevel Optimal -Force

Write-Host ''
Write-Host '============================================================'
Write-Host '                PERSISTENCE TEST: PASS'
Write-Host '============================================================'
Write-Host "RUN A settings:   $($settingsA.Bytes) bytes  $($settingsA.Sha256)"
Write-Host "RUN A highscores: $($highscoresA.Bytes) bytes  $($highscoresA.Sha256)"
Write-Host "RUN B settings:   PASS_FROM_DISK  sameHash=$settingsSame"
Write-Host "RUN B highscores: PASS_FROM_DISK  sameHash=$highscoresSame"
Write-Host ''
Write-Host 'Final automated evidence bundle:'
Write-Host "  $finalBundle"
Write-Host ''
Write-Host 'Upload ONLY that ZIP to ChatGPT.'
Write-Host ''
