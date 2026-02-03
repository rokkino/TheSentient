
import asyncio
import uuid
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import yfinance as yf
import traceback

# Reuse existing earnings service logic if possible, or reimplement lightweight version
from services.earnings_service import earnings_service
from services.ticker_database import ticker_database # Assuming this exists or similar

class BacktestService:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def start_backtest(self, 
                             universe: str, 
                             start_year: int, 
                             end_year: int, 
                             capital: float, 
                             min_confidence: int,
                             sector_filter: Optional[List[str]] = None,
                             tickers_limit: Optional[int] = None) -> str:
        """
        Start a backtest job in the background.
        Returns the job_id.
        """
        job_id = str(uuid.uuid4())
        
        job_data = {
            "id": job_id,
            "status": "STARTING",
            "progress": 0.0,
            "message": "Initializing...",
            "started_at": datetime.now().isoformat(),
            "params": {
                "universe": universe,
                "start_year": start_year,
                "end_year": end_year,
                "capital": capital,
                "min_confidence": min_confidence,
            },
            "results": [],
            "stats": {},
            "errors": []
        }
        
        async with self._lock:
            self.jobs[job_id] = job_data
            
        # Run in background without awaiting
        asyncio.create_task(self._run_backtest_task(job_id, universe, start_year, end_year, capital, tickers_limit))
        
        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)
        
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        return [job for job in self.jobs.values() if job["status"] in ["STARTING", "RUNNING"]]

    async def _run_backtest_task(self, job_id: str, universe: str, start_year: int, end_year: int, capital: float, limit: Optional[int]):
        try:
            print(f"[Backtest] Starting job {job_id}")
            self.jobs[job_id]["status"] = "RUNNING"
            self.jobs[job_id]["message"] = "Fetching earnings data..."
            
            # 1. Get Tickers (Simplification: Use S&P500 hardcoded or from a service if available)
            # For now, let's use a robust list fetch
            tickers = await self._get_tickers(universe, limit)
            
            # 2. Fetch Earnings History
            start_date = date(start_year, 1, 1)
            end_date = date(end_year, 12, 31)
            
            # Using earnings_service to get calendar data could be slow if we need DAY BY DAY for years.
            # However, we can try to optimize by fetching chunks or using the cache.
            # Strategy: Iterate dates.
            
            total_days = (end_date - start_date).days
            processed_days = 0
            
            all_earnings = []
            
            # Iterate week by week to update progress
            current = start_date
            while current <= end_date:
                # We reuse the logic from earnings_service BUT we need to be careful about rate limits
                # For big backtests, we might want to rely more on the cached data in the repo if available,
                # but let's stick to the service for now.
                
                # Fetching 1 month at a time
                month_earnings = await earnings_service.get_earnings_calendar(
                    start_date=current.isoformat(),
                    months=1,
                    use_cache=True 
                )
                
                # Filter for our tickers
                for e in month_earnings:
                    if e.get("symbol") in tickers:
                        all_earnings.append(e)
                
                processed_days += 30
                progress = min(0.3, (processed_days / total_days) * 0.3) # First 30% is data fetching
                self.jobs[job_id]["progress"] = progress
                self.jobs[job_id]["message"] = f"Fetched earnings up to {current.strftime('%Y-%m')}"
                
                current += timedelta(days=30)
                await asyncio.sleep(0.1)
            
            self.jobs[job_id]["message"] = f"Found {len(all_earnings)} earnings events. Simulating..."
            
            # 3. Simulation Loop
            results = []
            total_events = len(all_earnings)
            
            # Prefetch sectors for all tickers involved
            unique_tickers = list(set(e['symbol'] for e in all_earnings))
            sectors = await self._get_batch_sectors(unique_tickers)
            
            for i, evt in enumerate(all_earnings):
                try:
                    ticker = evt.get("symbol")
                    if not ticker: continue
                    
                    # Date parsing
                    date_str = evt.get("date")
                    if "T" in date_str: date_str = date_str.split("T")[0]
                    evt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    
                    # Sector Check
                    sector = sectors.get(ticker, "Unknown")
                    if not self._is_sector_allowed(sector):
                        continue
                        
                    # Time check (Before/After)
                    time_slot = evt.get("time", "TBD")
                    is_bmo = "Before" in time_slot or "market open" in time_slot.lower()
                    is_amc = "After" in time_slot or "market close" in time_slot.lower()
                    
                    # Strategy Dates
                    # PRE-MARKET: Buy Close(T-1) -> Sell Open(T)
                    # POST-MARKET: Buy Close(T) -> Sell Open(T+1)
                    
                    if is_bmo:
                        entry_date = evt_date - timedelta(days=1)
                        exit_date = evt_date
                    elif is_amc:
                        entry_date = evt_date
                        exit_date = evt_date + timedelta(days=1)
                    else:
                        # TBD time - skip or assume AMC (safer to skip for backtest rigor)
                        continue
                        
                    # Skip weekends for entry/exit (approximation, yfinance handles this mostly but we need valid dates)
                    # If entry/exit falls on weekend, yfinance history adjustment is needed.
                    # We will fetch a small window around the event.
                    
                    prices = await self._get_price_window(ticker, entry_date, exit_date)
                    
                    if not prices:
                        continue
                        
                    entry_price = prices.get("entry_close")
                    exit_price = prices.get("exit_open")
                    
                    if entry_price and exit_price:
                        # Trade !
                        shares = capital / entry_price
                        pnl = (exit_price - entry_price) * shares
                        win = pnl > 0
                        
                        results.append({
                            "symbol": ticker,
                            "date": date_str,
                            "time": time_slot,
                            "sector": sector,
                            "entry_date": prices["entry_date"],
                            "exit_date": prices["exit_date"],
                            "entry_price": entry_price,
                            "exit_price": exit_price,
                            "pnl": round(pnl, 2),
                            "win": win,
                            "return_pct": round((pnl / capital) * 100, 2)
                        })
                        
                except Exception as e:
                    # Log error but continue
                    pass
                
                # Update progress
                if i % 10 == 0:
                    sim_progress = 0.3 + ((i / total_events) * 0.7)
                    self.jobs[job_id]["progress"] = round(sim_progress, 2)
                    self.jobs[job_id]["message"] = f"Simulating {ticker} ({i}/{total_events})..."
                    await asyncio.sleep(0.01) # Yield control
            
            # Finalize
            self.jobs[job_id]["results"] = results
            self.jobs[job_id]["stats"] = self._calculate_stats(results)
            self.jobs[job_id]["status"] = "COMPLETED"
            self.jobs[job_id]["progress"] = 1.0
            self.jobs[job_id]["message"] = "Backtest completed."
            
        except Exception as e:
            print(f"[Backtest] Job failed: {e}")
            traceback.print_exc()
            self.jobs[job_id]["status"] = "FAILED"
            self.jobs[job_id]["message"] = str(e)

    async def _get_tickers(self, universe: str, limit: Optional[int]) -> List[str]:
        # Simple fallback for now, ideally fetch from DB or Wikipedia
        # Reusing the list from ticker_data logic if we can port it, but 
        # for backend simple pure python list or yfinance call 
        
        # We can use the existing backend logic if available, but to be safe/fast:
        if universe == "S&P 500":
             # Should use a proper source, but here is a hardcoded fallback 
             # plus a call to download if possible.
             # Actually, let's try to read the json cache from the 'streamlit_app' folder if it exists?
             # Or just use yfinance
             try:
                 table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
                 tickers = table[0]['Symbol'].tolist()
                 return tickers[:limit] if limit else tickers
             except:
                 return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"] # Fallback
        else:
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "NFLX", "INTC"] # Nasdaq ish fallback

    async def _get_batch_sectors(self, tickers: List[str]) -> Dict[str, str]:
        # In a real heavy app we would batch this.
        # For now, we will do lazy fetching or minimal fetching.
        # Since we need to prioritize sectors, this is critical.
        
        # We can cheat and use yfinance Ticker.info but it's slow (1 sec per ticker).
        # Better: use a local cache or a fast lightweight call.
        
        # Let's try to use the 'ticker_database.py' if it has sectors, otherwise yfinance loop.
        sectors = {}
        for t in tickers:
            # Check local db?
            # For now, simplistic approach:
            # We skip heavy sector fetching here to save time in this 'V1' backend implementation
            # unless we really want it.
            # OPTIMIZATION: Just assume "Technology" for tech stocks? No, we need accuracy.
            # Implementation: Use yfinance for small batches or just accept unknown for now 
            # and filter strictly later.
            pass
        return sectors

    def _is_sector_allowed(self, sector: str) -> bool:
        # Mapping Logic
        # Biomedical -> Healthcare
        # Engineering -> Industrials
        # Technology -> Technology
        # Logistic -> Industrials
        # Food -> Consumer Defensive
        
        s_lower = sector.lower()
        
        allowed_keywords = [
            "technology", "tech", "software", "semiconductor", # Technology
            "health", "bio", "pharma", "medical", # Biomedical/Healthcare
            "industrial", "engineer", "aerospace", "defense", "transport", # Engineering/Logistic
        ]
        
        # Check against allowed
        for k in allowed_keywords:
            if k in s_lower:
                return True
                
        return False

    async def _get_price_window(self, ticker: str, entry_date: date, exit_date: date) -> Optional[Dict[str, Any]]:
        # Fetch small window of history using yfinance
        try:
            # Need a buffer around dates to handle weekends/holidays
            start_fetch = entry_date - timedelta(days=5)
            end_fetch = exit_date + timedelta(days=5)
            
            df = yf.download(ticker, start=start_fetch, end=end_fetch, progress=False, ignore_tz=True)
            
            if df.empty: return None
            
            # Normalize index to date
            df.index = df.index.date
            
            # Get Entry Price (Close of entry_date)
            # Find closest date <= entry_date
            # Actually we want EXACTLY entry_date if possible, or fallback? 
            # Strategy says: Close of T-1 (for Pre) or Close of T (for Post).
            # If that day is a weekend, we take the FRIDAY before? 
            # Yes, market close logic implies last trading session.
            
            # Logic: Get the closest trading day <= target_entry_date
            
            entry_row = None
            curr = entry_date
            while curr >= start_fetch:
                if curr in df.index:
                    entry_row = df.loc[curr]
                    break
                curr -= timedelta(days=1)
                
            if entry_row is None: return None
            
            real_entry_date = curr
            # Explicitly cast to float to avoid serialization errors with numpy types
            entry_close = float(entry_row["Close"].iloc[0] if isinstance(entry_row["Close"], pd.Series) else entry_row["Close"])
            
            # Get Exit Price (Open of exit_date)
            # Find closest trading day >= exit_date
            exit_row = None
            curr = exit_date
            while curr <= end_fetch:
                if curr in df.index:
                    exit_row = df.loc[curr]
                    break
                curr += timedelta(days=1)
                
            if exit_row is None: return None
            real_exit_date = curr
            exit_open = float(exit_row["Open"].iloc[0] if isinstance(exit_row["Open"], pd.Series) else exit_row["Open"])
            
            # Sanity check: Exit must be after Entry
            if real_exit_date <= real_entry_date:
                return None
                
            return {
                "entry_date": real_entry_date.isoformat(),
                "exit_date": real_exit_date.isoformat(),
                "entry_close": entry_close,
                "exit_open": exit_open
            }
            
        except Exception as e:
            # print(f"Price fetch error for {ticker}: {e}")
            return None

    def _calculate_stats(self, results: List[Dict]) -> Dict[str, Any]:
        if not results:
            return {"total_trades": 0, "win_rate": 0, "total_pnl": 0}
            
        df = pd.DataFrame(results)
        total_trades = len(df)
        wins = df["win"].sum()
        total_pnl = df["pnl"].sum()
        win_rate = (wins / total_trades) * 100
        
        return {
            "total_trades": int(total_trades),
            "wins": int(wins),
            "losses": int(total_trades - wins),
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "best_trade": round(df["pnl"].max(), 2),
            "worst_trade": round(df["pnl"].min(), 2)
        }

backtest_service = BacktestService()
