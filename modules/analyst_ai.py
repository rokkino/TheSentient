import google.generativeai as genai
from config import GOOGLE_API_KEY, ANALYST_SYSTEM_PROMPT
from .utils import setup_logger, parse_json_response
import pandas as pd

logger = setup_logger("AnalystAI")

# Configure Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logger.warning("GOOGLE_API_KEY not found in environment variables.")

def analyze_opportunity(ticker: str, market_data: pd.DataFrame, news_summary: str = "") -> dict:
    """
    Consults the cloud Gemini model to analyze a trading opportunity.
    """
    try:
        if market_data.empty:
            logger.warning(f"No market data for {ticker}, skipping analysis.")
            return {"decision": "PASS", "reason": "No data"}

        # Prepare data summary for the prompt
        # We take the last few rows to keep the context small but relevant
        data_summary = market_data.tail(10).to_string()
        
        prompt = f"Ticker: {ticker}. Market Data (Last 10 candles):\n{data_summary}\nNews Summary: {news_summary}"
        
        logger.info(f"Consulting Analyst AI (Gemini) for {ticker}...")
        
        model = genai.GenerativeModel('gemini-1.5-flash') # Or gemini-2.0-flash if available
        
        # We can use system instruction if supported by the library version, 
        # otherwise we prepend it to the prompt. 
        # For 'gemini-1.5-flash', system_instruction is supported in newer SDKs.
        # We will prepend for compatibility if needed, but let's try to use the system_instruction arg if possible
        # or just chat.
        
        chat = model.start_chat(history=[
            {"role": "user", "parts": [ANALYST_SYSTEM_PROMPT]}
        ])
        
        response = chat.send_message(prompt)
        response_text = response.text
        
        logger.debug(f"Analyst AI Response: {response_text}")
        
        return parse_json_response(response_text)
        
    except Exception as e:
        logger.error(f"Error consulting Analyst AI: {e}")
        return {"decision": "PASS", "reason": f"Error: {e}"}
