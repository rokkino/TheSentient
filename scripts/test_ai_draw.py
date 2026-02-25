import asyncio
import os
import sys
import json
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.backend.services.gemini_service import GeminiService
from src.backend.services.llama_service import llama_service

async def test_ai_draw():
    print("Testing AI Draw Feature...")
    
    # Mock chart data (simple uptrend)
    now = datetime.now()
    chart_data = []
    price = 100.0
    for i in range(50):
        time = (now - timedelta(days=50-i)).timestamp()
        open_p = price
        close_p = price + 1.0
        high_p = max(open_p, close_p) + 0.5
        low_p = min(open_p, close_p) - 0.5
        
        chart_data.append({
            "time": time,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p
        })
        price = close_p

    print(f"Generated {len(chart_data)} mock candles.")

    # Test Gemini
    print("\n--- Testing Gemini Service ---")
    gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if gemini_key:
        try:
            gemini = GeminiService(api_key=gemini_key)
            prompt = "Draw a trendline for this uptrend"
            print(f"Prompt: {prompt}")
            drawing = await gemini.generate_drawing(prompt, "#2196F3", chart_data)
            print("Gemini Result:")
            print(json.dumps(drawing, indent=2))
        except Exception as e:
            print(f"Gemini Test Failed: {e}")
    else:
        print("Skipping Gemini test (no API key)")

    # Test Llama
    print("\n--- Testing Llama Service ---")
    try:
        prompt = "Draw a support line at 100"
        print(f"Prompt: {prompt}")
        # Llama service is synchronous in this mock but might be async in real usage, 
        # but the method signature I added is sync. Wait, let me check.
        # generate_drawing in LlamaService is sync.
        drawing = llama_service.generate_drawing(prompt, "#FF0000", chart_data)
        print("Llama Result:")
        print(json.dumps(drawing, indent=2))
    except Exception as e:
        print(f"Llama Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_draw())
