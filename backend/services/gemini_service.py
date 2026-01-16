"""
Gemini Service - Handles Google Gemini API calls for earnings analysis
"""
import os
from typing import Dict, Any, List, Optional
import json

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Install with: pip install google-generativeai")

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_GEMINI_API_KEY')
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-3-flash-preview')
                self.available = True
            except Exception as e:
                print(f"[GEMINI] Error initializing Gemini: {e}")
                self.available = False
                self.model = None
        else:
            self.available = False
            self.model = None
            if not self.api_key:
                print("[GEMINI] Warning: GOOGLE_GEMINI_API_KEY not set")
    
    def _safe_get_text(self, response) -> str:
        """Safely extract text from Gemini response"""
        try:
            return response.text.strip()
        except Exception as e:
            print(f"[GEMINI] Warning: Could not extract text directly: {e}")
            
            # Check for safety blocks or other issues
            try:
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    print(f"[GEMINI] Prompt feedback: {response.prompt_feedback}")
                
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    print(f"[GEMINI] Finish reason: {candidate.finish_reason}")
                    if candidate.content and candidate.content.parts:
                        return candidate.content.parts[0].text.strip()
            except Exception as inner_e:
                print(f"[GEMINI] Error inspecting response: {inner_e}")
            
            return ""
    
    async def analyze_earnings_safety(self, 
                                     symbol: str, 
                                     company: str,
                                     earnings_date: str,
                                     eps_history: List[Dict[str, Any]],
                                     reliability: Dict[str, Any],
                                     available_cash: float) -> Dict[str, Any]:
        """
        Analyze earnings safety using Gemini AI
        Returns safety score (0-100) and allocation recommendation
        """
        if not self.available or not self.model:
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
            
            prompt = f"""You are a financial analyst evaluating earnings trading opportunities.

Company: {company} ({symbol})
Earnings Date: {earnings_date}
Available Cash: ${available_cash:,.2f}

EPS History (last 2 years):
{chr(10).join(quarters_summary) if quarters_summary else 'No historical data available'}

Reliability Metrics:
- Beat Rate: {beat_rate:.2f}%
- Beat Count: {beat_count}/{total_quarters} quarters
- Miss Count: {miss_count}/{total_quarters} quarters

Based on this information, provide:
1. A safety score from 0-100 (where 100 = very safe, 0 = very risky)
2. Recommended allocation percentage (0-1.0) of available cash to invest in this stock
3. Recommendation: 'buy', 'avoid', or 'sell'
4. Brief reasoning (max 100 words)

Respond ONLY with a JSON object in this exact format:
{{
    "safety_score": <number 0-100>,
    "allocation_percentage": <number 0-1.0>,
    "recommendation": "<buy|avoid|sell>",
    "reasoning": "<brief explanation>"
}}
"""
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = self._safe_get_text(response)
            
            if not response_text:
                print("[GEMINI] Empty response received")
                return self._fallback_analysis(reliability)
            
            # Try to extract JSON from response
            # Sometimes Gemini wraps JSON in markdown code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            try:
                result = json.loads(response_text)
                
                # Validate and sanitize results
                safety_score = max(0, min(100, float(result.get('safety_score', 50))))
                allocation = max(0, min(1.0, float(result.get('allocation_percentage', 0))))
                recommendation = result.get('recommendation', 'avoid').lower()
                reasoning = result.get('reasoning', 'No reasoning provided')
                
                # Ensure recommendation is valid
                if recommendation not in ['buy', 'avoid', 'sell']:
                    recommendation = 'avoid'
                
                return {
                    'safety_score': round(safety_score, 2),
                    'allocation_percentage': round(allocation, 4),
                    'recommendation': recommendation,
                    'reasoning': reasoning,
                    'source': 'gemini'
                }
                
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

    async def chat_about_bot(self, context: str, history: List[Dict[str, str]], prompt: str) -> str:
        """Chat about bot activity with history"""
        if not self.available or not self.model:
            return "Gemini AI is not available."
            
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
            
            response = self.model.generate_content(full_prompt)
            text = self._safe_get_text(response)
            if not text:
                return "I apologize, but I couldn't generate a response at this time. The model might be busy or the request was filtered."
            return text
        except Exception as e:
            print(f"[GEMINI] Error in chat: {e}")
            return f"Error: {str(e)}"

    async def generate_explanation(self, context: str) -> str:
        """Generate explanation for bot activity"""
        if not self.available or not self.model:
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
            response = self.model.generate_content(prompt)
            text = self._safe_get_text(response)
            if not text:
                return "I couldn't generate an explanation at this time."
            return text
        except Exception as e:
            print(f"[GEMINI] Error generating explanation: {e}")
            return f"I tried to analyze the bot's activity but encountered an error: {str(e)}"
