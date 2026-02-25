#!/usr/bin/env python
"""
Diagnostica Alpaca: verifica che alpaca-py sia disponibile e che il backend
che risponde su :8000 sia quello aggiornato.
"""
import sys
import os

# Assicurati di essere nella cartella backend per gli import
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

def main():
    print("=" * 60)
    print("DIAGNOSTICA ALPACA")
    print("=" * 60)
    print(f"Python: {sys.executable}")
    print(f"CWD:    {os.getcwd()}")
    print()

    # 1. Import modulo alpaca_service (stesso che usa il backend)
    try:
        from services.alpaca_service import ALPACA_AVAILABLE, AlpacaService
        print(f"[OK] ALPACA_AVAILABLE = {ALPACA_AVAILABLE}")
        s = AlpacaService()
        print(f"[OK] AlpacaService() creato, is_configured = {s.is_configured()}")
    except Exception as e:
        print(f"[ERRORE] Import alpaca_service: {e}")
        print()
        print("SOLUZIONE: dalla cartella backend esegui: pip install alpaca-py")
        return 1

    if not ALPACA_AVAILABLE:
        print("[ERRORE] ALPACA_AVAILABLE e' False: il modulo non ha trovato alpaca.trading")
        print("SOLUZIONE: pip install alpaca-py (nello stesso Python usato per avviare il backend)")
        return 1

    # 2. Controlla il backend in ascolto su :8001 (porta dev)
    print()
    print("Controllo backend su http://127.0.0.1:8001 ...")
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8001/api/debug/build")
        with urllib.request.urlopen(req, timeout=3) as r:
            body = r.read().decode()
            print(f"[OK] Risposta: {body}")
            if "alpaca_available" in body and "true" in body:
                print("[OK] Il backend che risponde e' AGGIORNATO (usa alpaca.trading).")
                print("     L'esecuzione ordini su Alpaca dovrebbe funzionare.")
            else:
                print("[?] Risposta inattesa (alpaca_available non true).")
    except urllib.error.HTTPError as e:
        print(f"[ERRORE] HTTP {e.code}: {e.read().decode()}")
        return 1
    except OSError as e:
        print(f"[INFO] Nessun backend in ascolto su :8001 ({e})")
        print("       Avvia il backend con: cd backend && python main.py")
        return 0

    print()
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
