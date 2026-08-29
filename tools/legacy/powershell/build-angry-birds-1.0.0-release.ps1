param(
    [switch]$SkipAuditBuild,
    [switch]$SkipSourceArchive
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$version = '1.0.0'
$versionCode = '1000000'
$auditPackage = 'dev.angryarm64.stage24'
$releasePackage = 'dev.angryarm64.angrybirds'
$alias = 'angry-birds-release'
$passEnvName = 'ANGRY_BIRDS_RELEASE_STOREPASS'
$privateRoot = Join-Path $env:USERPROFILE '.angry-arm64\signing'
$keyPath = Join-Path $privateRoot 'angry-birds-release.p12'
$certPrivate = Join-Path $privateRoot 'angry-birds-release-cert.pem'
$dist = Join-Path $root 'dist\1.0.0'
$public = Join-Path $dist 'release'
$audit = Join-Path $dist 'audit'
$profileBackup = Join-Path $audit 'profile-backup'
$work = Join-Path $dist '_work'
foreach ($d in @($public,$audit,$profileBackup,$work,$privateRoot)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

$python = (Get-Command python -ErrorAction Stop).Source
$keytool = Get-Command keytool -ErrorAction Stop
$sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$buildTools = Get-ChildItem (Join-Path $sdk 'build-tools') -Directory | Sort-Object @{ Expression = { try { [version]$_.Name } catch { [version]'0.0.0' } }} -Descending | Select-Object -First 1
if (!$buildTools) { throw 'Android build-tools not found.' }
$aapt = Join-Path $buildTools.FullName 'aapt.exe'
$apksigner = Join-Path $buildTools.FullName 'apksigner.bat'
$adb = Join-Path $sdk 'platform-tools\adb.exe'
$ndk = Get-ChildItem (Join-Path $sdk 'ndk') -Directory | Sort-Object @{ Expression = { try { [version]$_.Name } catch { [version]'0.0.0' } }} -Descending | Select-Object -First 1
if (!$ndk) { throw 'Android NDK not found.' }
$readelf = Join-Path $ndk.FullName 'toolchains\llvm\prebuilt\windows-x86_64\bin\llvm-readelf.exe'
foreach ($tool in @($aapt,$apksigner,$adb,$readelf)) { if (!(Test-Path $tool)) { throw "Required tool missing: $tool" } }

function Convert-SecureToPlain([Security.SecureString]$Secure) {
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function Read-ReleasePassword([bool]$Creating) {
    $one = Read-Host 'Release keystore password' -AsSecureString
    $plain = Convert-SecureToPlain $one
    if ($plain.Length -lt 16) { throw 'Use at least 16 characters for the release keystore password.' }
    if ($Creating) {
        $two = Read-Host 'Confirm release keystore password' -AsSecureString
        $plain2 = Convert-SecureToPlain $two
        if ($plain -cne $plain2) { throw 'Release keystore passwords do not match.' }
    }
    return $plain
}

function Test-AdbDevice {
    if (!(Test-Path -LiteralPath $adb)) { return $false }
    $savedPreference = $ErrorActionPreference
    try {
        # Windows PowerShell converts native stderr into an ErrorRecord when
        # ErrorActionPreference=Stop.  A disconnected phone is not a build
        # failure, so probe quietly and decide from adb's exit code + stdout.
        $ErrorActionPreference = 'SilentlyContinue'
        $state = @(& $adb get-state 2>$null | ForEach-Object { "$_" })
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedPreference
    }
    return ($exitCode -eq 0 -and (($state -join "`n").Trim() -eq 'device'))
}

Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' ANGRY BIRDS ARM64 1.0.0 - RELEASE ENGINEERING' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host 'Private signing material stays under ~/.angry-arm64/signing and is NEVER copied into dist/source archives.' -ForegroundColor Yellow
Write-Host ''

# Static fail-closed contract before touching signing/build output.
$contract = Join-Path $audit 'stage24.49.1-release-engineering-contract.txt'
$contractLines = @(& $python (Join-Path $root 'tools\stage24490_release_engineering_contract.py') $root 2>&1 | ForEach-Object { "$_" })
$contractExit = $LASTEXITCODE
$contractLines | Set-Content -Encoding UTF8 $contract
$contractLines | ForEach-Object { Write-Host $_ }
if ($contractExit -ne 0) { throw "Stage24.49.1 static release contract failed report=$contract" }

$creatingKey = !(Test-Path -LiteralPath $keyPath)
$plainPass = Read-ReleasePassword $creatingKey
[Environment]::SetEnvironmentVariable($passEnvName, $plainPass, 'Process')
try {
    if ($creatingKey) {
        Write-Host "[release-key] Creating permanent release key: $keyPath" -ForegroundColor Cyan
        & $keytool.Source -genkeypair -noprompt -keystore $keyPath -storetype PKCS12 -alias $alias -keyalg RSA -keysize 4096 -sigalg SHA256withRSA -validity 36500 -dname 'CN=Angry Birds ARM64 Release,OU=Release,O=Angry ARM64 Reconstruction' '-storepass:env' $passEnvName '-keypass:env' $passEnvName
        if ($LASTEXITCODE -ne 0) { throw 'Release key generation failed.' }
    } else {
        Write-Host "[release-key] Reusing permanent release key: $keyPath" -ForegroundColor Cyan
    }

    & $keytool.Source -list -v -keystore $keyPath -storetype PKCS12 -alias $alias '-storepass:env' $passEnvName | Set-Content -Encoding UTF8 (Join-Path $audit 'release-key-certificate-full.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Release keystore password/alias verification failed.' }
    & $keytool.Source -exportcert -rfc -keystore $keyPath -storetype PKCS12 -alias $alias '-storepass:env' $passEnvName -file $certPrivate
    if ($LASTEXITCODE -ne 0) { throw 'Release public certificate export failed.' }
    Copy-Item $certPrivate (Join-Path $public 'SIGNING-CERTIFICATE.pem') -Force

    # Preserve the historical development profile before the final audit build.
    if (Test-AdbDevice) {
        foreach ($leaf in @('settings.lua','highscores.lua')) {
            $dst = Join-Path $profileBackup $leaf
            try {
                & $adb exec-out run-as $auditPackage cat "files/stage24/appdata/$leaf" 2>$null | Set-Content -Encoding UTF8 $dst
                if ((Test-Path $dst) -and (Get-Item $dst).Length -gt 0) { Write-Host "[profile] backed up $leaf -> $dst" }
            } catch { }
        }
    }

    $build = Join-Path $root 'build-stage24-live-surface-touch-arm64.ps1'
    $out = Join-Path $root 'stage24-output'

    if (-not $SkipAuditBuild) {
        Write-Host ''
        Write-Host '[1/2] Building fully-audited development envelope...' -ForegroundColor Cyan
        & $build -BuildFlavor Audit -SkipInstall
        if ($LASTEXITCODE -ne 0) { throw "Audited build failed exit=$LASTEXITCODE" }
        $auditApkSrc = Join-Path $out 'angry-arm64-stage24-audited.apk'
        $auditApk = Join-Path $audit 'Angry-Birds-1.0.0-AUDITED-stage24-arm64-v8a.apk'
        Copy-Item $auditApkSrc $auditApk -Force
    } else {
        $auditApk = Join-Path $audit 'Angry-Birds-1.0.0-AUDITED-stage24-arm64-v8a.apk'
        if (!(Test-Path $auditApk)) { throw 'SkipAuditBuild requested but audited APK is missing in dist.' }
    }

    Write-Host ''
    Write-Host '[2/2] Building final non-debuggable release envelope with permanent key...' -ForegroundColor Cyan
    & $build -BuildFlavor Release -ReleaseKeystore $keyPath -ReleaseAlias $alias -ReleasePasswordEnv $passEnvName -SkipInstall
    if ($LASTEXITCODE -ne 0) { throw "Release build failed exit=$LASTEXITCODE" }
    $releaseApkSrc = Join-Path $out 'Angry-Birds-1.0.0-arm64-v8a.apk'
    $releaseApk = Join-Path $public 'Angry-Birds-1.0.0-arm64-v8a.apk'
    Copy-Item $releaseApkSrc $releaseApk -Force

    # Hard proof that release packaging did not change the reconstructed engine.
    $eqReport = Join-Path $audit 'native-payload-equivalence.txt'
    $eqLines = @(& $python (Join-Path $root 'tools\stage24490_compare_native_payload.py') $auditApk $releaseApk 2>&1 | ForEach-Object { "$_" })
    $eqExit = $LASTEXITCODE; $eqLines | Set-Content -Encoding UTF8 $eqReport
    if ($eqExit -ne 0) { throw "Audit/release native payloads differ report=$eqReport" }

    # 16 KB ELF page-size future-proofing gate.
    $releaseSo = Join-Path $work 'libangryarm64-release.so'
    & $python (Join-Path $root 'tools\stage24490_extract_native.py') $releaseApk $releaseSo
    if ($LASTEXITCODE -ne 0) { throw 'Could not extract release native library.' }
    $elfReport = Join-Path $audit 'elf-16k-page-size-audit.txt'
    $elfLines = @(& $python (Join-Path $root 'tools\stage24490_elf_16k_audit.py') $readelf $releaseSo 2>&1 | ForEach-Object { "$_" })
    $elfExit = $LASTEXITCODE; $elfLines | Set-Content -Encoding UTF8 $elfReport
    if ($elfExit -ne 0) { throw "16 KB ELF alignment gate failed report=$elfReport" }

    # Installed-facing APK metadata and release certificate.
    $badging = Join-Path $audit 'release-aapt-badging.txt'
    @(& $aapt dump badging $releaseApk 2>&1) | Set-Content -Encoding UTF8 $badging
    $badgingText = Get-Content $badging -Raw
    if ($badgingText -notmatch "package: name='dev\.angryarm64\.angrybirds'.*versionCode='1000000'.*versionName='1\.0\.0'") { throw "Release package/version badging mismatch report=$badging" }
    if ($badgingText -notmatch "application: label='Angry Birds'") { throw "Release label mismatch report=$badging" }
    if ($badgingText -match 'application-debuggable') { throw "Release APK is still debuggable report=$badging" }

    $certReport = Join-Path $public 'SIGNING-CERTIFICATE.txt'
    @(& $apksigner verify --verbose --print-certs $releaseApk 2>&1) | Set-Content -Encoding UTF8 $certReport
    if ($LASTEXITCODE -ne 0) { throw 'Release APK signature verification failed.' }
    $certText = Get-Content $certReport -Raw
    if ($certText -notmatch 'Angry Birds ARM64 Release') { throw 'Release APK is not signed by the expected release identity.' }
    if ($certText -match 'Android Debug') { throw 'Debug certificate leaked into final release.' }

    if (-not $SkipSourceArchive) {
        $sourceZip = Join-Path $public 'Angry-Birds-ARM64-1.0.0-source.zip'
        & $python (Join-Path $root 'tools\stage24490_make_source_archive.py') $root $sourceZip
        if ($LASTEXITCODE -ne 0) { throw 'Clean source archive creation failed.' }
    }

    $releaseNotes = @"
# Angry Birds ARM64 1.0.0

Native ARM64 reconstruction of the Angry Birds Classic 1.4.2 Android runtime.

- Package: `$releasePackage
- Version: $version (`$versionCode=$versionCode)
- ABI: arm64-v8a only
- Application label: Angry Birds
- Release APK: Angry-Birds-1.0.0-arm64-v8a.apk
- Signing: permanent local release key; see SIGNING-CERTIFICATE.txt / .pem
- Runtime lineage: byte-identical native payload between the audited Stage24 build and the non-debuggable release envelope.
- Physics: Box2D/Rovio fidelity path retains `-ffp-contract=off` and all previously closed numerical contracts.
- Android lifecycle: Recents/Surface recreation preserves the live Lua + Box2D engine.

The source archive intentionally excludes proprietary Angry Birds assets and all private signing material. The locally-built APK uses assets sourced from the user's own original extraction at build time. Redistribution of binary/assets should only be done where the uploader has the necessary rights.
"@
    $releaseNotes | Set-Content -Encoding UTF8 (Join-Path $public 'RELEASE-NOTES.md')

    $prov = New-Object System.Collections.Generic.List[string]
    $prov.Add('ANGRY_BIRDS_ARM64_1_0_0_BUILD_PROVENANCE 1')
    $prov.Add(('generated=' + (Get-Date).ToString('o')))
    $prov.Add("package=$releasePackage")
    $prov.Add("versionName=$version")
    $prov.Add("versionCode=$versionCode")
    $prov.Add('abi=arm64-v8a')
    $prov.Add(('runtime_cpp_sha256=' + (Get-FileHash (Join-Path $root 'stage24_live_surface.cpp') -Algorithm SHA256).Hash.ToLower()))
    $prov.Add(('cmake_sha256=' + (Get-FileHash (Join-Path $root 'CMakeLists.txt') -Algorithm SHA256).Hash.ToLower()))
    $prov.Add(('release_apk_sha256=' + (Get-FileHash $releaseApk -Algorithm SHA256).Hash.ToLower()))
    $prov.Add(('audit_apk_sha256=' + (Get-FileHash $auditApk -Algorithm SHA256).Hash.ToLower()))
    $prov.Add('native_payload_equivalence=PASS')
    $prov.Add('elf_16k_alignment=PASS')
    $prov.Add('release_debuggable=false')
    $prov.Add('release_signing=PASS')
    $prov | Set-Content -Encoding UTF8 (Join-Path $public 'BUILD-PROVENANCE.txt')

    @"
# Upload layout

`release/` contains the candidate public-facing artifacts. It contains no private key or password.

`audit/` is the forensic companion: audited APK, native equivalence proof, page-size proof, preflight reports, and a best-effort backup of the historical Stage24 profile.

The permanent private key lives only at:
`$keyPath

Back that file up offline. Do not place it in Git, cloud-public folders, release ZIPs, or screenshots. The public PEM certificate is safe to share.
"@ | Set-Content -Encoding UTF8 (Join-Path $dist 'README-FIRST.md')

    # Hash every public artifact after all files are present.
    $hashLines = foreach ($f in Get-ChildItem $public -File | Sort-Object Name) {
        $h = (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower()
        "$h  $($f.Name)"
    }
    $hashLines | Set-Content -Encoding ASCII (Join-Path $public 'SHA256SUMS.txt')

    Write-Host ''
    Write-Host 'RELEASE PACKAGING PASS' -ForegroundColor Green
    Write-Host "Release folder: $public"
    Write-Host "Audit folder:   $audit"
    Write-Host "Private key:    $keyPath" -ForegroundColor Yellow
    Write-Host 'DO NOT upload the private key.' -ForegroundColor Yellow
}
finally {
    [Environment]::SetEnvironmentVariable($passEnvName, $null, 'Process')
    $plainPass = $null
}
