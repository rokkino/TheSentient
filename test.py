import sys
import yfinance as yf

try:
    from curl_cffi.requests import Session
except ImportError:
    print("ERRORE: 'curl_cffi' non trovato. Esegui: pip install curl_cffi")
    sys.exit(1)

# --- CONFIGURAZIONE DEL TEST ---
# Imposta questo su False per la rete aziendale
SSL_VERIFY = False
TICKER = "NVDA"
# ------------------------------

print(f"--- AVVIO TEST 'yfinance' + 'curl_cffi' ---")
print(f"Ticker: {TICKER}")
print(f"Modalità Verifica SSL: {SSL_VERIFY}\n")

session = None
try:
    # 1. Crea la sessione che impersona Chrome
    print("Creazione sessione curl_cffi (impersonate='chrome110')...")
    session = Session(impersonate="chrome110")
    
    # 2. Applica l'impostazione SSL
    session.verify = SSL_VERIFY

    # 3. Passa la sessione a yfinance
    print(f"Richiesta dati per {TICKER} tramite yf.Ticker (sessione passata)...")
    tk = yf.Ticker(TICKER, session=session)
    
    # 4. Scarica i dati storici
    data = tk.history(period="1mo")
    
    if data.empty:
        raise ValueError("yfinance non ha restituito dati (data.empty è True).")

    print("\n--- RISULTATO ---")
    print("✅ SUCCESSO!")
    print(f"Dati storici per {TICKER} scaricati correttamente.")
    print("-----------------")
    print("Ultime 5 righe di dati:")
    print(data.tail())

except Exception as e:
    print("\n--- RISULTATO ---")
    print(f"❌ FALLITO (Errore: {type(e).__name__})")
    if "SSL certificate problem" in str(e):
        print("DIAGNOSI: Errore SSL. Assicurati che SSL_VERIFY = False")
    elif "429" in str(e):
        print("DIAGNOSI: Errore 429. Yahoo ti sta ancora bloccando (Rate Limit).")
    elif "Yahoo API requires curl_cffi" in str(e):
         print("DIAGNOSI: yfinance non sta ricevendo la sessione curl_cffi correttamente.")
    else:
        print(f"Dettagli Errore: {e}")
    print("-----------------")

finally:
    if session:
        session.close()
    print("\n--- TEST COMPLETATO ---")