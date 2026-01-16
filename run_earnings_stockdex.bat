@echo off
chcp 65001 >nul
REM Script per eseguire il programma earnings con stockdex
echo ========================================
echo Programma Earnings per Data (stockdex)
echo ========================================
echo.

REM Imposta encoding UTF-8
set PYTHONIOENCODING=utf-8

REM Attiva l'ambiente virtuale
call venv_earnings\Scripts\activate.bat

REM Esegui il programma con gli argomenti passati
python get_earnings_stockdex.py %*

REM Disattiva l'ambiente virtuale
call deactivate

pause
