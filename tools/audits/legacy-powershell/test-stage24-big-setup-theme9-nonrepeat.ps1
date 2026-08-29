$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.46.1 - THE BIG SETUP THEME9 NON-REPEAT BACKGROUND'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Previous live discovery proved:'
Write-Host '  - 9-1 LevelP4_421 loads correctly with Theme9'
Write-Host '  - Theme9 uses 7 background layers + 2 foreground layers'
Write-Host '  - layers 3..6 are PARALLAX_CRANE_1..4 with repeat=false'
Write-Host '  - their exact original offsets are 565, 645, 755, 822'
Write-Host '  - the old renderer stopped fail-closed on repeat=false before gameplay frame 2065'
Write-Host ''
Write-Host 'This build reconstructs the exact ARMv7 GameLua::drawBackground repeat=false branch:'
Write-Host '  transformX = offset - trunc(offset)'
Write-Host '  drawX      = offset - (topLeftX * parallax) / layerScale'
Write-Host '  drawY      = -topLeftY / layerScale'
Write-Host '  drawSprite once (no horizontal tiling)'
Write-Host 'No Theme9-specific visual constants are added; blockTable.themes.theme9 remains authoritative.'
Write-Host ''

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/install failed: $LASTEXITCODE" }

Write-Host ''
Write-Host 'On the phone:'
Write-Host '  1. Enter The Big Setup 9-1 normally.'
Write-Host '  2. First priority: verify the construction/crane background renders and gameplay starts.'
Write-Host '  3. If 9-1 is clean, continue through 9-15 with stock Next.'
Write-Host '  4. Finish 9-15 and press stock Next once; let theme9Complete/next selection settle.'
Write-Host '  5. Stop immediately on first crash, scene corruption, missing resource, Lua error, or GPU failure.'
Write-Host ''
Read-Host '[stage24.46.1] When 9-1..9-15 are done (or first failure occurs), press ENTER'

& powershell -ExecutionPolicy Bypass -File (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 diagnostic pull failed: $LASTEXITCODE" }

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.46.1 capture complete.'
Write-Host ' Upload the newest stage24-diagnostics*.zip to ChatGPT.'
Write-Host ' Key report: stage24.46.1-nonrepeat-background-runtime.txt'
Write-Host '============================================================'
