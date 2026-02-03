@echo off
REM Windows development startup script

echo Starting The Sentient Development Servers...

REM Start backend
start "Backend Server" cmd /k "cd backend && python main.py"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start frontend
start "Frontend Server" cmd /k "cd frontend && npm run dev"

REM Start Streamlit Backtesting (porta 8501)
start "Backtesting (Streamlit)" cmd /k "cd streamlit_app && python -m streamlit run app.py --server.port 8501 --server.headless true"

echo.
echo Backend: http://localhost:8001
echo Frontend: http://localhost:5173
echo Backtesting: http://localhost:8501
echo.
echo Close the windows to stop the servers.

