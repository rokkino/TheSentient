import yfinance as yf
import time
from datetime import datetime

# --- 1. YAHOO FINANCE NEWS (CON FILTRI E PARSING CORRETTI) ---

def get_yfinance_news(tickers):
    """
    Estrae le notizie più recenti da Yahoo Finance per un elenco di ticker.
    Filtra le notizie senza titolo o con timestamp non validi.
    """
    all_news = []
    # Nota: Riduciamo la verbosità per il loop in real-time
    # print(f"[News.py] Avvio recupero notizie da Yahoo Finance per {len(tickers)} ticker...")
    
    for ticker in tickers:
        try:
            tk = yf.Ticker(ticker)
            news_list = tk.news
            
            if not news_list:
                continue

            for news_item in news_list:
                
                # --- FIX: Leggi dal dizionario 'content' annidato ---
                content = news_item.get('content')
                if not content:
                    continue

                pub_date_str = content.get('pubDate')
                title = content.get('title')
                
                # Prova a ottenere il link da 'clickThroughUrl', altrimenti da 'canonicalUrl'
                link_data = content.get('clickThroughUrl') or content.get('canonicalUrl')
                link = link_data.get('url') if link_data else None

                # Salta questa notizia se manca un'informazione chiave
                if not title or not pub_date_str or not link:
                    continue
                # --- FINE FIX ---
                
                # Converti la data da stringa ISO (es. '2025-11-04T00:31:05Z')
                try:
                    # Rimuovi la 'Z' (UTC) per compatibilità
                    timestamp = datetime.fromisoformat(pub_date_str.replace('Z', ''))
                except ValueError:
                    # Salta se il formato data è strano
                    continue
                
                formatted_item = {
                    'source': 'Yahoo Finance',
                    'ticker': ticker,
                    'title': title,
                    'link': link,
                    'publisher': content.get('provider', {}).get('displayName'),
                    'timestamp': timestamp,
                    'text': title # Per l'LLM, il testo è il titolo
                }
                all_news.append(formatted_item)
            
            # RIMOSSO: time.sleep(0.5) <-- Non necessario se il loop principale attende 5 min.

        except Exception as e:
            # Silenzia gli errori nel loop per non intasare il log
            # print(f"[News.py] Errore durante il recupero notizie per {ticker}: {e}")
            pass
            
    # print(f"[News.py] Recupero da Yahoo Finance completato. Trovate {len(all_news)} notizie valide.")
    return all_news


# --- 2. FUNZIONE AGGREGATORE (SEMPLIFICATA) ---

def fetch_all_news(yfinance_tickers):
    """
    Raccoglie notizie da Yahoo Finance e le unisce in un unico "data pool".
    """
    all_news = []
    
    # Fonte 1: Yahoo Finance
    yahoo_news = get_yfinance_news(yfinance_tickers)
    all_news.extend(yahoo_news)
    
    # Ordina il pool di dati per timestamp, con il più recente in cima
    if all_news:
        all_news.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return all_news

# --- 3. ESECUZIONE IN REAL TIME (per testare questo file) ---
if __name__ == "__main__":
    
    # 1. Definisci i tuoi target
    YFINANCE_TICKERS_TO_WATCH = [
        'GC=F',  # Oro
        'CL=F',  # Petrolio Greggio
        '^GSPC', # S&P 500
        'NVDA',  # Nvidia (AI)
        'MSFT',  # Microsoft (AI)
        'GOOGL', # Google (AI)
        'TSLA',  # Tesla
        'AAPL'   # Apple
    ]
    
    # Set per tenere traccia delle notizie già viste (usiamo i link come ID univoco)
    seen_links = set()
    is_first_run = True

    print("--- Avvio News Feed Monitor (Ctrl+C per uscire) ---")

    try:
        while True:
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{current_time}] Controllo nuove notizie da Yahoo Finance...")
            
            # 2. Recupera il data pool
            data_pool = fetch_all_news(YFINANCE_TICKERS_TO_WATCH)
            
            new_items = []
            if not data_pool:
                print("Nessuna notizia trovata.")
                time.sleep(60) # Attendi 1 minuto se non c'è nulla
                continue
                
            # 3. Filtra le notizie che non abbiamo ancora visto
            for item in data_pool:
                link = item.get('link')
                if link and link not in seen_links:
                    new_items.append(item)
                    seen_links.add(link)
            
            # 4. Decidi cosa mostrare
            if is_first_run:
                items_to_show = new_items[:3] # Mostra solo le ultime 3 al primo avvio
                print(f"--- Mostro le {len(items_to_show)} notizie più recenti trovate all'avvio ---")
                is_first_run = False
            else:
                items_to_show = new_items # Mostra tutte le *nuove* notizie
                if new_items:
                    print(f"--- TROVATE {len(new_items)} NUOVE NOTIZIE ---")

            # 5. Stampa le notizie
            for item in items_to_show:
                print(f"\n>> [{item['source']}] - {item['timestamp']}")
                print(f"   Titolo: {item['title']}")
                if item.get('ticker'):
                    print(f"   Ticker: {item['ticker']}")
                
                print(f"   Testo: {item['text'][:100]}...") 
                print(f"   Link: {item['link']}")

            if not items_to_show and not is_first_run:
                print("Nessuna *nuova* notizia trovata.")

            # 6. Attendi per 5 minuti (300 secondi)
            print(f"\n[{current_time}] ...In attesa per 5 minuti (300 secondi)...")
            time.sleep(300) # <-- Intervallo "buonsenso"

    except KeyboardInterrupt:
        print("\n--- News Feed Monitor interrotto. ---")