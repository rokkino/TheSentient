# Programma Earnings per Data

## Problema con le Dipendenze

Hai installato `yahoo_fin` ma c'è un **conflitto di dipendenze**:

- `yfinance` (già nel progetto) richiede `websockets>=13.0`
- `yahoo_fin` dipende da `pyppeteer`, che richiede `websockets<11.0,>=10.0`

Questo crea un conflitto incompatibile.

## Soluzioni

### Soluzione 1: Usare il programma con yfinance (CONSIGLIATO)

Il programma ora usa automaticamente `yfinance` come fallback se `yahoo_fin` non funziona. `yfinance` è già installato nel progetto e non causa conflitti.

**Pro:** Funziona subito senza problemi  
**Contro:** Meno completo per alcuni ticker (controlla solo ticker popolari)

### Soluzione 2: Ambiente Virtuale Separato per yahoo_fin

Crea un ambiente virtuale dedicato solo per questo script:

```bash
# Crea nuovo ambiente virtuale
python -m venv venv_earnings

# Attiva (Windows)
venv_earnings\Scripts\activate

# Installa solo yahoo_fin e dipendenze
pip install yahoo_fin

# Esegui il programma
python get_earnings_by_date.py 2025-01-15
```

### Soluzione 3: Ignorare il Warning (a tuo rischio)

Il warning potrebbe non impedire il funzionamento. Prova a eseguire comunque:

```bash
python get_earnings_by_date.py 2025-01-15
```

Se funziona, puoi ignorare il warning. Tuttavia, alcune funzionalità di `pyppeteer` potrebbero non funzionare correttamente.

### Soluzione 4: Usare il servizio esistente del backend

Il progetto ha già un `EarningsService` che fa scraping da multiple fonti senza dipendenze problematiche. Potresti usare quello invece.

## Uso del Programma

```bash
# Con data come argomento
python get_earnings_by_date.py 2025-01-15

# Modalità interattiva
python get_earnings_by_date.py
```

## Formati Data Supportati

- `YYYY-MM-DD` (es: 2025-01-15)
- `DD-MM-YYYY` (es: 15-01-2025)
- `DD/MM/YYYY` (es: 15/01/2025)
- `MM/DD/YYYY` (es: 01/15/2025)
- `January 15 2025` (formato esteso)

## Note

Il programma ora gestisce automaticamente:
1. Prova `yahoo_fin` se disponibile
2. Se fallisce, usa `yfinance` come fallback
3. Mostra messaggi chiari su quale metodo viene usato
