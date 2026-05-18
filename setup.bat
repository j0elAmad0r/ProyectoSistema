@echo off
REM setup.bat - Script de configuracion automatica para ProgSistemas

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   ProgSistemas - Setup Automatico
echo ========================================
echo.

REM 1. Crear entorno virtual Python
echo [1/4] Creando entorno virtual Python...
if not exist ".venv" (
    python -m venv .venv
    echo. ✓ Entorno virtual creado
) else (
    echo. ✓ Entorno virtual ya existe
)

REM 2. Activar entorno virtual e instalar dependencias Python
echo [2/4] Instalando dependencias Python...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo. ✓ Dependencias Python instaladas

REM 3. Instalar dependencias Node.js
echo [3/4] Instalando dependencias Node.js (frontend)...
cd frontend
if not exist "node_modules" (
    npm install
    echo. ✓ Dependencias Node.js instaladas
) else (
    echo. ✓ Dependencias Node.js ya existen
)
cd ..

REM 4. Iniciar servidores
echo [4/4] Iniciando servidores...
echo.
echo ========================================
echo   ¡Configuracion completada!
echo ========================================
echo.
echo Las siguientes ventanas se abriran automaticamente:
echo   - Terminal 1: Backend FastAPI (127.0.0.1:8000)
echo   - Terminal 2: Frontend React/Vite (127.0.0.1:5173)
echo.
pause

REM Abrir Backend en nueva ventana
echo.
echo Abriendo Backend...
start cmd /k ".venv\Scripts\activate.bat && python app.py"

REM Pequeña pausa para que se estabilice el backend
timeout /t 2 /nobreak

REM Abrir Frontend en nueva ventana
echo Abriendo Frontend...
start cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo ✓ Servidores iniciados. Abre tu navegador en http://127.0.0.1:5173
echo.
pause
