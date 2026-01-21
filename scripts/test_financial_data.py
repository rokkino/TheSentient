import yfinance as yf
import pandas as pd
import json

def test_ticker_data(symbol):
    print(f"Testing data for {symbol}...")
    tk = yf.Ticker(symbol)
    
    print("\n--- Calendar ---")
    try:
        print(tk.calendar)
    except Exception as e:
        print(f"Error getting calendar: {e}")

    print("\n--- Income Statement (Quarterly) ---")
    try:
        # quarterly_financials usually contains Revenue, Net Income, etc.
        qf = tk.quarterly_financials
        if not qf.empty:
            print(qf.head())
            print("\nAvailable rows:", qf.index.tolist())
    except Exception as e:
        print(f"Error getting quarterly financials: {e}")

    print("\n--- Earnings (Quarterly) ---")
    try:
        # quarterly_earnings usually contains Revenue and Earnings
        qe = tk.quarterly_earnings
        if not qe.empty:
            print(qe)
    except Exception as e:
        print(f"Error getting quarterly earnings: {e}")

    print("\n--- Earnings History ---")
    try:
        # earnings_history might be in info or a separate method depending on version
        if 'earningsHistory' in tk.info:
            print(json.dumps(tk.info['earningsHistory'], indent=2))
        else:
            print("earningsHistory not found in info")
    except Exception as e:
        print(f"Error getting earnings history: {e}")

if __name__ == "__main__":
    test_ticker_data("AAPL")
