#!/usr/bin/env python3
"""
Programma alternativo per ottenere earnings usando stockdex
Usage: python get_earnings_stockdex.py [YYYY-MM-DD]

Richiede: pip install stockdex
"""

import sys
import io
from datetime import datetime, date
from typing import List, Dict, Any
import pandas as pd

# Fix encoding per Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from stockdex import Ticker
    stockdex_available = True
except ImportError:
    stockdex_available = False
    print("❌ Errore: stockdex non è installato.")
    print("\nInstalla stockdex con:")
    print("  pip install stockdex")
    print("\nOppure aggiorna la versione esistente con:")
    print("  pip install stockdex -U")
    sys.exit(1)


def print_earnings_table(earnings: List[Dict[str, Any]], target_date: date):
    """Stampa gli earnings in formato tabella"""
    if not earnings:
        print(f"\n❌ Nessun earning trovato per la data {target_date.strftime('%Y-%m-%d')}")
        return
    
    print(f"\n{'='*90}")
    print(f"📅 EARNINGS PER LA DATA: {target_date.strftime('%A, %d %B %Y')}")
    print(f"{'='*90}")
    print(f"Totale: {len(earnings)} aziende\n")
    
    # Ordina per simbolo
    earnings_sorted = sorted(earnings, key=lambda x: str(x.get('ticker', x.get('symbol', ''))).upper())
    
    # Stampa intestazione tabella
    print(f"{'Simbolo':<12} {'Azienda':<45} {'EPS Stimato':<15} {'EPS Effettivo':<15}")
    print("-" * 90)
    
    # Stampa tutti gli earnings
    for earning in earnings_sorted:
        ticker = earning.get('ticker', earning.get('symbol', earning.get('Ticker', 'N/A')))
        if ticker:
            ticker = str(ticker).upper()
        else:
            ticker = 'N/A'
        
        company = (earning.get('companymearningsshortname') or 
                  earning.get('company') or 
                  earning.get('Company') or 
                  earning.get('companyName') or 
                  earning.get('name') or
                  'N/A')
        if len(company) > 43:
            company = company[:40] + "..."
        
        eps_estimate = (earning.get('epsestimate') or 
                       earning.get('epsEstimate') or 
                       earning.get('EPS Estimate') or
                       earning.get('eps_estimate') or
                       earning.get('eps_expected'))
        if eps_estimate is None:
            eps_estimate = 'N/A'
        elif isinstance(eps_estimate, (int, float)):
            eps_estimate = f"${eps_estimate:.2f}"
        else:
            eps_estimate = str(eps_estimate)
        
        eps_actual = (earning.get('epsactual') or 
                     earning.get('epsActual') or 
                     earning.get('EPS Actual') or
                     earning.get('eps_actual') or
                     earning.get('eps_reported'))
        if eps_actual is None:
            eps_actual = 'N/A'
        elif isinstance(eps_actual, (int, float)):
            eps_actual = f"${eps_actual:.2f}"
        else:
            eps_actual = str(eps_actual)
        
        print(f"{ticker:<12} {company:<45} {eps_estimate:<15} {eps_actual:<15}")
    
    print(f"\n{'='*90}")
    print(f"📊 TOTALE: {len(earnings)} aziende")
    print(f"{'='*90}\n")


