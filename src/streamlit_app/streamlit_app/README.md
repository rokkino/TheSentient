# TheSentient - Backtesting Dashboard

Dashboard Streamlit per la simulazione storica del bot **Earning Report Genius**.

## Avvio

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Oppure su Windows: `run_backtest.bat`

## Funzionalità

- **Data Ingestion**: Lista S&P 500 o Nasdaq 100, earnings storici da Nasdaq API, OHLC da yfinance
- **Simulation Loop**: Per ogni evento earnings, invoca `bot_logic_placeholder()` e calcola P&L vs giorno successivo
- **Report**: Win Rate, P&L totale, filtri per anno e settore
- **Caching**: Dati earnings e ticker cachati per run successivi

## Personalizzazione

Sostituisci `bot_logic_placeholder()` in `backtest_engine.py` con la tua logica Earning Report Genius (es. integrazione Gemini). La firma:

```python
def bot_logic_placeholder(ticker, earnings_date, pre_price, ohlc_history, earning_info) -> Dict:
    # Ritorna: {"decision": "BUY"|"WAIT"|"NO_GO", "confidence_score": 0-100, "reasoning": "..."}
```
