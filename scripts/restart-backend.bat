@echo off
REM Stop any backend on port 8000, then start the updated backend (con Alpaca)

echo Stopping any process on port 8001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a 2>nul
)
timeout /t 3 /nobreak >nul

echo Starting backend (updated code with alpaca.trading)...
start "Backend Server" cmd /k "cd /d %~dp0backend && python main.py"

echo.
echo Backend avviato su http://localhost:8001
echo.
echo Dopo 5-10 secondi:
echo   1. Apri http://localhost:8001/api/debug/build
echo      - Se vedi "alpaca_available":true il backend e' aggiornato.
echo   2. Ricarica la dashboard (F5) e riprova Esegui ordine.
echo.
pause
