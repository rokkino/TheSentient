import asyncio
import os
import sys

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

from services.alpaca_service import AlpacaService

async def main():
    print("Testing Alpaca portfolio history...")
    from alpaca.trading.requests import GetPortfolioHistoryRequest
    
    svc = AlpacaService()
    
    if svc.client is None:
        print("API keys not loaded.")
        return
        
    try:
        req = GetPortfolioHistoryRequest(period="1M", timeframe="1D")
        history = svc.client.get_portfolio_history(req)
        print("History len:", len(history.timestamp) if history.timestamp else 0)
        if history.timestamp:
            for ts, eq, pl in zip(history.timestamp[-5:], history.equity[-5:], history.profit_loss[-5:]):
                print(f"TS: {ts}, EQ: {eq}, PL: {pl}")
    except Exception as e:
        print("Error:", e)
        
if __name__ == "__main__":
    asyncio.run(main())
