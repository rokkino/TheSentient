"""
Gemini Service - Handles Google Gemini API calls for earnings analysis
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
from services.web_search_service import web_search_service

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-genai not installed. Install with: pip install google-genai")

class GeminiService:
    DEFAULT_MODEL = 'gemini-2.5-pro'
    # Fallback chain when quota exceeded (429): Pro -> Flash -> Flash-Lite (higher free-tier limits)
    FALLBACK_MODELS = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite']

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        model_name = (model_name or '').strip() or self.DEFAULT_MODEL
        
        # Remove 'models/' prefix if present (API adds it automatically)
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
        # Migrate older/preview model names to stable 2.5 chain
        if model_name.startswith("gemini-3") or 'preview' in model_name.lower():
            print(f"[GEMINI] Migrating '{model_name}' to '{self.DEFAULT_MODEL}' (better free-tier limits)")
            model_name = self.DEFAULT_MODEL
        
        self.model_name = model_name
        if GEMINI_AVAILABLE and self.api_key:
            try:

                # Use v1beta for preview/experimental models, v1 for stable
                api_version = 'v1'
                if any(x in self.model_name for x in ['preview', 'exp', 'gemini-3', 'latest']):
                    api_version = 'v1beta'
                
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options={'api_version': api_version}
                )
                self.available = True
                print(f"[GEMINI] Initialized with model '{self.model_name}' using API {api_version}")
            except Exception as e:
                print(f"[GEMINI] Error initializing Gemini: {e}")
                self.available = False
                self.client = None
        else:
            self.available = False
            self.client = None
            if not self.api_key:
                print("[GEMINI] Warning: GOOGLE_GEMINI_API_KEY not set")
        
        self.user_memories: Dict[int, List[Dict[str, str]]] = {}
        
        # Setup memory paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        self.chat_memory_dir = os.path.join(backend_dir, 'memory', 'chat')
        self.decision_memory_dir = os.path.join(backend_dir, 'memory', 'bot', 'decisions')
        
        os.makedirs(self.chat_memory_dir, exist_ok=True)
        os.makedirs(self.decision_memory_dir, exist_ok=True)
    
    def _safe_get_text(self, response) -> str:
        """Safely extract text from Gemini response"""
        try:
            return response.text.strip()
        except Exception as e:
            print(f"[GEMINI] Warning: Could not extract text directly: {e}")
            return ""

    def _is_quota_error(self, e: Exception) -> bool:
        """Check if exception is a 429/quota exhausted error"""
        msg = str(e).lower()
        return '429' in msg or 'resource_exhausted' in msg or 'quota' in msg

    def _generate_with_fallback(self, contents, **kwargs):
        """Call generate_content with fallback chain on 429 quota errors."""
        models_to_try = [self.model_name]
        for m in self.FALLBACK_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)
        last_error = None
        for model in models_to_try:
            try:
                return self.client.models.generate_content(model=model, contents=contents, **kwargs)
            except Exception as e:
                last_error = e
                if self._is_quota_error(e) and model != models_to_try[-1]:
                    next_idx = models_to_try.index(model) + 1
                    print(f"[GEMINI] Quota exceeded for {model}, falling back to {models_to_try[next_idx]}...")
                    continue
                raise
        raise last_error or RuntimeError("All models exhausted")

    def _save_chat_to_memory(self, user_id: int, prompt: str, response: str):
        """Save chat interaction to JSON file"""
        try:
            import uuid
            timestamp = datetime.now().isoformat()
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"chat_{user_id}_{date_str}.json"
            file_path = os.path.join(self.chat_memory_dir, filename)
            
            entry = {
                "id": str(uuid.uuid4()),
                "timestamp": timestamp,
                "user_id": user_id,
                "role": "user",
                "content": prompt,
                "response": response,
                "provider": "gemini"
            }
            
            data = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = []
            
            data.append(entry)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[GEMINI] Error saving chat to memory: {e}")

    def _save_decision_to_memory(self, symbol: str, decision_data: Dict[str, Any]):
        """Save bot decision to JSON file"""
        try:
            import uuid
            timestamp = datetime.now().isoformat()
            date_str = datetime.now().strftime("%Y-%m-%d")
            # Use symbol and date for filename
            filename = f"decision_{symbol}_{date_str}.json"
            file_path = os.path.join(self.decision_memory_dir, filename)
            
            entry = {
                "id": str(uuid.uuid4()),
                "timestamp": timestamp,
                "symbol": symbol,
                "data": decision_data
            }
            
            # Append if exists (multiple decisions per day possible)
            data = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict): # Handle legacy if any
                            data = [data]
                except:
                    data = []
            
            data.append(entry)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"[GEMINI] Error saving decision to memory: {e}")
    
    async def analyze_earnings_safety(self, 
                                     symbol: str, 
                                     company: str,
                                     earnings_date: str,
                                     eps_history: List[Dict[str, Any]],
                                     reliability: Dict[str, Any],
                                     available_cash: float,
                                     current_price: float = 0.0,
                                     current_time: str = "",
                                     short_interest: str = "N/A",
                                     iv_rank: str = "N/A") -> Dict[str, Any]:
        """
        Analyze earnings safety using Gemini AI
        Returns safety score (0-100) and allocation recommendation
        """
        if not self.available or not self.client:
            # Fallback: simple safety score based on reliability
            beat_rate = reliability.get('beat_rate', 0)
            safety_score = beat_rate  # Simple: use beat rate as safety score
            return {
                'safety_score': round(safety_score, 2),
                'allocation_percentage': min(safety_score / 100, 0.3),  # Max 30% per stock
                'recommendation': 'buy' if safety_score >= 50 else 'avoid',
                'reasoning': f'Based on {reliability.get("beat_count", 0)} beats in {reliability.get("quarters_with_data", 0)} quarters'
            }
        
        try:
            # Prepare context for Gemini
            quarters_summary = []
            if eps_history:
                for q in eps_history[:8]:  # Last 8 quarters
                    result = q.get('result', 'unknown')
                    eps_actual = q.get('eps_actual')
                    eps_estimate = q.get('eps_estimate')
                    quarter = q.get('quarter', '')
                    
                    if eps_actual is not None and eps_estimate is not None:
                        quarters_summary.append(
                            f"{quarter}: Actual {eps_actual:.2f} vs Estimate {eps_estimate:.2f} ({result})"
                        )
            
            beat_rate = reliability.get('beat_rate', 0)
            beat_count = reliability.get('beat_count', 0)
            miss_count = reliability.get('miss_count', 0)
            total_quarters = reliability.get('quarters_with_data', 0)
            
            # Read system prompt file
            system_prompt = ""
            try:
                prompt_path = os.path.join("backend", "memory", "bot", "earning_report_genius", "system_prompt_gemini.txt")
                if os.path.exists(prompt_path):
                    with open(prompt_path, "r", encoding="utf-8") as f:
                        system_prompt = f.read()
                else:
                    # Fallback to strategy.md if system prompt doesn't exist
                    strategy_path = os.path.join("backend", "memory", "bot", "earning_report_genius", "strategy.md")
                    if os.path.exists(strategy_path):
                        with open(strategy_path, "r", encoding="utf-8") as f:
                            system_prompt = f.read()
            except Exception as e:
                print(f"[GEMINI] Warning: Could not read system prompt file: {e}")

            prompt = f"""{system_prompt}

