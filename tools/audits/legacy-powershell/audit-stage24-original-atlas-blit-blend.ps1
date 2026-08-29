$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
Write-Host ''
Write-Host '============================================================'
Write-Host ' Stage 24.31.4d - ORIGINAL ATLAS / BLIT / BLEND AUDIT'
Write-Host '============================================================'
Write-Host 'No gameplay interaction is needed.'
Write-Host 'This is read-only: it inspects the untouched ARMv7 renderer and the'
Write-Host 'original local atlas pixels around the exact UI sprite rectangles.'
Write-Host ''

$androidSdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
$ndkRoot = Join-Path $androidSdk 'ndk'
$ndk = Get-ChildItem -LiteralPath $ndkRoot -Directory -ErrorAction Stop | Sort-Object Name -Descending | Select-Object -First 1
$toolbin = Join-Path $ndk.FullName 'toolchains\llvm\prebuilt\windows-x86_64\bin'
$llvmNm = Join-Path $toolbin 'llvm-nm.exe'
$llvmObjdump = Join-Path $toolbin 'llvm-objdump.exe'
if (!(Test-Path $llvmNm) -or !(Test-Path $llvmObjdump)) { throw 'LLVM nm/objdump not found in Android NDK.' }
$python = (Get-Command python -ErrorAction Stop).Source
$angryRe = Join-Path $env:USERPROFILE 'Downloads\angry-re'
if (!(Test-Path $angryRe)) { throw "Original corpus root not found: $angryRe" }
$armv7 = Get-ChildItem -LiteralPath $angryRe -Recurse -File -Filter 'libangrybirds.so' -ErrorAction Stop |
    Sort-Object @{Expression={if ($_.FullName -match 'armeabi|armv7') {0} else {1}}}, FullName | Select-Object -First 1
if (!$armv7) { throw 'Original ARMv7 libangrybirds.so not found.' }
$images = Join-Path $angryRe 'assets\data\images\864x480'
if (!(Test-Path $images)) { throw "864x480 image corpus not found: $images" }
$out = Join-Path $root 'stage24-output'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$report = Join-Path $out 'stage24.31.4d-original-atlas-blit-blend-contract.txt'
& $python (Join-Path $root 'tools\stage24314d_atlas_blit_blend_contract.py') $llvmNm $llvmObjdump $armv7.FullName $images (Join-Path $root 'stage24_live_surface.cpp') *> $report
if ($LASTEXITCODE -ne 0) { throw "24.31.4d audit failed exit=$LASTEXITCODE report=$report" }
$zip = Join-Path $out 'stage24.31.4d-original-atlas-blit-blend-audit.zip'
if (Test-Path $zip) { Remove-Item $zip -Force }
$items = New-Object System.Collections.Generic.List[string]
$items.Add($report)
foreach ($n in @('stage24.31.4b-original-texture-sampling-backing-contract.txt','stage24.31.4a-original-egl-image-draw-contract.txt','stage24.31.4-ui-seam-fidelity-contract.txt')) {
  $p = Join-Path $out $n
  if (Test-Path $p) { $items.Add($p) }
}
Compress-Archive -Path $items.ToArray() -DestinationPath $zip -CompressionLevel Optimal -Force
Write-Host ''
Write-Host '[stage24.31.4d] Audit bundle ready:'
Write-Host "  $zip"
Write-Host 'Upload that ZIP to ChatGPT. No gameplay test is needed.'
