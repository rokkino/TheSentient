#!/usr/bin/env python3
"""
Programma per ottenere tutti gli earnings per una data specifica
Usage: python get_earnings_by_date.py [YYYY-MM-DD]
Se non viene fornita una data, verrà chiesta interattivamente

DIPENDENZE:
- yfinance (già presente nel progetto) - metodo principale
- yahoo_fin (opzionale, potrebbe causare conflitti con websockets)

NOTA: Se yahoo_fin causa conflitti di dipendenze (websockets), il programma
userà automaticamente yfinance come fallback.
"""

import sys
import io
from datetime import datetime, date
from typing import List, Dict, Any

# Fix encoding per Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Prova a importare yahoo_fin, ma non fallire se non disponibile
yahoo_fin_available = False
yahoo_fin_warning = False
try:
    import yahoo_fin.stock_info as si
    yahoo_fin_available = True
    # Verifica se ci sono problemi con le dipendenze
    try:
        import websockets
        ws_version = tuple(map(int, websockets.__version__.split('.')[:2]))
        if ws_version < (11, 0):
            yahoo_fin_warning = True
    except:
        pass
except ImportError:
    yahoo_fin_available = False
except Exception as e:
    yahoo_fin_available = False
    yahoo_fin_warning = True

# Fallback: usa yfinance che è già nel progetto
yfinance_available = False
try:
    import yfinance as yf
    yfinance_available = True
except ImportError:
    yfinance_available = False

# Per scraping diretto
try:
    import requests
    from bs4 import BeautifulSoup
    requests_available = True
except ImportError:
    requests_available = False

if not yahoo_fin_available and not yfinance_available:
    print("❌ Errore: Né yahoo_fin né yfinance sono disponibili.")
    print("\nInstalla almeno uno dei due:")
    print("  pip install yfinance")
    print("\nOppure per yahoo_fin (potrebbe causare conflitti di dipendenze):")
    print("  pip install yahoo_fin")
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
    
    # Ordina per simbolo (ticker)
    earnings_sorted = sorted(earnings, key=lambda x: str(x.get('ticker', x.get('Ticker', ''))).upper())
    
    # Stampa intestazione tabella estesa (con più informazioni se disponibili)
    has_extra_info = any(e.get('marketCap') not in [None, 'N/A'] or e.get('fiscalQuarter') not in [None, 'N/A'] for e in earnings_sorted)
    
    if has_extra_info:
        # Tabella estesa con informazioni aggiuntive
        print(f"{'Simbolo':<10} {'Azienda':<40} {'EPS Forecast':<15} {'Market Cap':<18} {'Quarter':<12}")
        print("-" * 100)
        
        for earning in earnings_sorted:
            ticker = earning.get('ticker', earning.get('Ticker', 'N/A'))
            if ticker:
                ticker = str(ticker).upper()
            else:
                ticker = 'N/A'
            
            company = (earning.get('companymearningsshortname') or 
                      earning.get('company') or 
                      earning.get('Company') or 
                      earning.get('companyName') or 
                      'N/A')
            if len(company) > 38:
                company = company[:35] + "..."
            
            eps_forecast = earning.get('epsestimate', earning.get('epsForecast', 'N/A'))
            if eps_forecast in [None, 'N/A', '']:
                eps_forecast = 'N/A'
            else:
                eps_forecast = str(eps_forecast)
            
            market_cap = earning.get('marketCap', 'N/A')
            if market_cap in [None, 'N/A', '']:
                market_cap = 'N/A'
            else:
                market_cap = str(market_cap)
            
            fiscal_quarter = earning.get('fiscalQuarter', 'N/A')
            if fiscal_quarter in [None, 'N/A', '']:
                fiscal_quarter = 'N/A'
            else:
                fiscal_quarter = str(fiscal_quarter)
            
            print(f"{ticker:<10} {company:<40} {eps_forecast:<15} {market_cap:<18} {fiscal_quarter:<12}")
    else:
        # Tabella semplice
        print(f"{'Simbolo':<12} {'Azienda':<45} {'EPS Stimato':<15} {'EPS Effettivo':<15}")
        print("-" * 90)
        
        for earning in earnings_sorted:
            ticker = earning.get('ticker', earning.get('Ticker', 'N/A'))
            if ticker:
                ticker = str(ticker).upper()
            else:
                ticker = 'N/A'
            
            company = (earning.get('companymearningsshortname') or 
                      earning.get('company') or 
                      earning.get('Company') or 
                      earning.get('companyName') or 
                      'N/A')
            if len(company) > 43:
                company = company[:40] + "..."
            
            eps_estimate = (earning.get('epsestimate') or 
                           earning.get('epsEstimate') or 
                           earning.get('EPS Estimate') or
                           earning.get('eps_estimate'))
            if eps_estimate is None:
                eps_estimate = 'N/A'
            elif isinstance(eps_estimate, (int, float)):
                eps_estimate = f"${eps_estimate:.2f}"
            else:
                eps_estimate = str(eps_estimate)
            
            eps_actual = (earning.get('epsactual') or 
                         earning.get('epsActual') or 
                         earning.get('EPS Actual') or
                         earning.get('eps_actual'))
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


