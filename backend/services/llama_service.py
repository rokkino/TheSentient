"""
Llama Service - Handles integration with local Ollama instance
"""
import os
from typing import Optional, Dict, Any, List
from langchain_community.llms import Ollama
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class LlamaService:
    def __init__(self, model_name: str = "llama3.2:1b"):
        self.model_name = model_name
        self.llm = None
        self.search = DuckDuckGoSearchRun()
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.agent = None
        self._initialized = False

    def initialize(self):
        """Initialize Ollama LLM and Agent"""
        if self._initialized:
            return

        try:
            print(f"[LlamaService] Initializing Ollama with model: {self.model_name}")
            self.llm = Ollama(
                model=self.model_name,
                callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
            )
            
            tools = [self.search]
            
            self.agent = initialize_agent(
                tools, 
                self.llm, 
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, 
                verbose=True, 
                memory=self.memory,
                handle_parsing_errors=True
            )
            
            self._initialized = True
            print("[LlamaService] Initialization successful")
        except Exception as e:
            print(f"[LlamaService] Initialization failed: {e}")
            self._initialized = False

    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using the agent"""
        if not self._initialized:
            self.initialize()
            if not self._initialized:
                return "Error: Llama service is not available. Please ensure Ollama is running."

        try:
            # Enhance prompt with context if provided
            full_prompt = prompt
            if context:
                full_prompt = f"""Context information is below.
---------------------
{context}
---------------------
Given the context information and not prior knowledge, answer the query.
Query: {prompt}
Answer:"""
            
            response = self.agent.run(full_prompt)
            return response
        except Exception as e:
            print(f"[LlamaService] Error generating response: {e}")
            return f"I encountered an error processing your request: {str(e)}"

    def chat_about_bot(self, context: str, history: List[Dict[str, str]], prompt: str) -> str:
        """Chat about bot activity with history"""
        if not self._initialized:
            self.initialize()
            if not self._initialized:
                return "Llama (Ollama) is not available."
        
        try:
            # Construct conversation history string
            history_str = ""
            for msg in history:
                role = "User" if msg.get('role') == 'user' else "Assistant"
                history_str += f"{role}: {msg.get('content')}\n"
            
            full_prompt = f"""You are a helpful assistant for a trading bot.
Your goal is to explain the bot's activity and answer user questions based on the provided data.

DATA SOURCE:
{context}

CONVERSATION HISTORY:
{history_str}

User: {prompt}
Assistant:"""

            # Use the agent or LLM directly. Since we're managing history manually here for the specific bot context,
            # we can just use the LLM or the agent. The agent has tools, which might be useful.
            # However, for strict explanation based on context, direct LLM might be safer to avoid tool hallucination.
            # But let's use the agent to keep consistency if it needs to search (though we want it to stick to data).
            # Actually, for "explanation", we want it to stick to the context.
            
            return self.agent.run(full_prompt)
        except Exception as e:
            print(f"[LlamaService] Error in chat: {e}")
            return f"Error: {str(e)}"

    def generate_explanation(self, context: str) -> str:
        """Generate explanation for bot activity"""
        if not self._initialized:
            self.initialize()
            if not self._initialized:
                return "Llama (Ollama) is not available to explain the bot's actions."
        
        try:
            prompt = f"""You are a strict reporting assistant for a trading bot.
Your ONLY source of truth is the provided JSON data below. 
DO NOT hallucinate. DO NOT make up trades, profits, or events not present in the data.
If the data is empty or missing, state that no data is available.

DATA SOURCE:
{context}

Based STRICTLY on the above data, provide a concise summary of:
1. Current financial status (Profit/Loss, Win Rate)
2. Recent trades (Symbol, Action, Price)
3. Active positions

