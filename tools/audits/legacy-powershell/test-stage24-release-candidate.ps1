param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$out = Join-Path $root 'stage24-output'
$pull = Join-Path $root 'pull-stage24-live-log.ps1'
$python = (Get-Command python -ErrorAction Stop).Source

Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' Stage24.48.0 - RELEASE CANDIDATE / REAL-PROFILE REGRESSION'
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'This pass DOES NOT clear settings.lua/highscores.lua.' -ForegroundColor Green
Write-Host 'Goal: prove the v0.26.157 engine baseline still behaves vanilla as one integrated app.'
Write-Host ''

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File .\build-stage24-live-surface-touch-arm64.ps1
    if ($LASTEXITCODE -ne 0) { throw "build failed exit=$LASTEXITCODE" }
}

Write-Host ''
Write-Host 'No telefone, faça este sweep (nao precisa zerar as fases):' -ForegroundColor Yellow
Write-Host '  1. Cold boot: splash -> menu principal normal; navegue pelos episodios/level selection.'
Write-Host '  2. Entre numa fase simples. Puxe um passaro, reinicie a fase pelo pause e continue.'
Write-Host '  3. Pause/resume pelo menu do jogo; confirme audio e animacoes voltando normalmente.'
Write-Host '  4. Teste pelo menos uma fase com habilidade especial (Yellow/Bomb/White/Boomerang; escolha as que quiser).'
Write-Host '  5. Entre em 8-3 e force algumas interacoes da estrutura de borracha/trampolim.'
Write-Host '  6. Abra um Golden Egg que ja esteja liberado e interaja normalmente.'
Write-Host '  7. Dentro de uma fase, abra a multitarefa e volte DUAS vezes; deve manter exatamente a mesma engine/tela.'
Write-Host '  8. Faça uma derrota/retry OU uma vitoria/next/replay — qualquer fluxo de resultado que seja rapido pra voce.'
Write-Host '  9. Volte aos menus e mexa por alguns segundos. Se tudo parece vanilla, terminou.'
Write-Host ''
Write-Host 'Se aparecer splash inesperado, reset, tela preta persistente, crash, fisica estranha ou audio quebrado, pare no primeiro sintoma.' -ForegroundColor DarkYellow
Write-Host ''
Read-Host '[stage24.48.0] Quando terminar o sweep (ou achar o primeiro erro), pressione ENTER'

# First pull gives the runtime auditor local copies of stdout/stderr/logcat.
& powershell -ExecutionPolicy Bypass -File $pull
if ($LASTEXITCODE -ne 0) { throw "diagnostic pull failed exit=$LASTEXITCODE" }

$runtime = Join-Path $out 'stage24.48.0-release-candidate-runtime.txt'
$stdout = Join-Path $out 'stage24-native-stdout.log'
$stderr = Join-Path $out 'stage24-native-stderr.log'
$logcat = Join-Path $out 'stage24-live-logcat.txt'
$lines = @(& $python (Join-Path $root 'tools\stage24480_runtime_smoke_audit.py') $stdout $stderr $logcat 2>&1 | ForEach-Object { "$_" })
$rc = $LASTEXITCODE
$lines | Set-Content -Encoding UTF8 $runtime
Write-Host ''
$lines | ForEach-Object { Write-Host $_ }

# Rebuild the bundle once so the Stage24.48.0 runtime report is included.
& powershell -ExecutionPolicy Bypass -File $pull
if ($LASTEXITCODE -ne 0) { throw "final diagnostic pull failed exit=$LASTEXITCODE" }

Write-Host ''
if ($rc -eq 0) {
    Write-Host 'Stage24.48.0 runtime safety gate PASS. Visual/oracle verdict is yours.' -ForegroundColor Green
} else {
    Write-Host 'Stage24.48.0 runtime safety gate FAIL. Send the diagnostics ZIP.' -ForegroundColor Red
}
Write-Host 'Diagnostic ZIP: stage24-output\stage24-diagnostics.zip'
