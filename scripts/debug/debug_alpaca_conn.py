
import sys
import os
import asyncio

# Mocking the environment to match what might be happening
# But we will mostly test the direct class usage

try:
    from alpaca.trade.client import TradeClient
    from alpaca.data.historical import StockHistoricalDataClient
    print("Alpaca libraries imported successfully")
except ImportError:
    print("Alpaca libraries NOT installed")
    sys.exit(1)

async def test_connection():
    print("Testing connection with URL in API Key field...")
    
    # Values from the screenshot
    api_key = "https://paper-api.alpaca.markets/v2" 
    api_secret = "some_dummy_secret"
    paper = True
    base_url = "https://paper-api.alpaca.markets"
    
    print(f"API Key: {api_key}")
    print(f"Base URL: {base_url}")
    
    try:
        print("Initializing TradeClient...")
        client = TradeClient(
            api_key=api_key,
            secret_key=api_secret,
            base_url=base_url,
            api_version='v2'
        )
        print("TradeClient initialized (Object created).")
        
        # Now try to use it - usually this is where it might fail if it checks actively
        print("Attempting to get account...")
        account = client.get_account()
        print("Account retrieval successful!")
        print(account)
        
    except Exception as e:
        print(f"\nGenerates Error: {e}")
        print(f"Error Type: {type(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
