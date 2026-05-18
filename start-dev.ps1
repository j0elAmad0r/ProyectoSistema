Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontend = Join-Path $root 'frontend'
$python = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw "No se encontro el entorno virtual en $python"
}

Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-ExecutionPolicy', 'Bypass',
    '-Command', "Set-Location '$root'; & '$python' app.py"
)

Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-ExecutionPolicy', 'Bypass',
    '-Command', "Set-Location '$frontend'; npm run dev -- --host 127.0.0.1 --port 5173 --strictPort"
)

Write-Host 'Backend: http://127.0.0.1:8000'
Write-Host 'Frontend: http://127.0.0.1:5173'