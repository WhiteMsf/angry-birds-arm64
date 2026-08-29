$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.41.1 - MIGHTY HOAX 5-11 -> 5-21 PAGE CLOSURE'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Validated baseline retained:'
Write-Host '  - Poached Eggs 1-1..3-21 complete'
Write-Host '  - Mighty Hoax 4-1..4-21 complete'
Write-Host '  - Mighty Hoax 5-1..5-10 complete'
Write-Host '  - Theme5 + checkForLuaFile + polygon contracts runtime-proven'
Write-Host ''
Write-Host 'This pass is page-sized transport only. Stock Lua owns Next/completion.'
Write-Host 'Mighty Hoax page 2 remaining map:'
Write-Host '  5-11 LevelP2_86   5-12 LevelP2_74   5-13 LevelP2_115  5-14 LevelP2_98'
Write-Host '  5-15 LevelP2_71   5-16 LevelP2_72   5-17 LevelP2_87   5-18 LevelP2_93'
Write-Host '  5-19 LevelP2_67   5-20 LevelP2_97   5-21 LevelP2_90'
Write-Host ''
Write-Host 'Existing save/profile is preserved.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Enter Mighty Hoax page 2 and open 5-11 directly. Do NOT replay validated levels.'
Write-Host '  2. Play 5-11 through 5-21 using stock Next.'
Write-Host '  3. Finish 5-21 and wait for the normal result screen.'
Write-Host '  4. Press stock Next exactly once and let any completion/selection transition settle.'
Write-Host '  5. Stop immediately on first crash, Lua error, missing object/scene, frozen load, or file-not-found.'
Write-Host ''
Read-Host '[stage24.41.1] When 5-11 -> 5-21 + one stock Next are done, press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.41.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.41.1-mighty-hoax-5-21-closure-runtime.txt'
Write-Host '============================================================'
