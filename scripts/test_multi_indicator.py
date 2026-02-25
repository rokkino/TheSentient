import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.backend.services.market_data import MarketDataService

async def test_multi_indicator():
    service = MarketDataService()
    ticker = "AAPL"
    timeframe = "1y"
    
    configs = [
        {"indicator": "SMA", "params": {"period": 20}},
        {"indicator": "RSI", "params": {"period": 14}}
    ]
    
    print(f"Testing calculate_indicator with {len(configs)} configs...")
    try:
        results = await service.calculate_indicator(ticker, timeframe, configs)
        
        print(f"Received {len(results)} results")
        
        for res in results:
            print(f"- Indicator: {res['indicator']}")
            print(f"  Data points: {len(res['data'])}")
            if res['data']:
                print(f"  First point: {res['data'][0]}")
                
        if len(results) == 2:
            print("SUCCESS: Received 2 indicator results")
        else:
            print("FAILURE: Did not receive 2 results")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_multi_indicator())
