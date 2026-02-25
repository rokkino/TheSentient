import sys
import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM  <-- RIMOSSO
# import requests <-- RIMOSSO
from bs4 import BeautifulSoup
import re
import os

# --- AGGIUNGI QUESTO BLOCCO ---
try:
    from curl_cffi.requests import Session as CurlSession
    import requests # Lo importiamo solo per le eccezioni
except ImportError:
    print("ERRORE: 'curl_cffi' non trovato. Esegui: pip install curl_cffi")
    CurlSession = None
    import requests # Fallback

# Variabile globale per il lazy loading
transformers = None
# --- AVVERTIMENTO DI SICUREZZA ---
print("="*80)
'''SOLO PER PAPER E TEST, IL MODELLO AI è MINUSCOLO PER ESSERE RISPETTATO DALLA CREW, NON ASCOLTARLO, DICE CAZZATE.'''
print("="*80)
# ---------------------------------

class TradingModel:
    """
    Carica un modello LLM in locale sulla CPU per eseguire
    analisi di base (sentiment, riassunto) su notizie finanziarie.
    """
    def __init__(self, session=None):
            # --- MODIFICA CHIAVE ---
            # Puntiamo alla cartella locale 'model'
            model_id = "./model" 
            # --- FINE MODIFICA ---
            
            print(f"[Model.py] Caricamento del modello dalla cartella locale: {model_id}")
            print("ATTENZIONE: Il caricamento e l'analisi sulla CPU saranno LENTI.")
            
            global transformers # Usiamo la variabile globale

            if session:
                self.session = session
            else:
                # Fallback per il test diretto (come quando esegui 'python model.py')
                if CurlSession:
                    print("[Model.py] ATTENZIONE: Nessuna sessione fornita. Creazione di una sessione curl_cffi di test.")
                    self.session = CurlSession(impersonate="chrome110")
                    self.session.verify = False # Per testare in azienda
                else:
                    print("[Model.py] ATTENZIONE: Nessuna sessione e curl_cffi non trovato. Uso requests.")
                    self.session = requests.Session()
                    self.session.verify = False

            # --- RIMOSSO IL BLOCCO os.environ ---
            # Non è più necessario, perché non stiamo scaricando.
            
            try:
                # --- LAZY IMPORT ---
                if transformers is None:
                    print("[Model.py] Importazione lazy di 'transformers'...")
                    import transformers as tr
                    transformers = tr
                # --- FINE LAZY IMPORT ---
                
                # Ora caricherà i file dalla cartella ./model
                self.tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)
                self.model = transformers.AutoModelForCausalLM.from_pretrained(
                    model_id,
                    device_map="cpu", 
                    dtype=torch.float32,
                    trust_remote_code=True
                )
                self.model.eval()
                print(f"[Model.py] Modello caricato con successo dalla cartella locale.")

            except Exception as e:
                print(f"[Model.py] ERRORE CRITICO durante il caricamento del modello: {e}")
                print(f"Verifica che la cartella '{model_id}' esista e contenga TUTTI i file del modello (config.json, ecc.).")
                self.model = None
                self.tokenizer = None

    def _get_llm_response(self, formatted_prompt):
        """Funzione helper interna per generare una risposta."""
        if not self.model or not self.tokenizer:
            return "Errore: Modello non caricato."

        # Prepara l'input per il modello
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)

        # Genera la risposta
        print("[Model.py] ...Il modello sta pensando (questo richiederà tempo su CPU)...")
        with torch.no_grad(): # Disabilita il calcolo del gradiente per risparmiare risorse
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=150, 
                pad_token_id=self.tokenizer.eos_token_id
            )
        print("[Model.py] ...Risposta generata.")
        
        # Decodifica l'output
        response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Pulisci l'output (rimuovi il prompt originale)
        clean_response = response_text.replace(formatted_prompt, "").strip()
        
        if "ASSISTANT:" in clean_response:
            clean_response = clean_response.split("ASSISTANT:")[-1].strip()
            
        return clean_response

    def check_url(self, url, session=None):
        """
        Visita un URL, estrae il testo principale e lo pulisce per l'LLM.
        """
        # --- Scegli la sessione da usare ---
        active_session = session if session else self.session
        print(f"[Model.py] Controllo URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = active_session.get(url, headers=headers, timeout=10)            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
                script_or_style.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            max_length = 2000
            if len(text) > max_length:
                text = text[:max_length] + "... (testo troncato)"
                
            print(f"[Model.py] URL letto e pulito. Lunghezza testo: {len(text)} caratteri.")
            return text

        except requests.RequestException as e:
            print(f"[Model.py] Errore durante il recupero dell'URL: {e}")
            return None
        except Exception as e:
            print(f"[Model.py] Errore during il parsing dell'HTML: {e}")
            return None

    def analyze_sentiment(self, text_content):
        """
        Analizza il sentiment di un testo.
        Risposta forzata: POSITIVE, NEGATIVE, o NEUTRAL.
        """
        if not text_content:
            return "Errore: Testo vuoto."
            
        prompt = f"""You are a financial analyst. Analyze the sentiment of the following news article.
Respond with only one word: POSITIVE, NEGATIVE, or NEUTRAL.

USER:
Article: "{text_content}"
Sentiment:

ASSISTANT:
"""
        response = self._get_llm_response(prompt)
        
        if "POSITIVE" in response.upper():
            return "POSITIVE"
        elif "NEGATIVE" in response.upper():
            return "NEGATIVE"
        else:
            return "NEUTRAL"

    def summarize_text(self, text_content):
        """
        Riassume il testo per un trader.
        """
        if not text_content:
            return "Errore: Testo vuoto."
            
        prompt = f"""You are a trading assistant. Summarize the following article for a trader in 3 bullet points.
Focus only on actionable information or market-moving statements.

USER:
Article: "{text_content}"
Summary:

ASSISTANT:
"""
        return self._get_llm_response(prompt)

    def analyze_trading_signal(self, text_content, ticker=None):
        """
        Analizza il testo e genera un segnale di trading con stop loss, take profit e confidence.
        Restituisce un dizionario con: direction (BULLISH/BEARISH/NEUTRAL), confidence (0-100),
        stop_loss, take_profit
        """
        if not text_content:
            return {
                'direction': 'NEUTRAL',
                'confidence': 0,
                'stop_loss': None,
                'take_profit': None
            }
        
        prompt = f"""You are a financial analyst. Analyze the following news article and provide a trading signal.
Respond in JSON format with these exact fields:
- "direction": "BULLISH" or "BEARISH" or "NEUTRAL"
- "confidence": a number between 0 and 100
- "stop_loss": a percentage (e.g., "-2.5%") for stop loss
- "take_profit": a percentage (e.g., "+5.0%") for take profit

Only respond with the JSON, no additional text.

Article: "{text_content[:1500]}"
Ticker: {ticker or "N/A"}

ASSISTANT:
"""
        response = self._get_llm_response(prompt)
        
        # Prova a estrarre JSON dalla risposta
        import json
        import re
        
        # Cerca JSON nella risposta
        json_match = re.search(r'\{[^}]+\}', response)
        if json_match:
            try:
                signal_data = json.loads(json_match.group())
                # Valida e normalizza i dati
                direction = signal_data.get('direction', 'NEUTRAL').upper()
                if direction not in ['BULLISH', 'BEARISH', 'NEUTRAL']:
                    direction = 'NEUTRAL'
                
                confidence = int(signal_data.get('confidence', 0))
                confidence = max(0, min(100, confidence))
                
                stop_loss = signal_data.get('stop_loss')
                take_profit = signal_data.get('take_profit')
                
                return {
                    'direction': direction,
                    'confidence': confidence,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: analisi basata su sentiment
        sentiment = self.analyze_sentiment(text_content)
        if sentiment == "POSITIVE":
            direction = "BULLISH"
            confidence = 65
        elif sentiment == "NEGATIVE":
            direction = "BEARISH"
            confidence = 65
        else:
            direction = "NEUTRAL"
            confidence = 50
        
        return {
            'direction': direction,
            'confidence': confidence,
            'stop_loss': "-2.5%" if direction != 'NEUTRAL' else None,
            'take_profit': "+5.0%" if direction == 'BULLISH' else ("-3.0%" if direction == 'BEARISH' else None)
        }


# --- 4. ESECUZIONE (per testare questo file) ---
if __name__ == "__main__":
    
    print("[Model.py] Avvio test del modulo...")
    
    try:
        model = TradingModel()
    except Exception as e:
        print(f"Impossibile inizializzare il modello. Assicurati che le dipendenze siano installate. Errore: {e}")
        sys.exit(1)

    if model.model is None:
        print("Caricamento modello fallito. Uscita.")
        sys.exit(1)
        
    test_url = "https://finance.yahoo.com/news/amazon-stock-jumps-on-38-billion-deal-with-openai-to-use-hundreds-of-thousands-of-nvidia-chips-145357373.html"

    news_text = model.check_url(test_url)
    
    if news_text:
        print("\n--- TESTO ESTRATTO (primi 500 caratteri) ---")
        print(news_text[:500] + "...")
        print("-" * 40)
        
        # 4. Analizza il Sentiment
        sentiment = model.analyze_sentiment(news_text)
        print(f"\nANALISI SENTIMENT: {sentiment}")
        print("-" * 40)
        s
        # 5. Fai un riassunto
        summary = model.summarize_text(news_text)
        print(f"\nRIASSUNTO PER TRADER:")
        print(summary)
        print("-" * 40)
        
    else:
        print("Test fallito: Impossibile recuperare il contenuto dell'URL.")
        
    print("[Model.py] Test completato.")