def get_earnings_with_yahoo_fin(target_date: date) -> List[Dict[str, Any]]:
    """Recupera earnings usando yahoo_fin"""
    if not yahoo_fin_available:
        return []
    
    # Prova prima con get_earnings_in_date_range (più affidabile)
    try:
        from datetime import timedelta
        # Crea un range di un giorno (dalla data richiesta alla stessa data)
        start_date = target_date.strftime('%m/%d/%Y')
        end_date = (target_date + timedelta(days=1)).strftime('%m/%d/%Y')
        earnings_range = si.get_earnings_in_date_range(start_date, end_date)
        if earnings_range:
            # Filtra solo quelli della data esatta
            filtered = []
            for e in earnings_range:
                # Controlla se c'è una data nel dizionario
                earning_date_str = e.get('startdatetime') or e.get('date') or e.get('earningsDate')
                if earning_date_str:
                    try:
                        if isinstance(earning_date_str, (int, float)):
                            ed = datetime.fromtimestamp(earning_date_str).date()
                        elif isinstance(earning_date_str, str):
                            # Prova vari formati
                            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S']:
                                try:
                                    ed = datetime.strptime(earning_date_str.split('T')[0], fmt).date()
                                    break
                                except:
                                    continue
                            else:
                                continue
                        else:
                            ed = earning_date_str.date() if hasattr(earning_date_str, 'date') else None
                        
                        if ed == target_date:
                            filtered.append(e)
                    except:
                        # Se non riesce a parsare, include comunque (meglio avere più dati)
                        filtered.append(e)
            
            if filtered:
                return filtered
            
            # Se il filtro è troppo restrittivo, restituisci tutto il range
            return earnings_range
    except Exception as e:
        pass
    
    # Fallback: prova get_earnings_for_date (ma ha un bug noto)
    date_formats = [
        target_date.strftime('%m/%d/%Y'),  # MM/DD/YYYY
        target_date.strftime('%Y-%m-%d'),  # YYYY-MM-DD
        target_date.strftime('%B %d %Y'),  # March 1 2021
    ]
    
    for date_format in date_formats:
        try:
            earnings = si.get_earnings_for_date(date_format)
            if earnings:
                return earnings
        except (IndexError, Exception) as e:
            # IndexError è il bug noto di yahoo_fin, continua con il prossimo formato
            continue
    return []


def get_earnings_with_yfinance(target_date: date) -> List[Dict[str, Any]]:
    """Recupera earnings usando yfinance (fallback)"""
    if not yfinance_available:
        return []
    
    print("Usando yfinance come fallback...")
    print("Nota: yfinance non ha una funzione diretta per earnings per data.")
    print("Verifico alcuni ticker popolari...\n")
    
    earnings = []
    # Lista di ticker popolari da controllare
    popular_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
        'AMD', 'INTC', 'JPM', 'BAC', 'WMT', 'DIS', 'V', 'MA',
        'CRM', 'ORCL', 'ADBE', 'CSCO', 'IBM', 'QCOM', 'AVGO',
        'COST', 'HD', 'MCD', 'NKE', 'TGT', 'GS', 'JNJ', 'PG',
        'KO', 'PEP', 'WFC', 'C', 'AXP', 'UNH', 'VZ', 'T'
    ]
    
    for ticker in popular_tickers:
        try:
            tk = yf.Ticker(ticker)
            info = tk.info
            
            # Controlla earningsDate
            earnings_date = info.get('earningsDate')
            if earnings_date:
                if isinstance(earnings_date, list) and len(earnings_date) > 0:
                    earnings_date = earnings_date[0]
                
                try:
                    if isinstance(earnings_date, (int, float)):
                        ed = datetime.fromtimestamp(earnings_date).date()
                    else:
                        ed = datetime.fromisoformat(str(earnings_date).split('T')[0]).date()
                    
                    if ed == target_date:
                        earnings.append({
                            'ticker': ticker,
                            'company': info.get('longName', info.get('shortName', ticker)),
                            'epsestimate': info.get('epsForward', 'N/A'),
                            'epsactual': 'N/A'  # yfinance non fornisce questo facilmente
                        })
                except:
                    pass
            
            # Controlla anche il calendar
            try:
                calendar = tk.calendar
                if calendar and isinstance(calendar, dict):
                    earnings_dates = calendar.get('Earnings Date', [])
                    for ed in earnings_dates:
                        try:
                            if isinstance(ed, datetime):
                                ed_date = ed.date()
                            elif hasattr(ed, 'date'):
                                ed_date = ed.date()
                            else:
                                ed_date = datetime.fromisoformat(str(ed).split('T')[0]).date()
                            
                            if ed_date == target_date:
                                # Evita duplicati
                                if not any(e['ticker'] == ticker for e in earnings):
                                    earnings.append({
                                        'ticker': ticker,
                                        'company': info.get('longName', info.get('shortName', ticker)),
                                        'epsestimate': info.get('epsForward', 'N/A'),
                                        'epsactual': 'N/A'
                                    })
                        except:
                            continue
            except:
                pass
        except:
            continue
    
    return earnings


