$ErrorActionPreference = 'Stop'

$python = Get-Command python -ErrorAction SilentlyContinue

if ($python) {
    & $python.Source (Join-Path $PSScriptRoot 'build.py') @args
    exit $LASTEXITCODE
}

$py = Get-Command py -ErrorAction SilentlyContinue

if ($py) {
    & $py.Source -3 (Join-Path $PSScriptRoot 'build.py') @args
    exit $LASTEXITCODE
}

throw 'Python 3 not found.'