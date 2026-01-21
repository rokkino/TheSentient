from yahoo_fin import stock_info as si
import pandas as pd
import json

def test_yahoo_fin(symbol):
    print(f"Testing yahoo_fin data for {symbol}...")
    
    print("\n--- Earnings History ---")
    try:
        # get_earnings_history usually returns a list of dicts with epsactual, epsestimate, etc.
        history = si.get_earnings_history(symbol)
        if history:
            print(f"Found {len(history)} entries")
            print(json.dumps(history[:3], indent=2))
        else:
            print("No earnings history found")
    except Exception as e:
        print(f"Error getting earnings history: {e}")

if __name__ == "__main__":
    test_yahoo_fin("AAPL")
