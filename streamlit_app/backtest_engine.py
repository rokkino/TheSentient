"""
Backtest Engine - Simulazione storica per Earning Report Genius
Data Ingestion, Simulation Loop, Output aggregato.
"""
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Callable, Generator
import pandas as pd
import yfinance as yf
import requests
import os
import json

# Rate limit per yfinance/API
RATE_LIMIT_DELAY = 0.15
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache", "backtest")
os.makedirs(CACHE_DIR, exist_ok=True)


# ============== BOT LOGIC PLACEHOLDER ==============
# Sostituisci questa funzione con la tua logica Earning Report Genius.
# Riceve: ticker, earnings_date, pre_price, ohlc_history, earning_info
# Ritorna: {"decision": "BUY"|"WAIT"|"NO_GO", "confidence_score": 0-100}

def bot_logic_placeholder(
    ticker: str,
    earnings_date: date,
    pre_price: float,
    ohlc_history: pd.DataFrame,
    earning_info: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Placeholder per la logica Earning Report Genius.
    Implementa euristiche semplificate basate sulla strategy.md:
    - Run-up > 10% nelle ultime 2 settimane -> NO_GO (Sell the news risk)
    - Run-up < 5% e volume normale -> BUY
    - Altrimenti -> WAIT
    """
    if ohlc_history is None or ohlc_history.empty or pre_price <= 0:
        return {"decision": "WAIT", "confidence_score": 0, "reasoning": "Dati insufficienti"}

    try:
        # Calcola run-up nelle ultime 2 settimane (10 trading days)
        ohlc = ohlc_history.copy()
        ohlc.index = pd.to_datetime(ohlc.index)
        ohlc = ohlc.sort_index()
        cutoff = pd.Timestamp(earnings_date) - pd.Timedelta(days=15)
        recent = ohlc[ohlc.index <= pd.Timestamp(earnings_date)].tail(10)

        if len(recent) < 3:
            return {"decision": "WAIT", "confidence_score": 20, "reasoning": "Storia prezzi insufficiente"}

        start_price = float(recent["Close"].iloc[0])
        run_up_pct = ((pre_price - start_price) / start_price) * 100 if start_price > 0 else 0

        # Euristica Earning Report Genius: evitare run-up eccessivo
        if run_up_pct > 10:
            return {"decision": "NO_GO", "confidence_score": 70, "reasoning": f"Run-up {run_up_pct:.1f}% - Sell the news risk"}
        elif run_up_pct < 5 and run_up_pct > -5:
            return {"decision": "BUY", "confidence_score": 55, "reasoning": f"Run-up moderato {run_up_pct:.1f}%"}
        elif run_up_pct < -5:
            # Fear dip - potenziale buy the dip
            return {"decision": "BUY", "confidence_score": 60, "reasoning": f"Fear dip {run_up_pct:.1f}% rilevato"}
        else:
            return {"decision": "WAIT", "confidence_score": 40, "reasoning": f"Run-up {run_up_pct:.1f}% - zona grigia"}
    except Exception as e:
        return {"decision": "WAIT", "confidence_score": 0, "reasoning": str(e)}


# ============== DATA INGESTION ==============

def _get_earnings_from_nasdaq(target_date: date) -> List[Dict[str, Any]]:
    """Recupera earnings per una data dalla Nasdaq API."""
    try:
        date_str = target_date.strftime("%Y-%m-%d")
        url = "https://api.nasdaq.com/api/calendar/earnings"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.nasdaq.com/",
        }
        resp = requests.get(url, headers=headers, params={"date": date_str}, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        rows = data.get("data", {}).get("rows", [])
        result = []
        for row in rows:
            if isinstance(row, dict):
                symbol = str(row.get("symbol", "")).strip().upper()
                if symbol and len(symbol) <= 10:
                    time_str = str(row.get("time", "TBD")).lower()
                    time_info = "After Market Close" if "after" in time_str else "Before Market Open" if "before" in time_str else "TBD"
                    result.append({
                        "symbol": symbol,
                        "company": row.get("name", symbol),
                        "date": date_str,
                        "time": time_info,
                    })
        return result
    except Exception:
        return []


def _get_ohlc_for_date(ticker: str, target_date: date, days_before: int = 30) -> Optional[pd.DataFrame]:
    """Ottiene OHLC storico per un ticker fino a target_date."""
    try:
        start = (target_date - timedelta(days=days_before + 5)).strftime("%Y-%m-%d")
        end = (target_date + timedelta(days=5)).strftime("%Y-%m-%d")
        tk = yf.Ticker(ticker)
        df = tk.history(start=start, end=end)
        if df is None or df.empty or len(df) < 3:
            return None
        return df[["Open", "High", "Low", "Close", "Volume"]].copy()
    except Exception:
        return None


def _get_price_on_date(ohlc: pd.DataFrame, d: date) -> Optional[float]:
    """Restituisce il prezzo di chiusura alla data (o ultimo disponibile prima)."""
    if ohlc is None or ohlc.empty:
        return None
    ohlc = ohlc.copy()
    ohlc.index = pd.to_datetime(ohlc.index).date
    if d in ohlc.index:
        return float(ohlc.loc[d, "Close"])
    before = ohlc[ohlc.index <= d]
    if before.empty:
        return None
    return float(before["Close"].iloc[-1])


def _get_next_trading_day_price(ohlc: pd.DataFrame, d: date) -> Optional[float]:
    """Prezzo di chiusura il giorno successivo (o primo disponibile dopo)."""
    if ohlc is None or ohlc.empty:
        return None
    ohlc = ohlc.copy()
    ohlc.index = pd.to_datetime(ohlc.index).date
    after = ohlc[ohlc.index > d]
    if after.empty:
        return None
    return float(after["Close"].iloc[0])


# ============== CACHE ==============

def _cache_key(prefix: str, *args) -> str:
    return prefix + "_" + "_".join(str(a) for a in args)


def _load_earnings_cache(start_year: int, end_year: int) -> Optional[List[Dict]]:
    key = _cache_key("earnings", start_year, end_year)
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _save_earnings_cache(start_year: int, end_year: int, data: List[Dict]):
    key = _cache_key("earnings", start_year, end_year)
    path = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        with open(path, "w") as f:
            json.dump(data, f, default=str)
    except Exception:
        pass


# ============== SIMULATION LOOP ==============

def fetch_historical_earnings(
    tickers: List[str],
    start_year: int,
    end_year: int,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    use_cache: bool = True,
    sample_days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Scarica tutti gli earnings storici per il periodo e i ticker dati.
    Itera giorno per giorno usando Nasdaq API.
    sample_days: se impostato (es. 7), scarica solo ogni N giorni per test rapidi.
    """
    ticker_set = set(t.upper() for t in tickers)
    if use_cache:
        cached = _load_earnings_cache(start_year, end_year)
        if cached:
            filtered = [e for e in cached if e.get("symbol", "").upper() in ticker_set]
            if filtered:
                return filtered

    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    all_earnings = []
    current = start_date
    step = sample_days or 1
    total_days = (end_date - start_date).days + 1
    days_to_process = (total_days + step - 1) // step
    done = 0

    while current <= end_date:
        earnings = _get_earnings_from_nasdaq(current)
        for e in earnings:
            if e["symbol"] in ticker_set:
                e["_parsed_date"] = current.isoformat()
                all_earnings.append(e)
        if progress_callback and (done % 20 == 0 or current >= end_date - timedelta(days=step)):
            progress_callback(min(done, days_to_process), days_to_process, f"Earnings {current}")
        time.sleep(RATE_LIMIT_DELAY)
        current += timedelta(days=step)
        done += 1

    if use_cache and all_earnings:
        _save_earnings_cache(start_year, end_year, all_earnings)
    return all_earnings


def run_historical_simulation(
    earnings_events: List[Dict[str, Any]],
    capital_per_trade: float = 1000.0,
    bot_logic: Optional[Callable] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    min_confidence: int = 30,
) -> List[Dict[str, Any]]:
    """
    Esegue la simulazione storica su ogni evento di earnings.
    Per ogni evento: invoca bot_logic -> se BUY, calcola P&L vs giorno successivo.
    """
    bot_logic = bot_logic or bot_logic_placeholder
    results = []
    total = len(earnings_events)

    for i, evt in enumerate(earnings_events):
        ticker = evt.get("symbol", "")
        date_str = evt.get("_parsed_date") or evt.get("date", "")
        try:
            ed = datetime.fromisoformat(date_str.split("T")[0]).date()
        except Exception:
            continue

        if progress_callback and (i % 10 == 0 or i == total - 1):
            progress_callback(i, total, f"{ticker} {date_str}")

        ohlc = _get_ohlc_for_date(ticker, ed)
        pre_price = _get_price_on_date(ohlc, ed)
        next_price = _get_next_trading_day_price(ohlc, ed)

        if pre_price is None or pre_price <= 0:
            results.append({
                "ticker": ticker,
                "date": date_str,
                "decision": "SKIP",
                "reasoning": "Prezzo non disponibile",
                "pnl": 0,
                "win": False,
                "sector": evt.get("sector", "Unknown"),
                "year": ed.year,
            })
            time.sleep(RATE_LIMIT_DELAY)
            continue

        decision_data = bot_logic(ticker, ed, pre_price, ohlc, evt)
        decision = decision_data.get("decision", "WAIT")
        confidence = int(decision_data.get("confidence_score", 0))

        if decision != "BUY" or confidence < min_confidence:
            results.append({
                "ticker": ticker,
                "date": date_str,
                "decision": decision,
                "reasoning": decision_data.get("reasoning", ""),
                "pnl": 0,
                "win": False,
                "sector": evt.get("sector", "Unknown"),
                "year": ed.year,
            })
            time.sleep(RATE_LIMIT_DELAY)
            continue

        # Calcola P&L: compriamo a pre_price, vendiamo a next_price (after earnings)
        if next_price is None or next_price <= 0:
            results.append({
                "ticker": ticker,
                "date": date_str,
                "decision": "BUY",
                "reasoning": decision_data.get("reasoning", ""),
                "pnl": 0,
                "win": False,
                "sector": evt.get("sector", "Unknown"),
                "year": ed.year,
            })
        else:
            shares = capital_per_trade / pre_price
            pnl = (next_price - pre_price) * shares
            win = pnl > 0
            results.append({
                "ticker": ticker,
                "date": date_str,
                "decision": "BUY",
                "reasoning": decision_data.get("reasoning", ""),
                "entry_price": pre_price,
                "exit_price": next_price,
                "pnl": round(pnl, 2),
                "win": win,
                "sector": evt.get("sector", "Unknown"),
                "year": ed.year,
            })

        time.sleep(RATE_LIMIT_DELAY)

    return results


def aggregate_results(results: List[Dict], filter_year: Optional[int] = None, filter_sector: Optional[str] = None) -> Dict[str, Any]:
    """Aggrega i risultati per report."""
    df = pd.DataFrame(results)
    if df.empty:
        return {"total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_pnl": 0, "total_analyzed": len(results)}

    if filter_year:
        df = df[df["year"] == filter_year]
    if filter_sector and filter_sector != "Tutti":
        df = df[df["sector"] == filter_sector]

    traded = df[df["decision"] == "BUY"]
    if traded.empty:
        return {"total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_pnl": 0, "total_analyzed": len(df)}

    wins = traded["win"].sum()
    total_trades = len(traded)
    total_pnl = traded["pnl"].sum()
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    return {
        "total_trades": total_trades,
        "wins": int(wins),
        "losses": total_trades - int(wins),
        "win_rate": round(win_rate, 1),
        "total_pnl": round(total_pnl, 2),
        "total_analyzed": len(df),
    }
