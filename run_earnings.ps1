# Script PowerShell per eseguire il programma earnings con ambiente virtuale

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Programma Earnings per Data" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Imposta encoding UTF-8
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Attiva l'ambiente virtuale
& .\venv_earnings\Scripts\Activate.ps1

# Esegui il programma con gli argomenti passati
python get_earnings_by_date.py $args

# Disattiva l'ambiente virtuale (automatico quando lo script termina)
