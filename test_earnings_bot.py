import asyncio
import os
import sys
from datetime import datetime, date

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from services.gemini_service import GeminiService
from dotenv import load_dotenv

load_dotenv()
print(f"GOOGLE_API_KEY present: {'GOOGLE_API_KEY' in os.environ}")
print(f"GOOGLE_GEMINI_API_KEY present: {'GOOGLE_GEMINI_API_KEY' in os.environ}")

async def test_bot_logic():
    print("Testing Earnings Genius Bot Logic...")
    
    # Try to get key from DB
    import sqlite3
    import json
    
    api_key = os.getenv('GOOGLE_GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        try:
            db_path = os.path.join("backend", "thesentient.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT config FROM bots")
            bots = cursor.fetchall()
            for (config_json,) in bots:
                try:
                    config = json.loads(config_json)
                    if config.get('gemini_api_key'):
                        api_key = config.get('gemini_api_key')
                        print("Found API key in database.")
                        break
                except:
                    pass
            conn.close()
        except Exception as e:
            print(f"Error reading DB: {e}")

    # Initialize Gemini Service
    gemini_service = GeminiService(api_key=api_key)
    if not gemini_service.available:
        print("Gemini not available. Check API Key.")
        return

    # Mock Data
    symbol = "NVDA"
    company = "NVIDIA Corporation"
    earnings_date = "2026-01-20" # Tomorrow
    available_cash = 10000.0
    current_price = 420.50
    current_time = "21:45"
    short_interest = "8%"
    iv_rank = "65%"
    
    eps_history = [
        {"quarter": "2025-Q4", "eps_actual": 4.50, "eps_estimate": 4.10, "result": "beat"},
        {"quarter": "2025-Q3", "eps_actual": 4.00, "eps_estimate": 3.80, "result": "beat"},
        {"quarter": "2025-Q2", "eps_actual": 3.50, "eps_estimate": 3.40, "result": "beat"},
        {"quarter": "2025-Q1", "eps_actual": 3.00, "eps_estimate": 2.90, "result": "beat"}
    ]
    
    reliability = {
        "beat_rate": 100.0,
        "beat_count": 4,
        "miss_count": 0,
        "quarters_with_data": 4
    }
    
    print(f"\nAnalyzing {symbol}...")
    print(f"Price: ${current_price}, Time: {current_time}, Earnings: {earnings_date}")
    
    try:
        analysis = await gemini_service.analyze_earnings_safety(
            symbol=symbol,
            company=company,
            earnings_date=earnings_date,
            eps_history=eps_history,
            reliability=reliability,
            available_cash=available_cash,
            current_price=current_price,
            current_time=current_time,
            short_interest=short_interest,
            iv_rank=iv_rank
        )
        
        print("\n--- Analysis Result ---")
        import json
        print(json.dumps(analysis, indent=2))
        
        decision = analysis.get('decision')
        print(f"\nDecision: {decision}")
        
        if decision == 'BUY':
            entry_zone = analysis.get('entry_zone', {})
            max_price = entry_zone.get('max_entry_price')
            if max_price and current_price > max_price:
                print(f"Price ${current_price} > Max Entry ${max_price} -> WAIT")
            else:
                print("Price in zone -> EXECUTE")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot_logic())
