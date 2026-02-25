"""
AI Service - Handles AI analysis of news
"""
import sys
import os
from typing import Dict, Any, Optional
from services.llm_factory import LLMFactory

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Lazy import for model
_model = None

def load_model():
    """Lazy load model module"""
    global _model
    if _model is not None:
        return _model
    try:
        import model as _model_module
        _model = _model_module
        return _model
    except Exception as e:
        print(f"Model not available: {e}")
        return None

class AIService:
    def __init__(self):
        self.trading_model = None
        self._model_loaded = False
    
    async def analyze_news(self, news_item: Dict[str, Any], provider: str = "local", api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Analyze news item with AI"""
        
        # Use cloud provider if specified
        if provider != "local" and provider != "gemini" and api_key:
            try:
                client = LLMFactory.create_client(provider, api_key)
                if client:
                    # Extract text
                    text = news_item.get('text') or news_item.get('title', '')
                    ticker = news_item.get('ticker', 'Unknown')
                    
                    prompt = f"""You are a financial analyst. Analyze the following news article for {ticker} and provide a trading signal.
Respond in JSON format with these exact fields:
- "direction": "BULLISH" or "BEARISH" or "NEUTRAL"
- "confidence": a number between 0 and 100
- "stop_loss": a percentage (e.g., "-2.5%") for stop loss
- "take_profit": a percentage (e.g., "+5.0%") for take profit

Article: "{text[:2000]}"
"""
                    response = client.generate_content(prompt)
                    
                    # Parse JSON from response
                    import json
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
                    else:
                        return None
            except Exception as e:
                print(f"[AIService] Error with {provider}: {e}")
                # Fallback to local model
                pass

        if not self._model_loaded:
            model_module = load_model()
            if model_module:
                try:
                    self.trading_model = model_module.TradingModel()
                    if self.trading_model.model:
                        self._model_loaded = True
                except Exception as e:
                    print(f"Failed to load trading model: {e}")
                    return None
        
        if not self.trading_model or not self.trading_model.model:
            return None
        
        # Get news text
        news_text = news_item.get('text', '')
        news_link = news_item.get('link', '')
        ticker = news_item.get('ticker', '')
        
        # If no text, try to fetch from URL
        if not news_text and news_link:
            news_text = self.trading_model.check_url(news_link)
        
        if not news_text:
            news_text = news_item.get('title', '')
        
        if not news_text:
            return None
        
        # Analyze
        try:
            trading_signal = self.trading_model.analyze_trading_signal(news_text, ticker)
            return trading_signal
        except Exception as e:
            print(f"Analysis error: {e}")
            return None

