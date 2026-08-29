$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$adb = Join-Path $sdk 'platform-tools\adb.exe'
if (!(Test-Path $adb)) { throw "adb not found: $adb" }

Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' ANGRY BIRDS ARM64 1.0.0 - FINAL ACCEPTANCE' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Phase A builds BOTH envelopes: audited Stage24 + final release, signs release with the permanent key, proves identical native payloads, and prepares dist/1.0.0.'
Write-Host ''
& (Join-Path $root 'build-angry-birds-1.0.0-release.ps1')
if ($LASTEXITCODE -ne 0) { throw "release engineering failed exit=$LASTEXITCODE" }

$auditApk = Join-Path $root 'dist\1.0.0\audit\Angry-Birds-1.0.0-AUDITED-stage24-arm64-v8a.apk'
$releaseApk = Join-Path $root 'dist\1.0.0\release\Angry-Birds-1.0.0-arm64-v8a.apk'
$auditPkg = 'dev.angryarm64.stage24'
$releasePkg = 'dev.angryarm64.angrybirds'

Write-Host ''
Write-Host 'PHASE B - EXISTING-PROFILE AUDITED REGRESSION' -ForegroundColor Cyan
& $adb install -r $auditApk
if ($LASTEXITCODE -ne 0) { throw 'Could not install audited envelope over Stage24.' }
& $adb shell am force-stop $auditPkg | Out-Null
& $adb logcat -c
& $adb shell am start -n "$auditPkg/android.app.NativeActivity" | Out-Null
Write-Host 'No telefone, faça o sweep curto:' -ForegroundColor Yellow
Write-Host '  1. Abra uma fase simples e jogue normalmente.'
Write-Host '  2. Teste uma habilidade especial qualquer.'
Write-Host '  3. Vá em 8-3 e mexa na estrutura de borracha.'
Write-Host '  4. Abra um Golden Egg já liberado.'
Write-Host '  5. Pause/resume e abra multitarefa duas vezes dentro de uma fase.'
Write-Host '  6. Faça uma vitória OU derrota/retry e volte aos menus.'
Read-Host 'Se tudo estiver vanilla, pressione ENTER'

# Reuse the giant diagnostic pull on the debuggable audited package.
& (Join-Path $root 'pull-stage24-live-log.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Audited diagnostic pull failed.' }
$diag = Join-Path $root 'stage24-output\stage24-diagnostics.zip'
if (Test-Path $diag) { Copy-Item $diag (Join-Path $root 'dist\1.0.0\audit\stage24-diagnostics-final.zip') -Force }

Write-Host ''
Write-Host 'PHASE C - CLEAN FINAL RELEASE PROFILE' -ForegroundColor Cyan
Write-Host 'The release uses a different final package, so it installs side-by-side and starts clean without touching the historical Stage24 save.'
& $adb install -r $releaseApk
if ($LASTEXITCODE -ne 0) { throw 'Could not install final release APK.' }
& $adb shell am force-stop $releasePkg | Out-Null
& $adb logcat -c
& $adb shell am start -n "$releasePkg/android.app.NativeActivity" | Out-Null
Write-Host 'Agora teste a experiência de usuário novo:' -ForegroundColor Yellow
Write-Host '  1. Cold boot: splash/intro/menu corretos.'
Write-Host '  2. Entre no 1-1; tutorial deve aparecer como perfil limpo.'
Write-Host '  3. Complete o 1-1 e confirme resultado/estrelas/progressão.'
Write-Host '  4. Dentro da próxima fase, abra multitarefa e volte: sem splash/reset.'
Write-Host '  5. Vá para Home, volte pelo ícone Angry Birds: deve resumir corretamente se o processo estiver vivo.'
Write-Host '  6. Confirme nome Angry Birds, ícone original e áudio.'
Read-Host 'Depois de completar 1-1 + testar multitarefa, pressione ENTER; o script fará um force-stop real'

& $adb shell am force-stop $releasePkg | Out-Null
Start-Sleep -Seconds 1
& $adb shell am start -n "$releasePkg/android.app.NativeActivity" | Out-Null
Write-Host 'O app foi encerrado de verdade e reaberto. Confirme que o progresso do 1-1 persistiu.' -ForegroundColor Yellow
Read-Host 'Se o save persistiu e tudo continua certo, pressione ENTER para fechar a homologação'

$releaseLog = Join-Path $root 'dist\1.0.0\audit\release-final-logcat.txt'
@(& $adb logcat -d 2>&1) | Set-Content -Encoding UTF8 $releaseLog
$bad = Select-String -Path $releaseLog -Pattern 'FATAL EXCEPTION|Fatal signal|SIGSEGV|SIGABRT|LIVE LUA FAIL|LUA ERROR|GPU frame FAIL|RuntimeException' -ErrorAction SilentlyContinue
if ($bad) {
    $bad | ForEach-Object { Write-Host $_.Line -ForegroundColor Red }
    throw "Final release log safety gate found fatal markers: $releaseLog"
}

$final = Join-Path $root 'dist\1.0.0\audit\FINAL-ACCEPTANCE.txt'
@(
    'ANGRY_BIRDS_ARM64_1_0_0_FINAL_ACCEPTANCE 1',
    ('completed=' + (Get-Date).ToString('o')),
    'audited_existing_profile=USER_PASS',
    'clean_release_profile=USER_PASS',
    'fatal_log_scan=PASS',
    'native_payload_equivalence=PASS_FROM_RELEASE_ENGINEERING',
    'release_signing=PASS_FROM_RELEASE_ENGINEERING',
    'release_debuggable=false',
    'verdict=PASS_1_0_0'
) | Set-Content -Encoding UTF8 $final

Write-Host ''
Write-Host '============================================================' -ForegroundColor Green
Write-Host ' ANGRY BIRDS ARM64 1.0.0 - FINAL ACCEPTANCE PASS' -ForegroundColor Green
Write-Host '============================================================' -ForegroundColor Green
Write-Host 'dist\1.0.0\release = artifacts for future upload'
Write-Host 'dist\1.0.0\audit   = forensic/audited companion'
