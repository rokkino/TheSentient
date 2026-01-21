from stockdex import Ticker
import pandas as pd

def test_stockdex_data(symbol):
    print(f"Testing stockdex data for {symbol}...")
    ticker = Ticker(symbol)
    
    print("\n--- Finviz Earnings Data ---")
    try:
        # finviz_earnings_data usually contains Date, Estimate, Actual, Surprise
        earnings = ticker.finviz_earnings_data()
        if earnings is not None and not earnings.empty:
            print(earnings.head())
            print("\nColumns:", earnings.columns.tolist())
    except Exception as e:
        print(f"Error getting finviz earnings: {e}")

    print("\n--- Digrin Earnings Data ---")
    try:
        # digrin might have historical data too
        digrin = ticker.digrin_upcoming_estimated_earnings()
        if digrin is not None and not digrin.empty:
            print(digrin.head())
    except Exception as e:
        print(f"Error getting digrin earnings: {e}")

    print("\n--- Yahoo Finance (via stockdex) ---")
    try:
        # stockdex might wrap yahoo finance differently
        yf_data = ticker.yahoo_api_earnings_history()
        if yf_data is not None and not yf_data.empty:
            print(yf_data.head())
    except Exception as e:
        print(f"Error getting yahoo earnings history via stockdex: {e}")

if __name__ == "__main__":
    test_stockdex_data("AAPL")