def get_earnings_for_date(target_date: date) -> List[Dict[str, Any]]:
    """Recupera tutti gli earnings per una data specifica"""
    print(f"\n🔍 Cercando earnings per la data: {target_date.strftime('%Y-%m-%d')}...")
    print("Usando API Nasdaq (metodo principale)...\n")
    
    # Usa API Nasdaq come metodo principale (più veloce e completo)
    import time
    start_time = time.time()
    
    earnings_nasdaq = get_earnings_from_nasdaq(target_date)
    elapsed = time.time() - start_time
    
    if earnings_nasdaq:
        print(f"✅ Trovati {len(earnings_nasdaq)} earnings da Nasdaq in {elapsed:.2f} secondi!")
        return earnings_nasdaq
    
    # Fallback solo se Nasdaq fallisce
    earnings = []
    
    if yahoo_fin_available:
        try:
            print("⚠️  Nasdaq non ha trovato risultati. Provo con yahoo_fin...")
            earnings = get_earnings_with_yahoo_fin(target_date)
            if earnings:
                print(f"✅ Trovati {len(earnings)} earnings con yahoo_fin!")
                return earnings
        except Exception as e:
            pass
    
    if yfinance_available and not earnings:
        print("⚠️  Provo con yfinance...")
        earnings = get_earnings_with_yfinance(target_date)
        if earnings:
            print(f"✅ Trovati {len(earnings)} earnings con yfinance!")
            return earnings
    
    if not earnings and not earnings_nasdaq:
        print("❌ Nessun earning trovato per questa data.")
        print("\n💡 Suggerimento:")
        print("   - Verifica che la data sia corretta")
        print("   - Prova con date diverse (ieri, domani, o date note con earnings)")
        print("   - Il problema potrebbe essere temporaneo con le API")
    
    return earnings


