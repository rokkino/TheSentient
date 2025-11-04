import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import requests
from bs4 import BeautifulSoup
import re

# --- AVVERTIMENTO DI SICUREZZA ---
print("="*80)
print("AVVISO: Questo script carica un Modello di Linguaggio (LLM) per analisi.")
print("NON USARE QUESTO SCRIPT PER DECISIONI DI TRADING REALI.")
print("I modelli locali 'piccoli' NON sono affidabili per previsioni finanziarie.")
print("USARE SOLO A SCOPO DIDATTICO E SPERIMENTALE. Rischio di perdita totale.")
print("="*80)
# ---------------------------------

class TradingModel:
    """
    Carica un modello LLM in locale sulla CPU per eseguire
    analisi di base (sentiment, riassunto) su notizie finanziarie.
    """
    def __init__(self):
        model_id = "deepseek-ai/deepseek-coder-1.3b-instruct"
        
        print(f"[Model.py] Caricamento del modello: {model_id} su CPU.")
        print("Questo potrebbe richiedere alcuni minuti e scaricherà ~1.3GB di dati la prima volta...")
        print("ATTENZIONE: Il caricamento e l'analisi sulla CPU saranno LENTI.")

        try:
            # Carica il modello e il tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                # --- MODIFICHE PER LA CPU ---
                # Rimosso: quantization_config (non serve senza GPU)
                device_map="cpu",             # <-- Forzato l'uso della CPU
                torch_dtype=torch.float32,    # Usa la precisione standard per la CPU
                # --- FINE MODIFICHE ---
                trust_remote_code=True
            )
            self.model.eval() # Modalità valutazione
            print(f"[Model.py] Modello caricato con successo sulla CPU.")

        except Exception as e:
            print(f"[Model.py] ERRORE CRITICO durante il caricamento del modello: {e}")
            print("Verifica di avere installato: transformers, torch")
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

    def check_url(self, url):
        """
        Visita un URL, estrae il testo principale e lo pulisce per l'LLM.
        """
        print(f"[Model.py] Controllo URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
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
        
        # 5. Fai un riassunto
        summary = model.summarize_text(news_text)
        print(f"\nRIASSUNTO PER TRADER:")
        print(summary)
        print("-" * 40)
        
    else:
        print("Test fallito: Impossibile recuperare il contenuto dell'URL.")
        
    print("[Model.py] Test completato.")