def get_earnings_with_stockdex(target_date: date) -> List[Dict[str, Any]]:
    """Recupera earnings usando stockdex"""
    if not stockdex_available:
        return []
    
    print(f"Usando stockdex per recuperare earnings...")
    print("Nota: stockdex non ha una funzione diretta per earnings per data.")
    print("Verifico alcuni ticker popolari usando finviz_earnings_data...\n")
    
    earnings = []
    
    # Lista di ticker popolari da controllare
    popular_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
        'AMD', 'INTC', 'JPM', 'BAC', 'WMT', 'DIS', 'V', 'MA',
        'CRM', 'ORCL', 'ADBE', 'CSCO', 'IBM', 'QCOM', 'AVGO',
        'COST', 'HD', 'MCD', 'NKE', 'TGT', 'GS', 'JNJ', 'PG',
        'KO', 'PEP', 'WFC', 'C', 'AXP', 'UNH', 'VZ', 'T',
        'ANIX', 'LEDS', 'LEXX'  # Aggiungi quelli trovati oggi
    ]
    
    for ticker in popular_tickers:
        try:
            t = Ticker(ticker)
            
            # Prova con finviz_earnings_data
            try:
                earnings_df = t.finviz_earnings_data()
                if earnings_df is not None and not earnings_df.empty:
                    # Cerca nella colonna delle date
                    for idx, row in earnings_df.iterrows():
                        try:
                            # Prova diverse colonne per la data
                            date_cols = ['Date', 'date', 'Earnings Date', 'earningsDate', 'Report Date']
                            earning_date = None
                            
                            for col in date_cols:
                                if col in row:
                                    date_val = row[col]
                                    if pd.isna(date_val):
                                        continue
                                    
                                    if isinstance(date_val, date):
                                        earning_date = date_val
                                    elif isinstance(date_val, datetime):
                                        earning_date = date_val.date()
                                    elif isinstance(date_val, str):
                                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S', '%b %d, %Y']:
                                            try:
                                                earning_date = datetime.strptime(date_val.split('T')[0], fmt).date()
                                                break
                                            except:
                                                continue
                                    break
                            
                            if earning_date == target_date:
                                # Evita duplicati
                                if not any(e.get('ticker') == ticker for e in earnings):
                                    earnings.append({
                                        'ticker': ticker,
                                        'company': row.get('Company', t.full_name if hasattr(t, 'full_name') else ticker),
                                        'companymearningsshortname': row.get('Company', ticker),
                                        'epsestimate': row.get('EPS Estimate', row.get('Estimate', 'N/A')),
                                        'epsactual': row.get('EPS Actual', row.get('Actual', 'N/A')),
                                        'date': target_date.isoformat()
                                    })
                        except:
                            continue
            except:
                pass
            
            # Prova anche con digrin_upcoming_estimated_earnings
            try:
                upcoming = t.digrin_upcoming_estimated_earnings()
                if upcoming is not None and not upcoming.empty:
                    for idx, row in upcoming.iterrows():
                        try:
                            date_cols = ['Date', 'date', 'Earnings Date', 'earningsDate']
                            earning_date = None
                            
                            for col in date_cols:
                                if col in row:
                                    date_val = row[col]
                                    if pd.isna(date_val):
                                        continue
                                    
                                    if isinstance(date_val, date):
                                        earning_date = date_val
                                    elif isinstance(date_val, datetime):
                                        earning_date = date_val.date()
                                    elif isinstance(date_val, str):
                                        for fmt in ['%Y-%m-%d', '%m/%d/%Y']:
                                            try:
                                                earning_date = datetime.strptime(date_val.split('T')[0], fmt).date()
                                                break
                                            except:
                                                continue
                                    break
                            
                            if earning_date == target_date:
                                if not any(e.get('ticker') == ticker for e in earnings):
                                    earnings.append({
                                        'ticker': ticker,
                                        'company': t.full_name if hasattr(t, 'full_name') else ticker,
                                        'companymearningsshortname': t.full_name if hasattr(t, 'full_name') else ticker,
                                        'epsestimate': row.get('EPS Estimate', 'N/A'),
                                        'epsactual': 'N/A',
                                        'date': target_date.isoformat()
                                    })
                        except:
                            continue
            except:
                pass
                
        except Exception as e:
            continue
    
    return earnings


