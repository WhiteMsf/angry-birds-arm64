$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.4a - ORIGINAL EGL_IMAGE / RENDERBATCHER AUDIT'
Write-Host '============================================================'
Write-Host 'No gameplay interaction is needed.'
Write-Host 'This will build/install only so the normal ARMv7 preflight can recover the'
Write-Host 'original image-subrect backend. Then it packages the report automatically.'
Write-Host ''

powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/audit failed: $LASTEXITCODE" }

$out = Join-Path $root 'stage24-output'
$report = Join-Path $out 'stage24.31.4a-original-egl-image-draw-contract.txt'
if (!(Test-Path $report)) { throw "Audit report not found: $report" }

$zip = Join-Path $out 'stage24.31.4a-original-egl-image-audit.zip'
if (Test-Path $zip) { Remove-Item $zip -Force }
$items = New-Object System.Collections.Generic.List[string]
$items.Add($report)
foreach ($n in @(
    'stage24.31.3-ui-microfidelity-contract.txt',
    'stage24.31.4-ui-seam-fidelity-contract.txt',
    'stage24-initial-logcat.txt'
)) {
    $p = Join-Path $out $n
    if (Test-Path $p) { $items.Add($p) }
}
Compress-Archive -Path $items.ToArray() -DestinationPath $zip -CompressionLevel Optimal -Force
Write-Host ''
Write-Host '[stage24.31.4a] Audit bundle ready:'
Write-Host "  $zip"
Write-Host 'Upload that ZIP to ChatGPT. No gameplay test is needed in this round.'
