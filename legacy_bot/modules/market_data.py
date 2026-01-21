import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from .utils import setup_logger

logger = setup_logger("MarketData")

def get_market_data(ticker: str, period: str = "1mo", interval: str = "1h") -> pd.DataFrame:
    """
    Fetches OHLCV data for a given ticker.
    """
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data.empty:
            logger.warning(f"No data found for {ticker}")
            return pd.DataFrame()
        return data
    except Exception as e:
        logger.error(f"Error fetching market data for {ticker}: {e}")
        return pd.DataFrame()

def get_earnings_date(ticker: str) -> str:
    """
    Fetches the next earnings date for a given ticker.
    Returns 'YYYY-MM-DD' or None if not found.
    """
    try:
        stock = yf.Ticker(ticker)
        calendar = stock.calendar
        if calendar is not None and not calendar.empty:
            # Depending on yfinance version, calendar might be a dict or DataFrame
            # Usually 'Earnings Date' or similar key
            # This part can be tricky as yfinance API changes. 
            # We will try to get the next earnings date.
            # For robustness, we'll return a string representation or None.
             if isinstance(calendar, dict):
                 earnings_date = calendar.get('Earnings Date', [None])[0]
             else:
                 # If dataframe, usually the index or a column
                 # Let's assume it returns a date object or list of dates
                 # This is a simplified implementation
                 return "Unknown" # Placeholder for complex parsing
            
             if earnings_date:
                 return earnings_date.strftime('%Y-%m-%d')
        return "Unknown"
    except Exception as e:
        logger.error(f"Error fetching earnings date for {ticker}: {e}")
        return "Unknown"

def is_market_open(ticker: str = "SPY") -> bool:
    """
    Checks if the market is currently open.
    This is a heuristic check. For precise check, we might need a market calendar library.
    For now, we rely on the Manager AI to decide based on time, but this helper can be useful.
    """
    # Simple check: is it a weekday?
    now = datetime.now()
    if now.weekday() >= 5: # 5=Sat, 6=Sun
        return False
    # Further checks can be added here
    return True
