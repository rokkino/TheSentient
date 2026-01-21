"""
Test market data service
"""
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from services.market_data_service import market_data_service

symbols = ['NVDA', 'AAPL', 'TSLA']

print("=== Testing Market Data Service ===\n")

for symbol in symbols:
    print(f"\n{symbol}:")
    data = market_data_service.get_stock_data(symbol)
    
    print(f"  Price: ${data.get('current_price')}")
    print(f"  P/E Ratio: {data.get('pe_ratio')}")
    print(f"  Short Interest: {data.get('short_interest')}")
    print(f"  IV Rank: {data.get('iv_rank')}")
    print(f"  2-Week Change: {data.get('two_week_change_pct')}%")
    print(f"  Run-up Warning: {data.get('run_up_warning')}")
    
    analyst = market_data_service.get_analyst_revisions(symbol)
    print(f"  Analyst Trend: {analyst.get('trend')}")
    print(f"  Upgrades: {analyst.get('upgrades')}, Downgrades: {analyst.get('downgrades')}")
