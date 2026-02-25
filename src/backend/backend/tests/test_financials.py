import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.market_data import MarketDataService

async def test_get_financials():
    service = MarketDataService()
    ticker = "AAPL"
    
    print(f"\nTesting get_financials for {ticker}...")
    data = await service.get_financials(ticker)
    
    # Check structure
    assert "symbol" in data
    assert data["symbol"] == ticker
    assert "quarterly_financials" in data
    assert "earnings_history" in data
    
    # Check quarterly financials
    qf = data["quarterly_financials"]
    print(f"Quarterly Financials: {len(qf)} records")
    if len(qf) > 0:
        first = qf[0]
        assert "date" in first
        assert "revenue" in first
        assert "earnings" in first
        print(f"Sample QF: {first}")
        
    # Check earnings history
    eh = data["earnings_history"]
    print(f"Earnings History: {len(eh)} records")
    if len(eh) > 0:
        first = eh[0]
        assert "date" in first
        assert "estimate" in first
        assert "actual" in first
        print(f"Sample EH: {first}")

if __name__ == "__main__":
    # Allow running directly without pytest
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_get_financials())
