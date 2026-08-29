$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.4b - ORIGINAL TEXTURE SAMPLING / BACKING AUDIT'
Write-Host '============================================================'
Write-Host 'No gameplay interaction is needed.'
Write-Host 'This recovers ARMv7 sampler state and texture-backing dimensions after'
Write-Host '24.31.4a proved that the original Image::draw does NOT use half-texel UVs.'
Write-Host ''
powershell -ExecutionPolicy Bypass -File (Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1')
if ($LASTEXITCODE -ne 0) { throw "Stage24 build/audit failed: $LASTEXITCODE" }
$out = Join-Path $root 'stage24-output'
$report = Join-Path $out 'stage24.31.4b-original-texture-sampling-backing-contract.txt'
if (!(Test-Path $report)) { throw "Audit report not found: $report" }
$zip = Join-Path $out 'stage24.31.4b-original-texture-sampling-audit.zip'
if (Test-Path $zip) { Remove-Item $zip -Force }
$items = New-Object System.Collections.Generic.List[string]
foreach ($n in @(
 'stage24.31.4b-original-texture-sampling-backing-contract.txt',
 'stage24.31.4a-original-egl-image-draw-contract.txt',
 'stage24.31.4-ui-seam-fidelity-contract.txt',
 'stage24.31.3-ui-microfidelity-contract.txt'
)) {
 $p = Join-Path $out $n
 if (Test-Path $p) { $items.Add($p) }
}
Compress-Archive -Path $items.ToArray() -DestinationPath $zip -CompressionLevel Optimal -Force
Write-Host ''
Write-Host '[stage24.31.4b] Audit bundle ready:'
Write-Host "  $zip"
Write-Host 'Upload that ZIP to ChatGPT. No gameplay test is needed.'