def get_earnings_from_nasdaq(target_date: date) -> List[Dict[str, Any]]:
    """Recupera earnings direttamente da Nasdaq (più affidabile)"""
    if not requests_available:
        return []
    
    try:
        
        date_str = target_date.strftime('%Y-%m-%d')
        url = "https://api.nasdaq.com/api/calendar/earnings"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.nasdaq.com/'
        }
        
        params = {'date': date_str}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'rows' in data['data']:
                rows = data['data']['rows']
                earnings = []
                
                for row in rows:
                    try:
                        # Il formato Nasdaq è un dizionario con tutte le informazioni
                        if isinstance(row, dict):
                            symbol = str(row.get('symbol', row.get('Symbol', ''))).strip().upper()
                            company = row.get('name', row.get('companyName', row.get('Company Name', symbol)))
                            time_str = str(row.get('time', row.get('Time', 'time-not-supplied')))
                            
                            # Informazioni aggiuntive disponibili
                            eps_forecast = row.get('epsForecast', row.get('epsEstimate', row.get('EPS Forecast')))
                            last_year_eps = row.get('lastYearEPS', row.get('lastYearEps'))
                            market_cap = row.get('marketCap', row.get('Market Cap'))
                            fiscal_quarter = row.get('fiscalQuarterEnding', row.get('Fiscal Quarter Ending'))
                            num_estimates = row.get('noOfEsts', row.get('noOfEstimates', row.get('# of Ests')))
                            last_year_date = row.get('lastYearRptDt', row.get('lastYearReportDate'))
                            
                        elif isinstance(row, (list, tuple)) and len(row) >= 2:
                            # Formato lista (meno comune)
                            symbol = str(row[0]).strip().upper() if row[0] else None
                            company = str(row[1]).strip() if len(row) > 1 and row[1] else symbol
                            time_str = str(row[2]) if len(row) > 2 else 'time-not-supplied'
                            eps_forecast = row[3] if len(row) > 3 else None
                            last_year_eps = row[4] if len(row) > 4 else None
                            market_cap = None
                            fiscal_quarter = None
                            num_estimates = None
                            last_year_date = None
                        else:
                            continue
                        
                        if not symbol or len(symbol) > 10:
                            continue
                        
                        if not company or company == 'N/A':
                            company = symbol
                        
                        time_info = 'TBD'
                        if time_str:
                            time_lower = str(time_str).lower()
                            if 'before' in time_lower or 'bmo' in time_lower or 'pre' in time_lower or 'pre-market' in time_lower:
                                time_info = 'Before Market Open'
                            elif 'after' in time_lower or 'amc' in time_lower or 'post' in time_lower or 'after-market' in time_lower:
                                time_info = 'After Market Close'
                            elif 'time-not-supplied' in time_lower or 'not supplied' in time_lower or time_lower == 'tbd':
                                time_info = 'TBD'
                        
                        earnings.append({
                            'ticker': symbol,
                            'companymearningsshortname': company,
                            'company': company,
                            'epsestimate': eps_forecast if eps_forecast not in [None, 'N/A', '', 'N/A'] else 'N/A',
                            'epsactual': last_year_eps if last_year_eps not in [None, 'N/A', ''] else 'N/A',
                            'time': time_info,
                            'date': target_date.isoformat(),
                            # Informazioni aggiuntive
                            'marketCap': market_cap if market_cap not in [None, 'N/A', ''] else 'N/A',
                            'fiscalQuarter': fiscal_quarter if fiscal_quarter not in [None, 'N/A', ''] else 'N/A',
                            'numEstimates': num_estimates if num_estimates not in [None, 'N/A', ''] else 'N/A',
                            'lastYearDate': last_year_date if last_year_date not in [None, 'N/A', ''] else 'N/A'
                        })
                    except Exception as e:
                        continue
                
                return earnings
    except Exception as e:
        pass
    
    return []


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
    # Mostra informazioni sulle dipendenze disponibili
    if yahoo_fin_warning:
        print("⚠️  AVVISO: yahoo_fin potrebbe avere conflitti di dipendenze (websockets).")
        print("   Il programma userà yfinance come fallback se necessario.\n")
    
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
        print("📅 RICERCA EARNINGS PER DATA")
        print("=" * 80)
        print("\nInserisci la data (formato: YYYY-MM-DD, oppure premi Invio per oggi)")
        date_input = input("Data: ").strip()
        
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
        response = input("Vuoi continuare comunque? (s/n): ").strip().lower()
        if response != 's' and response != 'si' and response != 'yes' and response != 'y':
            print("Operazione annullata.")
            sys.exit(0)
    
    # Recupera gli earnings
    try:
        earnings = get_earnings_for_date(target_date)
        
        # Mostra i risultati
        print_earnings_table(earnings, target_date)
        
        # Salva anche in un file opzionale (solo se esecuzione interattiva)
        # Non chiedere se la data è stata passata come argomento
        if earnings and len(sys.argv) == 1:  # Solo se modalità interattiva
            try:
                save_response = input("\nVuoi salvare i risultati in un file? (s/n): ").strip().lower()
                if save_response in ['s', 'si', 'yes', 'y']:
                    filename = f"earnings_{target_date.strftime('%Y%m%d')}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"EARNINGS PER LA DATA: {target_date.strftime('%A, %d %B %Y')}\n")
                        f.write("=" * 90 + "\n")
                        f.write(f"Totale: {len(earnings)} aziende\n\n")
                        f.write(f"{'Simbolo':<12} {'Azienda':<45} {'EPS Stimato':<15} {'EPS Effettivo':<15}\n")
                        f.write("-" * 90 + "\n")
                        
                        for earning in sorted(earnings, key=lambda x: str(x.get('ticker', x.get('Ticker', ''))).upper()):
                            ticker = earning.get('ticker', earning.get('Ticker', 'N/A'))
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
                                           earning.get('EPS Estimate') or
                                           earning.get('eps_estimate'))
                            if eps_estimate is None:
                                eps_estimate = 'N/A'
                            elif isinstance(eps_estimate, (int, float)):
                                eps_estimate = f"${eps_estimate:.2f}"
                            else:
                                eps_estimate = str(eps_estimate)
                            
                            eps_actual = (earning.get('epsactual') or 
                                         earning.get('epsActual') or 
                                         earning.get('EPS Actual') or
                                         earning.get('eps_actual'))
                            if eps_actual is None:
                                eps_actual = 'N/A'
                            elif isinstance(eps_actual, (int, float)):
                                eps_actual = f"${eps_actual:.2f}"
                            else:
                                eps_actual = str(eps_actual)
                            
                            f.write(f"{ticker:<12} {company:<45} {eps_estimate:<15} {eps_actual:<15}\n")
                    
                    print(f"✅ Risultati salvati in: {filename}")
            except (EOFError, KeyboardInterrupt):
                # Esecuzione non interattiva o interrotta
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