Keep it under 200 words. Use a professional, factual tone.
"""
            return self.agent.run(prompt)
        except Exception as e:
            error_msg = str(e)
            if "WinError 10061" in error_msg or "Connection refused" in error_msg:
                print(f"[LlamaService] Connection refused: {e}")
                return "I cannot connect to Ollama. Please make sure the Ollama application is running on your computer."
            
            print(f"[LlamaService] Error generating explanation: {e}")
            return f"I tried to analyze the bot's activity but encountered an error: {str(e)}"

    def parse_chart_request(self, query: str) -> List[Dict[str, Any]]:
        """Parse natural language chart request into structured data"""
        if not self._initialized:
            self.initialize()
            if not self._initialized:
                raise Exception("Llama service is not available")

        try:
            prompt = f"""You are a financial charting assistant. Extract the technical indicators and parameters from the user's request.
            Return ONLY a JSON list of objects, where each object has the following keys:
            - "indicator": The type of indicator (SMA, EMA, RSI, BB, MACD, VOL, STOCH).
            - "params": A dictionary of parameters (e.g., "period": 20, "std_dev": 2, "fast_period": 12, "slow_period": 26, "signal_period": 9).
            - "color": A suggested hex color code for the indicator (e.g., "#FF5733").

            User Request: "{query}"

            Example 1:
            Request: "Show me the 20 day moving average"
            Response: [{{"indicator": "SMA", "params": {{"period": 20}}, "color": "#2196F3"}}]

            Example 2:
            Request: "Add RSI 14 and MACD"
            Response: [
                {{"indicator": "RSI", "params": {{"period": 14}}, "color": "#9C27B0"}},
                {{"indicator": "MACD", "params": {{"fast_period": 12, "slow_period": 26, "signal_period": 9}}, "color": "#00BCD4"}}
            ]

            Example 3:
            Request: "Bollinger bands with 20 period and 2 std dev"
            Response: [{{"indicator": "BB", "params": {{"period": 20, "std_dev": 2}}, "color": "#FF9800"}}]

            Example 4:
            Request: "Add volume and stochastic"
            Response: [
                {{"indicator": "VOL", "params": {{}}, "color": "#4CAF50"}},
                {{"indicator": "STOCH", "params": {{"k_period": 14, "d_period": 3, "slowing": 3}}, "color": "#E91E63"}}
            ]

            Response:"""
            
            response = self.agent.run(prompt)
            
            # Clean up response to ensure it's valid JSON
            import json
            import re
            
            # Find JSON block
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Try parsing the whole response
                result = json.loads(response)
                if isinstance(result, dict):
                    return [result]
                return result
                
        except Exception as e:
            print(f"[LlamaService] Error parsing chart request: {e}")
            # Fallback for simple queries if LLM fails
            query_lower = query.lower()
            results = []
            if "rsi" in query_lower:
                results.append({"indicator": "RSI", "params": {"period": 14}, "color": "#9C27B0"})
            if "sma" in query_lower or "simple moving average" in query_lower:
                results.append({"indicator": "SMA", "params": {"period": 20}, "color": "#2196F3"})
            if "ema" in query_lower or "exponential" in query_lower:
                results.append({"indicator": "EMA", "params": {"period": 20}, "color": "#4CAF50"})
            if "bollinger" in query_lower:
                results.append({"indicator": "BB", "params": {"period": 20, "std_dev": 2}, "color": "#FF9800"})
            if "macd" in query_lower:
                results.append({"indicator": "MACD", "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9}, "color": "#00BCD4"})
            if "volume" in query_lower:
                results.append({"indicator": "VOL", "params": {}, "color": "#4CAF50"})
            if "stoch" in query_lower:
                results.append({"indicator": "STOCH", "params": {"k_period": 14, "d_period": 3, "slowing": 3}, "color": "#E91E63"})
            
            if results:
                return results
            
            raise e

    def generate_strategy_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Generate a trading strategy from a natural language prompt"""
        if not self._initialized:
            self.initialize()
            if not self._initialized:
                raise Exception("Llama service is not available")

        try:
            system_prompt = """You are an expert quantitative trading strategist. 
            Convert the user's trading strategy description into a structured JSON format.
            
            The JSON structure must be exactly as follows:
            {
                "name": "Strategy Name",
                "description": "Brief description of the strategy",
                "entry_rules": [
                    {
                        "indicator": "RSI", 
                        "condition": "<", 
                        "value": 30,
                        "params": {"period": 14}
                    }
                ],
                "exit_rules": [
                    {
                        "indicator": "RSI", 
                        "condition": ">", 
                        "value": 70,
                        "params": {"period": 14}
                    }
                ],
                "risk_management": {
                    "stop_loss_pct": 2.0,
                    "take_profit_pct": 4.0
                }
            }
            
            Supported indicators: RSI, SMA, EMA, MACD, BB (Bollinger Bands), VOLUME, PRICE.
            Supported conditions: >, <, >=, <=, ==, CROSS_ABOVE, CROSS_BELOW.
            
            User Description: """
            
            full_prompt = f"{system_prompt}\n\"{prompt}\"\n\nJSON Response:"
            
            response = self.agent.run(full_prompt)
            
            # Clean up response to ensure it's valid JSON
            import json
            import re
            
            # Find JSON block
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Try parsing the whole response
                return json.loads(response)
                
        except Exception as e:
            print(f"[LlamaService] Error generating strategy: {e}")
            # Fallback/Mock response for testing if LLM fails
            return {
                "name": "Generated Strategy",
                "description": f"Strategy based on: {prompt}",
                "entry_rules": [],
                "exit_rules": [],
                "risk_management": {
                    "stop_loss_pct": 1.0,
                    "take_profit_pct": 2.0
                }
            }

# Singleton instance
llama_service = LlamaService()