def parse_date(date_str: str) -> date:
    """Prova a parsare la data in vari formati"""
    formats = [
        '%Y-%m-%d',      # 2025-01-15
        '%d-%m-%Y',      # 15-01-2025
        '%d/%m/%Y',      # 15/01/2025
        '%m/%d/%Y',      # 01/15/2025 (formato US)
        '%Y/%m/%d',      # 2025/01/15
        '%d.%m.%Y',      # 15.01.2025
        '%B %d %Y',      # January 15 2025
        '%b %d %Y',      # Jan 15 2025
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    
    raise ValueError(f"Formato data non riconosciuto: {date_str}")


def main():
    """Funzione principale"""
    target_date = None
    
    # Controlla se la data è passata come argomento
    if len(sys.argv) > 1:
        try:
            target_date = parse_date(sys.argv[1])
        except ValueError as e:
            print(f"❌ Errore: {e}")
            print("\nFormati supportati:")
            print("  YYYY-MM-DD  (es: 2025-01-15)")
            print("  DD-MM-YYYY  (es: 15-01-2025)")
            print("  DD/MM/YYYY  (es: 15/01/2025)")
            sys.exit(1)
    else:
        # Chiedi la data interattivamente
        print("=" * 80)
        print("📅 RICERCA EARNINGS PER DATA (usando stockdex)")
        print("=" * 80)
        print("\nInserisci la data (formato: YYYY-MM-DD, oppure premi Invio per oggi)")
        try:
            date_input = input("Data: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOperazione annullata.")
            sys.exit(0)
        
        if not date_input:
            target_date = date.today()
            print(f"Usando la data di oggi: {target_date.strftime('%Y-%m-%d')}")
        else:
            try:
                target_date = parse_date(date_input)
            except ValueError as e:
                print(f"❌ Errore: {e}")
                print("\nFormati supportati:")
                print("  YYYY-MM-DD  (es: 2025-01-15)")
                print("  DD-MM-YYYY  (es: 15-01-2025)")
                print("  DD/MM/YYYY  (es: 15/01/2025)")
                sys.exit(1)
    
    # Verifica che la data non sia nel futuro lontano
    if target_date > date.today():
        print(f"⚠️  Avviso: La data {target_date.strftime('%Y-%m-%d')} è nel futuro.")
        try:
            response = input("Vuoi continuare comunque? (s/n): ").strip().lower()
            if response not in ['s', 'si', 'yes', 'y']:
                print("Operazione annullata.")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\nOperazione annullata.")
            sys.exit(0)
    
    # Recupera gli earnings
    try:
        print(f"\n🔍 Cercando earnings per la data: {target_date.strftime('%Y-%m-%d')}...")
        print("Questo potrebbe richiedere alcuni secondi...\n")
        
        earnings = get_earnings_with_stockdex(target_date)
        
        # Mostra i risultati
        print_earnings_table(earnings, target_date)
        
        # Salva anche in un file opzionale (solo se esecuzione interattiva)
        if earnings and len(sys.argv) == 1:
            try:
                save_response = input("\nVuoi salvare i risultati in un file? (s/n): ").strip().lower()
                if save_response in ['s', 'si', 'yes', 'y']:
                    filename = f"earnings_stockdex_{target_date.strftime('%Y%m%d')}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"EARNINGS PER LA DATA: {target_date.strftime('%A, %d %B %Y')}\n")
                        f.write("=" * 90 + "\n")
                        f.write(f"Totale: {len(earnings)} aziende\n")
                        f.write("Fonte: stockdex\n\n")
                        f.write(f"{'Simbolo':<12} {'Azienda':<45} {'EPS Stimato':<15} {'EPS Effettivo':<15}\n")
                        f.write("-" * 90 + "\n")
                        
                        for earning in sorted(earnings, key=lambda x: str(x.get('ticker', x.get('symbol', ''))).upper()):
                            ticker = earning.get('ticker', earning.get('symbol', 'N/A'))
                            if ticker:
                                ticker = str(ticker).upper()
                            else:
                                ticker = 'N/A'
                            
                            company = (earning.get('companymearningsshortname') or 
                                      earning.get('company') or 
                                      earning.get('Company') or 
                                      earning.get('companyName') or 
                                      'N/A')
                            
                            eps_estimate = (earning.get('epsestimate') or 
                                           earning.get('epsEstimate') or 
                                           earning.get('eps_expected'))
                            if eps_estimate is None:
                                eps_estimate = 'N/A'
                            elif isinstance(eps_estimate, (int, float)):
                                eps_estimate = f"${eps_estimate:.2f}"
                            else:
                                eps_estimate = str(eps_estimate)
                            
                            eps_actual = (earning.get('epsactual') or 
                                         earning.get('epsActual') or 
                                         earning.get('eps_reported'))
                            if eps_actual is None:
                                eps_actual = 'N/A'
                            elif isinstance(eps_actual, (int, float)):
                                eps_actual = f"${eps_actual:.2f}"
                            else:
                                eps_actual = str(eps_actual)
                            
                            f.write(f"{ticker:<12} {company:<45} {eps_estimate:<15} {eps_actual:<15}\n")
                    
                    print(f"✅ Risultati salvati in: {filename}")
            except (EOFError, KeyboardInterrupt):
                pass
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operazione interrotta dall'utente.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore durante il recupero degli earnings: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