*** DATI ATTUALI DAL MERCATO ***
Ticker: {symbol}
Company: {company}
Prezzo Attuale: ${current_price}
Orario attuale: {current_time}
Earnings Date: {earnings_date}
Short Interest: {short_interest}
IV Rank: {iv_rank}
Available Cash: ${available_cash:,.2f}

EPS History (last 2 years):
{chr(10).join(quarters_summary) if quarters_summary else 'No historical data available'}

Reliability Metrics:
- Beat Rate: {beat_rate:.2f}%
- Beat Count: {beat_count}/{total_quarters} quarters
- Miss Count: {miss_count}/{total_quarters} quarters

ANALIZZA E DAMMI IL JSON.
"""
            
            # Call Gemini API (with fallback on 429)
            response = self._generate_with_fallback(prompt)
            response_text = self._safe_get_text(response)
            
            if not response_text:
                print("[GEMINI] Empty response received")
                return self._fallback_analysis(reliability)
            
            # Try to extract JSON from response
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            try:
                result = json.loads(response_text)
                
                # Validate and sanitize results
                decision = result.get('decision', 'NO_GO')
                confidence = max(0, min(100, float(result.get('confidence_score', 0))))
                
                # Map to old format for compatibility if needed, but prefer new format
                return {
                    'decision': decision,
                    'confidence_score': confidence,
                    'reasoning_summary': result.get('reasoning_summary', 'No reasoning provided'),
                    'entry_zone': result.get('entry_zone', {}),
                    'stop_loss_pre_earning': result.get('stop_loss_pre_earning'),
                    'warning_flag': result.get('warning_flag', 'Nessuno'),
                    
                    # Backwards compatibility fields for bot_service
                    'safety_score': confidence,
                    'allocation_percentage': 0.1 if decision == 'BUY' else 0.0, # Default 10% if BUY, else 0
                    'recommendation': 'buy' if decision == 'BUY' else 'avoid',
                    'reasoning': result.get('reasoning_summary', ''),
                    'source': 'gemini'
                }
                
                # Save decision to memory
                self._save_decision_to_memory(symbol, final_result)
                
                return final_result
                
            except json.JSONDecodeError as e:
                print(f"[GEMINI] Error parsing Gemini response: {e}")
                print(f"[GEMINI] Response text: {response_text[:200]}")
                # Fallback
                return self._fallback_analysis(reliability)
                
        except Exception as e:
            print(f"[GEMINI] Error calling Gemini API: {e}")
            import traceback
            traceback.print_exc()
            # Fallback
            return self._fallback_analysis(reliability)
    
    def _fallback_analysis(self, reliability: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when Gemini is not available"""
        beat_rate = reliability.get('beat_rate', 0)
        safety_score = beat_rate
        allocation = min(safety_score / 100, 0.3)  # Max 30% per stock
        
        return {
            'safety_score': round(safety_score, 2),
            'allocation_percentage': round(allocation, 4),
            'recommendation': 'buy' if safety_score >= 50 else 'avoid',
            'reasoning': f'Based on {reliability.get("beat_count", 0)} beats in {reliability.get("quarters_with_data", 0)} quarters (fallback analysis)',
            'source': 'fallback'
        }

    def generate_response(self, prompt: str, context: str = "", user_id: Optional[int] = None) -> str:
        """Generate response for general chat with per-user memory"""
        if not self.available or not self.client:
            return "Gemini AI is not available. Please check your API key."

        try:
            # Manage history
            history = []
            if user_id is not None:
                if user_id not in self.user_memories:
                    self.user_memories[user_id] = []
                history = self.user_memories[user_id]

            # Construct prompt with history
            full_prompt = ""
            if context:
                full_prompt += f"Context: {context}\n\n"
            
            # Add history to prompt (since Gemini API handles history differently, we'll just append it to prompt for simplicity here, 
            # or we could use start_chat if we wanted to maintain session object, but stateless is easier for this service pattern)
            for msg in history:
                role = "User" if msg['role'] == 'user' else "Assistant"
                full_prompt += f"{role}: {msg['content']}\n"
            
            full_prompt += f"User: {prompt}\nAssistant:"

            # Call Gemini (with fallback on 429)
            response = self._generate_with_fallback(full_prompt)
            response_text = self._safe_get_text(response)
            
            if not response_text:
                return "I apologize, but I couldn't generate a response."

            # Update memory
            if user_id is not None:
                self.user_memories[user_id].append({"role": "user", "content": prompt})
                self.user_memories[user_id].append({"role": "assistant", "content": response_text})
                
                # Keep memory size manageable (last 20 messages)
                if len(self.user_memories[user_id]) > 20:
                    self.user_memories[user_id] = self.user_memories[user_id][-20:]
            
            # Save to disk
            if user_id is not None:
                self._save_chat_to_memory(user_id, prompt, response_text)
            
            return response_text

        except Exception as e:
            print(f"[GEMINI] Error generating response: {e}")
            return f"Error: {str(e)}"

    async def chat_about_bot(self, context: str, history: List[Dict[str, str]], prompt: str, search_web: bool = True) -> str:
        """Chat about bot activity with history"""
        if not self.available or not self.client:
            return "Gemini AI is not available."
            
        try:
            # Construct conversation history string
            history_str = ""
            for msg in history:
                role = "User" if msg.get('role') == 'user' else "Assistant"
                history_str += f"{role}: {msg.get('content')}\n"
            
            # Perform web search if enabled
            search_context = ""
            if search_web:
                try:
                    print(f"[GEMINI] Performing web search for: {prompt}")
                    # Run search in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    search_results = await loop.run_in_executor(None, web_search_service.search, prompt)
                    search_context = f"\n\nWEB SEARCH RESULTS:\n{search_results}"
                except Exception as e:
                    print(f"[GEMINI] Search failed: {e}")

            full_prompt = f"""You are a helpful assistant for a trading bot.
Your goal is to explain the bot's activity and answer user questions based on the provided data and web search results.

DATA SOURCE:
{context}{search_context}

CONVERSATION HISTORY:
{history_str}

User: {prompt}
Assistant:"""
            
            response = self._generate_with_fallback(full_prompt)
            text = self._safe_get_text(response)
            if not text:
                return "I apologize, but I couldn't generate a response at this time. The model might be busy or the request was filtered."
            return text
        except Exception as e:
            print(f"[GEMINI] Error in chat: {e}")
            return f"Error: {str(e)}"

    async def generate_explanation(self, context: str) -> str:
        """Generate explanation for bot activity"""
        if not self.available or not self.client:
            return "Gemini AI is not available to explain the bot's actions."
            
        try:
            prompt = f"""You are an AI assistant explaining the actions of a trading bot called 'Earnings Report Genius'.
The user wants to know what the bot has been doing and how it's performing.

Here is the context including recent activity logs and profit status:
{context}

Please provide a concise, friendly summary of:
1. The bot's current financial status (profit/loss)
2. Recent trading actions (what it bought/sold and why, if mentioned)
3. Any issues or errors noted in the logs

Keep it under 200 words. Be professional but conversational.
"""
            response = self._generate_with_fallback(prompt)
            text = self._safe_get_text(response)
            if not text:
                return "I couldn't generate an explanation at this time."
            return text
        except Exception as e:
            print(f"[GEMINI] Error generating explanation: {e}")
            return f"I tried to analyze the bot's activity but encountered an error: {str(e)}"

    async def generate_drawing(self, prompt: str, color: str, chart_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a drawing based on prompt and chart data.
        Returns a drawing object compatible with frontend.
        """
        if not self.available or not self.client:
            raise Exception("Gemini AI is not available")

        try:
            # Prepare context from chart data
            context = ""
            if chart_data:
                # Summarize chart data to keep prompt size manageable
                # We'll take a sample of points to give the AI an idea of the trend and price range
                step = max(1, len(chart_data) // 50)  # Limit to ~50 points
                sampled_data = chart_data[::step]
                
                context = "Chart Data (Time, Open, High, Low, Close):\n"
                for d in sampled_data:
                    # Convert timestamp to readable date if possible, or keep as is
                    # Assuming time is unix timestamp in seconds or milliseconds
                    context += f"T:{d.get('time')} O:{d.get('open')} H:{d.get('high')} L:{d.get('low')} C:{d.get('close')}\n"
                
                # Add min/max context
                all_highs = [d.get('high') for d in chart_data if d.get('high') is not None]
                all_lows = [d.get('low') for d in chart_data if d.get('low') is not None]
                if all_highs and all_lows:
                    context += f"\nPrice Range: {min(all_lows)} to {max(all_highs)}\n"
                    context += f"Time Range: {chart_data[0].get('time')} to {chart_data[-1].get('time')}\n"

            system_prompt = f"""You are a technical analysis assistant. 
The user wants you to draw on a financial chart based on their request.
You must return a JSON object representing the drawing.

Available drawing types and their required fields:
1. "line": {{ "type": "line", "p1": {{ "time": <timestamp>, "price": <price> }}, "p2": {{ "time": <timestamp>, "price": <price> }}, "color": "{color}" }}
2. "square": {{ "type": "square", "p1": {{ "time": <timestamp>, "price": <price> }}, "p2": {{ "time": <timestamp>, "price": <price> }}, "color": "{color}" }}
3. "circle": {{ "type": "circle", "p1": {{ "time": <timestamp>, "price": <price> }}, "p2": {{ "time": <timestamp>, "price": <price> }}, "color": "{color}" }}
4. "arrow": {{ "type": "arrow", "p1": {{ "time": <timestamp>, "price": <price> }}, "p2": {{ "time": <timestamp>, "price": <price> }}, "color": "{color}" }}
5. "hline": {{ "type": "hline", "price": <price>, "color": "{color}" }} (Horizontal Line)
6. "vline": {{ "type": "vline", "time": <timestamp>, "color": "{color}" }} (Vertical Line)
7. "text": {{ "type": "text", "p1": {{ "time": <timestamp>, "price": <price> }}, "text": "Your text here", "color": "{color}" }}

Rules:
- Use the provided Chart Data to determine appropriate coordinates (time and price).
- Ensure the coordinates are within the Price Range and Time Range provided.
- For "support" or "resistance", use "hline" or "line".
- For "trendline", use "line".
- For "box" or "zone", use "square".
- For specific patterns (like "bull flag"), try to draw the main trendlines.
- Return ONLY the JSON object. Do not include markdown formatting or explanations.

User Request: {prompt}

{context}
"""
            response = self._generate_with_fallback(system_prompt)
            text = self._safe_get_text(response)
            
            # Clean up response
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            drawing_data = json.loads(text)
            
            # Add ID if missing
            if 'id' not in drawing_data:
                import uuid
                drawing_data['id'] = str(uuid.uuid4())[:8]
                
            return drawing_data

        except Exception as e:
            print(f"[GEMINI] Error generating drawing: {e}")
            raise e

    async def analyze_market_opportunities(self, earnings_list: List[Dict[str, Any]], current_market_data: Dict[str, Any], current_time: str = "") -> List[Dict[str, Any]]:
        """
        Analyze a list of earnings and market data to generate trading decisions.
        Follows the user's specific rules:
        1. Big Cap + Positive Trend -> Immediate Entry
        2. Others -> Entry at 21:50
        """
        if not self.available or not self.client:
            print("[GEMINI] Service not available for market analysis")
            return []

        try:
            # Prepare context
            earnings_context = ""
            for item in earnings_list:
                symbol = item.get('symbol')
                earnings_context += f"- {symbol}: {item.get('company', '')} (Time: {item.get('time', 'N/A')})\n"
                # Add market data if available
                if symbol in current_market_data:
                    data = current_market_data[symbol]
                    earnings_context += f"  Price: {data.get('price')}, Trend (1w): {data.get('trend_1w', 'Unknown')}\n"

            prompt = f"""
Sei un analista finanziario esperto. Analizza questi dati sugli utili aziendali previsti per il post-market di oggi e il pre-market di domani.

DATI ATTUALI:
Orario attuale (Server Time): {current_time}

DATI EARNINGS:
{earnings_context}

REGOLE DI TRADING (CRITICHE):
1. SELEZIONE SETTORIALE: DEVI considerare SOLAMENTE le aziende che operano nei settori "DIFESA" (Defense, Aerospace) o "INTELLIGENZA ARTIFICIALE" (AI, Semiconductor, Cloud Computing per AI).
   - IGNORA COMPLETAMENTE tutte le altre aziende (es. Retail, Farmaceutico, ecc.), restituendo "NO_GO" o omettendo l'output.
2. TIMING EARNINGS: Considera SOLO aziende che riportano utili in:
   - POST-MARKET di OGGI (After Market Close / AMC).
   - PRE-MARKET di DOMANI (Before Market Open / BMO).
   - Ignora chi ha già riportato (oggi BMO).
3. ORARIO DI ESECUZIONE:
   - Se l'opportunità è ESTREMAMENTE CHIARA (Big Cap + Trend molto positivo), execution_time = "IMMEDIATE".
   - Per TUTTI GLI ALTRI CASI (la norma), l'ordine deve essere preparato per la chiusura del mercato: execution_time = "21:59".
4. DECISIONE: Determina se è un BUY o SELL basandoti sui dati. Se incerto, WAIT.
5. CONFIDENCE: Valuta la tua fiducia nella decisione (0-100). Solo le decisioni con confidence >= 50 saranno considerate.

OUTPUT RICHIESTO:
Restituisci SOLAMENTE un array JSON valido. Nessun markdown.
Formato:
[
  {{
    "symbol": "PLTR",
    "decision": "BUY",
    "confidence_score": 75,
    "execution_time": "21:59",
    "reasoning": "Settore Difesa/AI. Utili previsti in crescita..."
  }}
]
"""
            print(f"[GEMINI] Sending analysis prompt...")
            response = self._generate_with_fallback(prompt)
            text = self._safe_get_text(response)
            
            # Clean up response
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            decisions = json.loads(text)
            print(f"[GEMINI] Generated {len(decisions)} decisions")
            return decisions

        except Exception as e:
            print(f"[GEMINI] Error in analyze_market_opportunities: {e}")
            import traceback
            traceback.print_exc()
            return []
