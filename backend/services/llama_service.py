"""
Llama Service - Handles integration with local Ollama instance directly via HTTP
"""
import os
import json
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from services.web_search_service import web_search_service
from services.llm_factory import LLMFactory
from services.gemini_service import GeminiService

class LlamaService:
    def __init__(self, model_name: str = "llama3.2:1b"):
        self.model_name = model_name
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._initialized = False
        self.user_memories: Dict[int, List[Dict[str, str]]] = {}
        
        # Setup memory path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        self.memory_dir = os.path.join(backend_dir, 'memory', 'chat')
        os.makedirs(self.memory_dir, exist_ok=True)

    def _save_chat_to_memory(self, user_id: int, prompt: str, response: str, provider: str = "llama"):
        """Save chat interaction to JSON file"""
        try:
            import time
            import uuid
            
            timestamp = datetime.now().isoformat()
            
            # Create a session ID based on date/hour to group chats roughly
            # or just append to a daily file per user
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"chat_{user_id}_{date_str}.json"
            file_path = os.path.join(self.memory_dir, filename)
            
            entry = {
                "id": str(uuid.uuid4()),
                "timestamp": timestamp,
                "user_id": user_id,
                "role": "user",
                "content": prompt,
                "response": response,
                "provider": provider
            }
            
            # Append to list in file
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
            print(f"[LlamaService] Error saving chat to memory: {e}")

    def initialize(self):
        """Check if Ollama is reachable"""
        if self._initialized:
            return

        try:
            print(f"[LlamaService] Connecting to Ollama at {self.base_url} with model: {self.model_name}")
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                self._initialized = True
                print("[LlamaService] Initialization successful")
            else:
                print(f"[LlamaService] Initialization failed: Status {response.status_code}")
                self._initialized = False
        except Exception as e:
            # print(f"[LlamaService] Initialization failed: {e}")
            # Don't print error stack trace for connection refused, just mark as uninitialized
            self._initialized = False

    def _call_ollama(self, prompt: str, context: str = "", system_prompt: str = "", history: List[Dict[str, str]] = None) -> str:
        """Helper to call Ollama chat endpoint with history"""
        if not self._initialized:
            self.initialize()
            if not self._initialized:
                # Fallback logic handled in generate_response, but for direct calls:
                return "Error: Llama service is not available (Ollama not running)."

        try:
            messages = []
            
            # System message
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            elif context:
                # Default system message with context
                messages.append({"role": "system", "content": f"You are a helpful assistant. Use the following context to answer the user's question. If the answer is not in the context, use your general knowledge.\n\nContext:\n{context}"})
            else:
                messages.append({"role": "system", "content": "You are a helpful assistant."})

            # Add history
            if history:
                messages.extend(history)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_gpu": 999
                }
            }

            response = requests.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
        except Exception as e:
            print(f"[LlamaService] Error calling Ollama: {e}")
            return f"Error processing request: {str(e)}"

    def generate_response(self, prompt: str, context: str = "", user_id: Optional[int] = None, 
                         provider: str = "local", api_key: Optional[str] = None) -> str:
        """Generate response using specified provider with per-user memory"""
        history = []
        if user_id is not None:
            if user_id not in self.user_memories:
                self.user_memories[user_id] = []
            history = self.user_memories[user_id]
        
        if provider != "local" and provider != "llama" and api_key:
            # Use cloud provider
            try:
                client = LLMFactory.create_client(provider, api_key)
                if client:
                    # Construct prompt with history
                    full_prompt = ""
                    if context:
                        full_prompt += f"Context: {context}\n\n"
                    
                    for msg in history:
                        role = "User" if msg['role'] == 'user' else "Assistant"
                        full_prompt += f"{role}: {msg['content']}\n"
                    
                    full_prompt += f"User: {prompt}"
                    
                    response = client.generate_content(full_prompt)
                else:
                    response = "Error: Invalid AI provider selected."
            except Exception as e:
                print(f"[LlamaService] Error with {provider}: {e}")
                response = f"Error using {provider}: {str(e)}"
        else:
            # Use local Ollama
            if not self._initialized:
                self.initialize()
            
            if self._initialized:
                response = self._call_ollama(prompt, context, history=history)
            else:
                # Fallback to Gemini if available
                print("[LlamaService] Ollama not available, attempting fallback to Gemini...")
                gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY")
                if gemini_key:
                    try:
                        gemini = GeminiService(api_key=gemini_key)
                        # Construct prompt with context and history
                        full_prompt = ""
                        if context:
                            full_prompt += f"Context: {context}\n\n"
                        for msg in history:
                            role = "User" if msg['role'] == 'user' else "Assistant"
                            full_prompt += f"{role}: {msg['content']}\n"
                        full_prompt += f"User: {prompt}"
                        
                        response = gemini.generate_response(full_prompt)
                        response = f"[Fallback to Gemini] {response}"
                    except Exception as e:
                        response = "Error: Llama is not running and Gemini fallback failed."
                else:
                    response = "Error: Llama service is not available. Please ensure Ollama is running or configure Gemini API key."
        
        # Update memory
        if user_id is not None:
            self.user_memories[user_id].append({"role": "user", "content": prompt})
            self.user_memories[user_id].append({"role": "assistant", "content": response})
            
            # Save to disk
            self._save_chat_to_memory(user_id, prompt, response, provider)
            
            # Keep memory size manageable (last 20 messages)
            if len(self.user_memories[user_id]) > 20:
                self.user_memories[user_id] = self.user_memories[user_id][-20:]
                
        return response

    def chat_about_bot(self, context: str, history: List[Dict[str, str]], prompt: str, search_web: bool = True,
                      provider: str = "local", api_key: Optional[str] = None) -> str:
        """Chat about bot activity with history"""
        if provider != "local" and provider != "llama" and api_key:
            # Use cloud provider
            try:
                client = LLMFactory.create_client(provider, api_key)
                if not client:
                    return "Error: Invalid AI provider selected."
                
                # Construct prompt
                search_context = ""
                if search_web:
                    try:
                        search_results = web_search_service.search(prompt)
                        search_context = f"\n\nWEB SEARCH RESULTS:\n{search_results}"
                    except Exception as e:
                        print(f"Search failed: {e}")

                full_prompt = f"""You are a helpful assistant for a trading bot.
Your goal is to explain the bot's activity and answer user questions based on the provided data and web search results.

DATA SOURCE:
{context}{search_context}

CONVERSATION HISTORY:
"""
                for msg in history:
                    role = "User" if msg.get('role') == 'user' else "Assistant"
                    full_prompt += f"{role}: {msg.get('content')}\n"
                
                full_prompt += f"User: {prompt}"
                
                return client.generate_content(full_prompt)
            except Exception as e:
                return f"Error using {provider}: {str(e)}"

        if not self._initialized:
            self.initialize()
            if not self._initialized:
                return "Llama (Ollama) is not available."
        
        try:
            # Construct messages for chat endpoint
            messages = []
            
            # Perform web search if enabled
            search_context = ""
            if search_web:
                print(f"[LlamaService] Performing web search for: {prompt}")
                search_results = web_search_service.search(prompt)
                search_context = f"\n\nWEB SEARCH RESULTS:\n{search_results}"
            
            # Read real-time bot activity logs
            bot_activity_context = ""
            try:
                # Read bot activity log (last 50 lines)
                log_path = os.path.join("backend", "bot_activity.log")
                if os.path.exists(log_path):
                    with open(log_path, "r") as f:
                        lines = f.readlines()
                        recent_lines = lines[-50:] if len(lines) > 50 else lines
                        bot_activity_context += "\n\nRECENT BOT ACTIVITY LOG:\n" + "".join(recent_lines)
                
                # Read profitto.json for current P&L
                profitto_path = os.path.join("backend", "profitto.json")
                if os.path.exists(profitto_path):
                    with open(profitto_path, "r") as f:
                        profitto_data = json.load(f)
                        bot_activity_context += f"\n\nCURRENT PROFIT/LOSS STATUS:\n{json.dumps(profitto_data, indent=2)}"
                
                # If no activity found, say so
                if not bot_activity_context:
                    bot_activity_context = "\n\nNOTE: No recent bot activity found. The bot may not be active yet."
                    
            except Exception as e:
                print(f"[LlamaService] Error reading bot activity: {e}")
                bot_activity_context = "\n\nNOTE: Could not read bot activity logs."

            # System message with context
            system_message = f"""You are a helpful assistant for the Earnings Report Genius trading bot.
Your goal is to explain what the bot is currently doing, what decisions it's making, and answer user questions.

You have access to:
1. Recent bot activity logs (what the bot is analyzing and deciding)
2. Current profit/loss status
3. Web search results (if relevant)

IMPORTANT: 
- If the user asks what the bot is doing NOW, check the RECENT BOT ACTIVITY LOG
- Explain the bot's current analysis, decisions (BUY/WAIT/NO_GO), and reasoning
- If the bot is analyzing a stock, explain the market data it's looking at
- If the bot made a trade, explain why
- Be specific about stock symbols, prices, and decisions

DATA SOURCES:
{context}{bot_activity_context}{search_context}"""
            messages.append({"role": "system", "content": system_message})

            # Add history
            for msg in history:
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_gpu": 999
                }
            }

            response = requests.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
        except Exception as e:
            print(f"[LlamaService] Error in chat: {e}")
            return f"Error: {str(e)}"

    def generate_explanation(self, context: str) -> str:
        """Generate explanation for bot activity"""
        system_prompt = """You are a strict reporting assistant for a trading bot.
Your ONLY source of truth is the provided JSON data. 
DO NOT hallucinate. DO NOT make up trades, profits, or events not present in the data.
If the data is empty or missing, state that no data is available.
Based STRICTLY on the data, provide a concise summary of:
1. Current financial status (Profit/Loss, Win Rate)
2. Recent trades (Symbol, Action, Price)
3. Active positions
Keep it under 200 words. Use a professional, factual tone."""
        
        return self._call_ollama(f"Data: {context}", system_prompt=system_prompt)

    def parse_chart_request(self, query: str) -> List[Dict[str, Any]]:
        """Parse natural language chart request into structured data"""
        system_prompt = """You are a financial charting assistant. Extract the technical indicators and parameters from the user's request.
Return ONLY a JSON list of objects, where each object has the following keys:
- "indicator": The type of indicator (SMA, EMA, RSI, BB, MACD, VOL, STOCH).
- "params": A dictionary of parameters.
- "color": A suggested hex color code.

Example Response: [{"indicator": "SMA", "params": {"period": 20}, "color": "#2196F3"}]"""

        try:
            response_text = self._call_ollama(query, system_prompt=system_prompt)
            
            # Clean up response to ensure it's valid JSON
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Try parsing the whole response if it's just the array
                return json.loads(response_text)
                
        except Exception as e:
            print(f"[LlamaService] Error parsing chart request: {e}")
            # Fallback
            query_lower = query.lower()
            results = []
            if "rsi" in query_lower:
                results.append({"indicator": "RSI", "params": {"period": 14}, "color": "#9C27B0"})
            if "sma" in query_lower:
                results.append({"indicator": "SMA", "params": {"period": 20}, "color": "#2196F3"})
            if "ema" in query_lower:
                results.append({"indicator": "EMA", "params": {"period": 20}, "color": "#4CAF50"})
            if "bollinger" in query_lower:
                results.append({"indicator": "BB", "params": {"period": 20, "std_dev": 2}, "color": "#FF9800"})
            if "macd" in query_lower:
                results.append({"indicator": "MACD", "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9}, "color": "#00BCD4"})
            if "volume" in query_lower:
                results.append({"indicator": "VOL", "params": {}, "color": "#4CAF50"})
            
            return results

    def generate_strategy_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Generate a trading strategy from a natural language prompt"""
        system_prompt = """You are an expert quantitative trading strategist. 
Convert the user's trading strategy description into a structured JSON format.
The JSON structure must be exactly as follows:
{
    "name": "Strategy Name",
    "description": "Brief description",
    "entry_rules": [{"indicator": "RSI", "condition": "<", "value": 30, "params": {"period": 14}}],
    "exit_rules": [],
    "risk_management": {"stop_loss_pct": 2.0, "take_profit_pct": 4.0}
}
Return ONLY the JSON."""

        try:
            response_text = self._call_ollama(prompt, system_prompt=system_prompt)
            
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                return json.loads(response_text)
        except Exception as e:
            print(f"[LlamaService] Error generating strategy: {e}")
            return {
                "name": "Generated Strategy",
                "description": f"Strategy based on: {prompt}",
                "entry_rules": [],
                "exit_rules": [],
                "risk_management": {"stop_loss_pct": 1.0, "take_profit_pct": 2.0}
            }

    def generate_drawing(self, prompt: str, color: str, chart_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a drawing based on prompt and chart data using Llama.
        Returns a drawing object compatible with frontend.
        """
        try:
            # Prepare context from chart data
            context = ""
            if chart_data:
                # Summarize chart data
                step = max(1, len(chart_data) // 30)  # Smaller sample for Llama context window
                sampled_data = chart_data[::step]
                
                context = "Chart Data Sample (Time, Price):\n"
                for d in sampled_data:
                    context += f"T:{d.get('time')} P:{d.get('close')}\n"
                
                # Add min/max context
                all_highs = [d.get('high') for d in chart_data if d.get('high') is not None]
                all_lows = [d.get('low') for d in chart_data if d.get('low') is not None]
                if all_highs and all_lows:
                    context += f"\nPrice Range: {min(all_lows)} to {max(all_highs)}\n"
                    context += f"Time Range: {chart_data[0].get('time')} to {chart_data[-1].get('time')}\n"

            system_prompt = f"""You are a technical analysis assistant. 
Generate a JSON object for a chart drawing based on the user's request and the provided chart data.

Output Format (JSON ONLY):
{{
    "type": "line" | "square" | "circle" | "arrow" | "hline" | "vline" | "text",
    "p1": {{ "time": <timestamp>, "price": <price> }},
    "p2": {{ "time": <timestamp>, "price": <price> }}, // Optional for hline/vline/text
    "color": "{color}",
    "text": "..." // Only for type "text"
}}

Rules:
- Use the provided Chart Data to determine valid coordinates.
- "hline" needs "price". "vline" needs "time". Others need "p1" and usually "p2".
- Return ONLY valid JSON. No explanations.
"""
            
            full_prompt = f"{context}\n\nUser Request: {prompt}"
            
            response_text = self._call_ollama(full_prompt, system_prompt=system_prompt)
            
            # Clean up response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                drawing_data = json.loads(json_str)
            else:
                drawing_data = json.loads(response_text)
            
            # Add ID if missing
            if 'id' not in drawing_data:
                import uuid
                drawing_data['id'] = str(uuid.uuid4())[:8]
                
            return drawing_data

        except Exception as e:
            print(f"[LlamaService] Error generating drawing: {e}")
            # Return a safe fallback or raise
            raise e

# Singleton instance
llama_service = LlamaService()
