# setup.ps1 - Script de configuración automática para ProgSistemas

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ProgSistemas - Setup Automático" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Crear entorno virtual Python
Write-Host "[1/4] Creando entorno virtual Python..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✓ Entorno virtual creado" -ForegroundColor Green
} else {
    Write-Host "✓ Entorno virtual ya existe" -ForegroundColor Green
}

# 2. Activar entorno virtual e instalar dependencias Python
Write-Host "[2/4] Instalando dependencias Python..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Write-Host "✓ Dependencias Python instaladas" -ForegroundColor Green

# 3. Instalar dependencias Node.js
Write-Host "[3/4] Instalando dependencias Node.js (frontend)..." -ForegroundColor Yellow
cd frontend
if (-not (Test-Path "node_modules")) {
    npm install
    Write-Host "✓ Dependencias Node.js instaladas" -ForegroundColor Green
} else {
    Write-Host "✓ Dependencias Node.js ya existen" -ForegroundColor Green
}
cd ..

# 4. Iniciar servidores
Write-Host "[4/4] Iniciando servidores..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ¡Configuración completada!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Las siguientes ventanas se abrirán automáticamente:" -ForegroundColor Cyan
Write-Host "  • Terminal 1: Backend FastAPI (127.0.0.1:8000)" -ForegroundColor White
Write-Host "  • Terminal 2: Frontend React/Vite (127.0.0.1:5173)" -ForegroundColor White
Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Abrir Backend en nueva ventana
Write-Host ""
Write-Host "Abriendo Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; python app.py"

# Pequeña pausa para que se estabilice el backend
Start-Sleep -Seconds 2

# Abrir Frontend en nueva ventana
Write-Host "Abriendo Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev -- --host 127.0.0.1 --port 5173"

Write-Host ""
Write-Host "✓ Servidores iniciados. Abre tu navegador en http://127.0.0.1:5173" -ForegroundColor Green
