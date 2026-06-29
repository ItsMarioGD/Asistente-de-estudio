@echo off
REM ============================================================
REM  Asistente de Estudio - lanzador para Windows
REM  Doble clic en este archivo para iniciar la aplicacion.
REM ============================================================
setlocal

cd /d "%~dp0"

REM --- Rutas absolutas (no dependemos de que python este en PATH) ---
set "PY=%~dp0venv\Scripts\python.exe"
set "APP=%~dp0app.py"

REM --- Verificaciones iniciales ---
echo.
echo ============================================================
echo   Asistente de Estudio
echo ============================================================
echo.

if not exist "%PY%" (
    echo [ERROR] No se encontro el entorno virtual.
    echo          Ejecuta primero: instalar.bat
    echo.
    pause
    exit /b 1
)

echo [1/3] Python del venv:
"%PY%" --version
echo.

REM Verificar Ollama (sin usar /FI que da problemas con pipes)
echo [2/3] Comprobando Ollama...
tasklist 2^>nul | find /I "ollama.exe" >nul
if errorlevel 1 (
    echo   Ollama NO esta corriendo. Intentando abrirlo...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" app
        echo   Espera 5 segundos a que Ollama arranque...
        timeout /t 5 /nobreak >nul
    ) else (
        echo   [AVISO] No se encontro Ollama instalado.
        echo           Descargalo de https://ollama.com/download
    )
) else (
    echo   Ollama OK.
)
echo.

REM --- Lanzar Streamlit ---
echo [3/3] Iniciando la aplicacion...
echo   URL local:   http://localhost:8501
echo   Si el navegador no se abre automaticamente, copia esa URL.
echo.
echo   Para detener la app: cierra esta ventana o presiona Ctrl+C.
echo ============================================================
echo.

REM Abrir el navegador 3 segundos despues (le da tiempo a Streamlit a arrancar)
start "" /min cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8501"

REM Lanzar streamlit en primer plano
"%PY%" -m streamlit run "%APP%"

REM Si streamlit termina, pausar para que veas el mensaje final
echo.
echo ============================================================
echo   La aplicacion se ha cerrado.
echo ============================================================
pause
endlocal