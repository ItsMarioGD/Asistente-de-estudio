@echo off
REM ============================================================
REM  Instalador del Asistente de Estudio (solo primera vez)
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   Instalando Asistente de Estudio...
echo ============================================================
echo.

REM Detectar Python: primero el del PATH, luego el launcher "py"
set "PY=python"
where python >nul 2>nul
if errorlevel 1 (
    set "PY=py"
    where py >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python no esta instalado.
        echo          Descargalo de https://www.python.org/downloads/
        echo          Durante la instalacion, MARCA "Add Python to PATH".
        echo.
        pause
        exit /b 1
    )
)

echo [1/4] Version de Python:
%PY% --version
echo.

echo [2/4] Creando entorno virtual...
if exist venv (
    echo   venv ya existe, lo reutilizamos.
) else (
    %PY% -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)
echo.

echo [3/4] Instalando dependencias (puede tardar unos minutos)...
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt" --quiet
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)
echo   Dependencias OK.
echo.

echo [4/4] Descargando modelos de IA (esto es LENTO: ~5 GB)...
echo   Si se interrumpe, puedes ejecutar "ollama pull llama3.1:8b" despues.
where ollama >nul 2>nul
if errorlevel 1 (
    echo   [AVISO] Ollama no esta en el PATH.
    echo            Instalalo desde https://ollama.com/download
    echo            y luego ejecuta:  ollama pull llama3.1:8b
    echo                                ollama pull nomic-embed-text
) else (
    ollama pull llama3.1:8b
    ollama pull nomic-embed-text
)
echo.

echo ============================================================
echo   Instalacion completa.
echo   Ahora ejecuta run.bat para iniciar la aplicacion.
echo ============================================================
echo.
pause
endlocal