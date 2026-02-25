import os
import sys
import asyncio

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from models.user import SessionLocal
from models.bot import Bot
from services.bot_service import bot_service
from services.alpaca_service import AlpacaService

async def test_alpaca():
    db = SessionLocal()
    b = db.query(Bot).filter(Bot.name == "Earnings Report Genius").first()
    
    svc = bot_service._get_configured_service(db, b)
    if isinstance(svc, AlpacaService):
        print("Got AlpacaService!")
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        
        req = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=100)
        orders = svc.client.get_orders(filter=req)
        
        print(f"Total orders fetched: {len(orders)}")
        if len(orders) > 0:
            filled = [o for o in orders if getattr(o, 'status', None) == 'filled' or (hasattr(o, 'status') and 'filled' in str(o.status).lower())]
            print(f"Number of 'filled' orders: {len(filled)}")
            if len(filled) > 0:
                print("First filled order status:", filled[0].status)
            
        print("-------------")
        from alpaca.trading.requests import GetPortfolioHistoryRequest
        req_hist = GetPortfolioHistoryRequest(period="1A", timeframe="1D")
        hist = svc.client.get_portfolio_history(req_hist)
        print("Portfolio history base value:", getattr(hist, 'base_value', None))
        
        if hist and hasattr(hist, 'timestamp') and hist.timestamp:
             ts = hist.timestamp
             eq = hist.equity
             
             print(f"Num pts: {len(ts)}")
             print(f"First eq: {eq[0]}")
             changed = [e for e in eq if e and float(e) != float(eq[0])]
             print(f"Num points where equity changed from initial: {len(changed)}")
             if changed:
                 print(f"First changed equity: {changed[0]}")
                 print(f"Last equity: {eq[-1]}")
    else:
        print("Service is not AlpacaService", type(svc))

if __name__ == "__main__":
    asyncio.run(test_alpaca())
