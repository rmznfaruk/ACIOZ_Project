$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Sanal ortam bulunamadı. README.md içindeki kurulum adımlarını uygula."
}

Set-Location $projectRoot
& $python main.py
exit $LASTEXITCODE
