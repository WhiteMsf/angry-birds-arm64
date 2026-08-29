param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ''
Write-Host '=== Stage24.47.6 Android lifecycle / multitarefa resume ===' -ForegroundColor Cyan
Write-Host 'Goal: Recents must pause/resume the SAME Lua + Box2D engine.'
Write-Host 'Expected: no second splash, no return to main menu unless that was already the current page.'
Write-Host ''

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
    if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }
}

Write-Host ''
Write-Host 'No telefone:' -ForegroundColor Yellow
Write-Host '  1. Espere o jogo terminar o splash e entrar normalmente.'
Write-Host '  2. Entre em qualquer fase e deixe a cena claramente reconhecivel.'
Write-Host '  3. Abra o menu de multitarefa / apps recentes do Android.'
Write-Host '  4. Espere 2-3 segundos e toque no Angry Birds para voltar.'
Write-Host '  5. PASS visual: volta exatamente para a mesma fase/tela, sem splash e sem menu principal resetado.'
Write-Host '  6. Faça o ciclo multitarefa -> voltar MAIS UMA VEZ na mesma sessão.'
Write-Host '  7. Se aparecer splash, tela preta permanente, crash ou reset de estado, pare ali.'
Write-Host ''
Read-Host '[stage24.47.6] Depois dos dois ciclos (ou primeiro erro), pressione ENTER'

& powershell -ExecutionPolicy Bypass -File .\pull-stage24-live-log.ps1
if ($LASTEXITCODE -ne 0) { throw "diagnostic pull failed exit=$LASTEXITCODE" }

Write-Host ''
Write-Host 'Lifecycle diagnostics collected.' -ForegroundColor Green
Write-Host ' Key reports:'
Write-Host '  - stage24.47.6-native-jni-lifecycle-audit.txt'
Write-Host '  - stage24.47.6-android-lifecycle-contract.txt'
Write-Host '  - stage24.47.6-android-lifecycle-runtime.txt'
