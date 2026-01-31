"""
Ticker Data - Gestione lista S&P500, Nasdaq e settori
Con caching per ottimizzare le chiamate massive.
"""
import pandas as pd
import requests
from typing import List, Dict, Optional
import time
import os
import json

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Lista fallback S&P 500 (top ~100 per evitare file enormi - caricamento completo via API)
SP500_FALLBACK = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "JPM", "V", "PG", "XOM", "HD", "MA", "CVX", "LLY", "ABBV", "MRK",
    "KO", "PEP", "COST", "WMT", "MCD", "CSCO", "ACN", "ABT", "TMO", "AVGO",
    "NEE", "DHR", "TXN", "VZ", "ADBE", "PM", "CRM", "NKE", "CMCSA", "WFC",
    "BMY", "ORCL", "AMD", "INTC", "QCOM", "HON", "UPS", "RTX", "IBM", "AMGN",
    "CAT", "BA", "GE", "DE", "LOW", "SBUX", "AXP", "INTU", "BLK", "GILD",
    "ADI", "BKNG", "AMAT", "MDT", "ISRG", "SYK", "REGN", "LMT", "MMC", "VRTX",
    "C", "TJX", "PLD", "ZTS", "CB", "SO", "DUK", "BSX", "BDX", "SLB",
]


def _load_from_cache(key: str, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
    """Carica dati dalla cache se presenti e validi."""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data.get("timestamp", 0)
        if time.time() - ts > max_age_hours * 3600:
            return None
        return pd.DataFrame(data.get("rows", []))
    except Exception:
        return None


def _save_to_cache(key: str, df: pd.DataFrame):
    """Salva DataFrame nella cache."""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "rows": df.to_dict("records")}, f)
    except Exception:
        pass


def get_sp500_tickers(use_cache: bool = True) -> List[str]:
    """Scarica la lista S&P 500 da Wikipedia o usa fallback."""
    if use_cache:
        cached = _load_from_cache("sp500")
        if cached is not None and not cached.empty:
            return cached["Symbol"].astype(str).str.strip().tolist()

    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        symbols = df["Symbol"].astype(str).str.replace(".", "-", regex=False).tolist()
        df_out = pd.DataFrame({"Symbol": symbols})
        _save_to_cache("sp500", df_out)
        return symbols
    except Exception:
        return SP500_FALLBACK


def get_nasdaq100_tickers(use_cache: bool = True) -> List[str]:
    """Scarica la lista Nasdaq 100 da Wikipedia o usa subset S&P tech."""
    if use_cache:
        cached = _load_from_cache("nasdaq100")
        if cached is not None and not cached.empty:
            return cached["Symbol"].astype(str).str.strip().tolist()

    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tables = pd.read_html(url)
        # La tabella dei componenti è tipicamente la 4
        for t in tables:
            if "Ticker" in t.columns or "Symbol" in t.columns:
                col = "Ticker" if "Ticker" in t.columns else "Symbol"
                symbols = t[col].astype(str).str.strip().tolist()
                if len(symbols) >= 50:
                    df_out = pd.DataFrame({"Symbol": symbols})
                    _save_to_cache("nasdaq100", df_out)
                    return symbols
        # Fallback: subset tech da S&P
        sp = get_sp500_tickers(use_cache=True)
        tech = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "INTC", "QCOM",
                "ADBE", "CRM", "ORCL", "CSCO", "AVGO", "AMAT", "TXN", "INTU", "AMGN", "GILD"]
        return [t for t in tech if t in sp] or sp[:80]
    except Exception:
        return get_sp500_tickers(use_cache=True)[:80]


def get_ticker_sector(ticker: str, yf_ticker=None) -> str:
    """Ottiene il settore per un ticker (da yfinance)."""
    try:
        import yfinance as yf
        tk = yf_ticker or yf.Ticker(ticker)
        info = tk.info
        sector = info.get("sector") or info.get("industry") or "Unknown"
        return str(sector) if sector else "Unknown"
    except Exception:
        return "Unknown"


def get_tickers_with_sectors(tickers: List[str], rate_limit_delay: float = 0.15) -> Dict[str, str]:
    """Ottiene settore per ogni ticker con rate limiting."""
    result = {}
    import yfinance as yf
    tickers = list(set(t.strip().upper() for t in tickers if t))
    for i, t in enumerate(tickers):
        try:
            tk = yf.Ticker(t)
            sector = get_ticker_sector(t, yf_ticker=tk)
            result[t] = sector
        except Exception:
            result[t] = "Unknown"
        if (i + 1) % 15 == 0:
            time.sleep(rate_limit_delay)
    return result
