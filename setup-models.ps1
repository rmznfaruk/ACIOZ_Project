$ErrorActionPreference = "Stop"

$ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
$ollama = $null
if ($ollamaCommand) {
    $ollama = $ollamaCommand.Source
} else {
    $localOllama = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path $localOllama) {
        $ollama = $localOllama
    }
}

if (-not $ollama) {
    throw "Ollama bulunamadı. README.md içindeki Ollama kurulum adımını uygula."
}

$env:OLLAMA_HOST = "127.0.0.1:11434"
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 | Out-Null
} catch {
    Start-Process -FilePath $ollama -ArgumentList "serve" -WindowStyle Hidden
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        throw "Ollama servisi localhost üzerinde başlatılamadı."
    }
}

& $ollama pull qwen3:4b
if ($LASTEXITCODE -ne 0) {
    throw "Metin modeli indirilemedi."
}

& $ollama pull qwen2.5vl:3b
if ($LASTEXITCODE -ne 0) {
    throw "Görüntü modeli indirilemedi."
}
