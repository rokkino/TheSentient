"""
Market Data Service - Handles chart data and quotes
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from typing import List
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
try:
    from yahoo_fin import stock_info as si
    YAHOO_FIN_AVAILABLE = True
except ImportError:
    YAHOO_FIN_AVAILABLE = False

class MarketDataService:
    def __init__(self):
        self.timeframe_map = {
            "1d": {"period": "1d", "interval": "2m"},
            "5d": {"period": "5d", "interval": "15m"},
            "1m": {"period": "1mo", "interval": "1d"},
            "3m": {"period": "3mo", "interval": "1d"},
            "6m": {"period": "6mo", "interval": "1d"},
            "1y": {"period": "1y", "interval": "1d"},
            "5y": {"period": "5y", "interval": "1wk"},
        }
        
        # Ensure cache directory exists
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory", "graph")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def get_chart_data(self, ticker: str, timeframe: str, chart_type: str = "candle", include_earnings: bool = True) -> Dict[str, Any]:
        """Get chart data for a ticker"""
        loop = asyncio.get_event_loop()
        
        params = self.timeframe_map.get(timeframe, self.timeframe_map["1y"])
        
        def fetch_data():
            # Try to get from cache first if timeframe is 1y (default for watchlist sparklines)
            # or if it's a standard timeframe that we want to cache
            use_cache = True
            
            cached_data = None
            last_timestamp = None
            
            if use_cache:
                cached_data = self._get_cached_data(ticker, timeframe)
                if cached_data and cached_data.get("data"):
                    # Get last timestamp from cache
                    try:
                        last_item = cached_data["data"][-1]
                        last_timestamp = last_item["time"] / 1000 # Convert back to seconds
                        # print(f"Found cached data for {ticker}, last timestamp: {datetime.fromtimestamp(last_timestamp)}")
                    except:
                        pass

            tk = yf.Ticker(ticker)
            
            # If we have cached data, only fetch new data
            if last_timestamp:
                # Add a small buffer (1 day) to ensure overlap/continuity
                start_date = datetime.fromtimestamp(last_timestamp).strftime('%Y-%m-%d')
                # print(f"Fetching new data for {ticker} starting from {start_date}")
                
                # Adjust params to use start date instead of period
                fetch_params = params.copy()
                if "period" in fetch_params:
                    del fetch_params["period"]
                fetch_params["start"] = start_date
                
                try:
                    new_data = tk.history(**fetch_params)
                except Exception as e:
                    print(f"Error fetching incremental data: {e}, falling back to full fetch")
                    new_data = tk.history(**params)
                    cached_data = None # Invalidate cache on error
            else:
                data = tk.history(**params)
                new_data = data
            
            if new_data.empty and not cached_data:
                raise ValueError(f"No data available for {ticker}")
            
            # Process new data
            if not new_data.empty:
                # Clean timezone if needed
                if params.get("interval", "1d").endswith(("m", "h")):
                    try:
                        new_data.index = new_data.index.tz_convert(None)
                    except (TypeError, AttributeError):
                        pass
                
                # Convert to numeric
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in new_data.columns:
                        new_data[col] = pd.to_numeric(new_data[col], errors='coerce')
                
                new_data = new_data.dropna()

            # Merge with cache if available
            if cached_data and not new_data.empty:
                # Convert cached list back to DataFrame for processing/indicators
                # This is a bit expensive, but needed for indicators. 
                # Alternatively, we could just append new processed data to cached processed data.
                # Let's try the append approach for performance.
                
                # 1. Process new data into list format
                new_chart_data = self._process_data_to_list(new_data, params)
                
                # 2. Merge lists (avoiding duplicates based on time)
                existing_times = set(d["time"] for d in cached_data["data"])
                
                for item in new_chart_data:
                    if item["time"] not in existing_times:
                        cached_data["data"].append(item)
                        # Also update earnings if any
                
                # Sort by time
                cached_data["data"].sort(key=lambda x: x["time"])
                
                # Update metadata
                cached_data["metadata"]["count"] = len(cached_data["data"])
                cached_data["metadata"]["end"] = cached_data["data"][-1]["time"]
                
                # Save updated cache
                self._save_cached_data(ticker, timeframe, cached_data)
                
                return cached_data
                
            elif not new_data.empty:
                # Full fetch (no cache or cache invalid)
                # Calculate indicators and format
                
                # ... (rest of original processing logic) ...
                # We need to wrap the original logic to reuse it
                pass
            
            # If we are here, we need to process 'new_data' fully (either full fetch or fallback)
            data = new_data # Rename for compatibility with original code
            
            if data.empty:
                 raise ValueError(f"No valid data after cleaning for {ticker}")
            
            # Calculate RSI
            rsi_data = None
            try:
                rsi_data = self._calculate_rsi(data['Close'])
            except:
                pass
            
            # Calculate Moving Averages (13, 50, 200, 800)
            ma_data = {}
            ma_periods = [13, 50, 200, 800]
            for period in ma_periods:
                try:
                    ma_data[f'ma{period}'] = data['Close'].rolling(window=period, min_periods=1).mean()
                except:
                    pass
            
            # Calculate Bull Run signal (based on RSI and price momentum)
            bull_run_data = None
            if rsi_data is not None and len(data) > 1:
                try:
                    price_diff = data['Close'].diff()
                    rsi_diff = rsi_data.diff()
                    # Bull signal: price down but RSI up (divergence bullish)
                    bull_core = (price_diff < 0) & (rsi_diff > 0)
                    # Bear signal: price up but RSI down (divergence bearish)
                    bear_core = (price_diff > 0) & (rsi_diff < 0)
                    # Create signals
                    bull_run_data = pd.Series(0, index=data.index)
                    bull_run_data[bull_core] = 1  # Bull signal
                    bull_run_data[bear_core] = -1  # Bear signal
                except:
                    pass
            
            # Get earnings dates if requested
            earnings_dates = []
            if include_earnings:
                try:
                    earnings_dates = self._get_earnings_dates(tk, data.index[0], data.index[-1])
                    if earnings_dates:
                        print(f"Found {len(earnings_dates)} earnings dates for {ticker}")
                except Exception as e:
                    print(f"Error getting earnings dates for {ticker}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Helper function to clean float values
            def clean_float(val):
                if val is None:
                    return None
                try:
                    f_val = float(val)
                    if pd.isna(f_val) or np.isnan(f_val) or np.isinf(f_val):
                        return None
                    return f_val
                except (ValueError, TypeError):
                    return None

            # Format data for frontend
            chart_data = []
            for idx, row in data.iterrows():
                timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
                
                # RSI value
                rsi_value = None
                if rsi_data is not None and idx in rsi_data.index:
                    try:
                        val = rsi_data.loc[idx]
                        rsi_value = clean_float(val)
                    except:
                        pass
                
                # MA values
                ma_values = {}
                for period in ma_periods:
                    ma_key = f'ma{period}'
                    if ma_key in ma_data and idx in ma_data[ma_key].index:
                        try:
                            val = ma_data[ma_key].loc[idx]
                            cleaned_val = clean_float(val)
                            if cleaned_val is not None:
                                ma_values[f'ma{period}'] = cleaned_val
                        except:
                            pass
                
                # Bull run signal
                bull_run_value = None
                if bull_run_data is not None and idx in bull_run_data.index:
                    try:
                        val = bull_run_data.loc[idx]
                        if not pd.isna(val):
                            bull_run_value = int(val)
                    except:
                        pass
                
                chart_data.append({
                    "time": timestamp,
                    "open": clean_float(row['Open']),
                    "high": clean_float(row['High']),
                    "low": clean_float(row['Low']),
                    "close": clean_float(row['Close']),
                    "volume": clean_float(row['Volume']),
                    "rsi": rsi_value,
                    **ma_values,  # Spread MA values into the object
                    "bull_run": bull_run_value
                })
            
            result = {
                "ticker": ticker,
                "timeframe": timeframe,
                "chart_type": chart_type,
                "data": chart_data,
                "earnings_dates": earnings_dates,
                "metadata": {
                    "count": len(chart_data),
                    "start": chart_data[0]["time"] if chart_data else None,
                    "end": chart_data[-1]["time"] if chart_data else None
                }
            }
            
            # Save to cache
            self._save_cached_data(ticker, timeframe, result)
            
            return result
        
        return await loop.run_in_executor(None, fetch_data)

    def _get_cached_data(self, ticker: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get data from JSON cache (all timeframes cached for faster repeat loads)"""
        try:
            file_path = os.path.join(self.cache_dir, f"{ticker}_{timeframe}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error reading cache for {ticker}: {e}")
        return None

    def _save_cached_data(self, ticker: str, timeframe: str, data: Dict[str, Any]):
        """Save data to JSON cache (all timeframes for faster repeat loads)"""
        try:
            file_path = os.path.join(self.cache_dir, f"{ticker}_{timeframe}.json")
            with open(file_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving cache for {ticker}: {e}")

    def _process_data_to_list(self, data: pd.DataFrame, params: Dict) -> List[Dict[str, Any]]:
        """Helper to process DataFrame to list of dicts (reused logic)"""
        # Calculate RSI
        rsi_data = None
        try:
            rsi_data = self._calculate_rsi(data['Close'])
        except:
            pass
        
        # Calculate Moving Averages (13, 50, 200, 800)
        ma_data = {}
        ma_periods = [13, 50, 200, 800]
        for period in ma_periods:
            try:
                ma_data[f'ma{period}'] = data['Close'].rolling(window=period, min_periods=1).mean()
            except:
                pass
        
        # Calculate Bull Run signal
        bull_run_data = None
        if rsi_data is not None and len(data) > 1:
            try:
                price_diff = data['Close'].diff()
                rsi_diff = rsi_data.diff()
                bull_core = (price_diff < 0) & (rsi_diff > 0)
                bear_core = (price_diff > 0) & (rsi_diff < 0)
                bull_run_data = pd.Series(0, index=data.index)
                bull_run_data[bull_core] = 1
                bull_run_data[bear_core] = -1
            except:
                pass

        # Helper function to clean float values
        def clean_float(val):
            if val is None:
                return None
            try:
                f_val = float(val)
                if pd.isna(f_val) or np.isnan(f_val) or np.isinf(f_val):
                    return None
                return f_val
            except (ValueError, TypeError):
                return None

        chart_data = []
        for idx, row in data.iterrows():
            timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
            
            # RSI value
            rsi_value = None
            if rsi_data is not None and idx in rsi_data.index:
                try:
                    val = rsi_data.loc[idx]
                    rsi_value = clean_float(val)
                except:
                    pass
            
            # MA values
            ma_values = {}
            for period in ma_periods:
                ma_key = f'ma{period}'
                if ma_key in ma_data and idx in ma_data[ma_key].index:
                    try:
                        val = ma_data[ma_key].loc[idx]
                        cleaned_val = clean_float(val)
                        if cleaned_val is not None:
                            ma_values[f'ma{period}'] = cleaned_val
                    except:
                        pass
            
            # Bull run signal
            bull_run_value = None
            if bull_run_data is not None and idx in bull_run_data.index:
                try:
                    val = bull_run_data.loc[idx]
                    if not pd.isna(val):
                        bull_run_value = int(val)
                except:
                    pass
            
            chart_data.append({
                "time": timestamp,
                "open": clean_float(row['Open']),
                "high": clean_float(row['High']),
                "low": clean_float(row['Low']),
                "close": clean_float(row['Close']),
                "volume": clean_float(row['Volume']),
                "rsi": rsi_value,
                **ma_values,
                "bull_run": bull_run_value
            })
            
        return chart_data
    
    def _get_earnings_dates(self, ticker_obj, start_date, end_date) -> List[Dict[str, Any]]:
        """Get earnings dates for a ticker within the chart date range"""
        earnings_dates = []
        
        try:
            info = ticker_obj.info
            
            # Method 1: Try to get from calendar
            try:
                calendar = ticker_obj.calendar
                if calendar is not None and not calendar.empty:
                    for idx in calendar.index:
                        earnings_date = None
                        if isinstance(idx, pd.Timestamp):
                            earnings_date = idx
                        else:
                            try:
                                earnings_date = pd.to_datetime(idx)
                            except:
                                continue
                        
                        if earnings_date:
                            # Check if date is in range
                            if start_date and earnings_date < start_date:
                                continue
                            if end_date and earnings_date > end_date:
                                continue
                            
                            timestamp = int(earnings_date.timestamp() * 1000)
                            earnings_dates.append({
                                'date': earnings_date.date().isoformat(),
                                'timestamp': timestamp
                            })
            except:
                pass
            
            # Method 2: Try earningsHistory from info
            try:
                earnings_history = info.get('earningsHistory', [])
                if isinstance(earnings_history, list):
                    for earning in earnings_history:
                        if isinstance(earning, dict):
                            earnings_date_str = earning.get('date') or earning.get('reportDate')
                            if earnings_date_str:
                                try:
                                    if isinstance(earnings_date_str, (int, float)):
                                        earnings_date = datetime.fromtimestamp(earnings_date_str)
                                    else:
                                        earnings_date = pd.to_datetime(earnings_date_str)
                                    
                                    # Check if date is in range
                                    if start_date and earnings_date < start_date:
                                        continue
                                    if end_date and earnings_date > end_date:
                                        continue
                                    
                                    timestamp = int(earnings_date.timestamp() * 1000)
                                    earnings_dates.append({
                                        'date': earnings_date.date().isoformat(),
                                        'timestamp': timestamp
                                    })
                                except:
                                    continue
            except:
                pass
            
            # Method 3: Try earningsDate from info (next earnings)
            try:
                earnings_date_str = info.get('earningsDate')
                if earnings_date_str:
                    if isinstance(earnings_date_str, list) and len(earnings_date_str) > 0:
                        earnings_date_str = earnings_date_str[0]
                    
                    try:
                        if isinstance(earnings_date_str, (int, float)):
                            earnings_date = datetime.fromtimestamp(earnings_date_str)
                        else:
                            earnings_date = pd.to_datetime(earnings_date_str)
                        
                        # Check if date is in range
                        if (not start_date or earnings_date >= start_date) and (not end_date or earnings_date <= end_date):
                            timestamp = int(earnings_date.timestamp() * 1000)
                            earnings_dates.append({
                                'date': earnings_date.date().isoformat(),
                                'timestamp': timestamp
                            })
                    except:
                        pass
            except:
                pass
            
            # Remove duplicates and sort
            seen = set()
            unique_earnings = []
            for earning in earnings_dates:
                if earning['timestamp'] not in seen:
                    seen.add(earning['timestamp'])
                    unique_earnings.append(earning)
            
            unique_earnings.sort(key=lambda x: x['timestamp'])
            return unique_earnings
            
        except Exception as e:
            print(f"Error in _get_earnings_dates: {e}")
            return []
    
    async def get_quote(self, ticker: str, timeframe: str = "1d") -> Dict[str, Any]:
        """Get current quote for a ticker with change calculated based on timeframe"""
        loop = asyncio.get_event_loop()
        
        def fetch_quote():
            tk = yf.Ticker(ticker)
            info = tk.info
            
            # Get current price
            quote = tk.history(period="1d", interval="1m")
            current_price = None
            if not quote.empty:
                current_price = float(quote['Close'].iloc[-1])
            
            # Calculate change based on timeframe
            change = 0
            change_percent = 0
            
            if current_price is not None:
                # Get historical data for the timeframe
                params = self.timeframe_map.get(timeframe, self.timeframe_map["1y"])
                historical = tk.history(**params)
                
                if not historical.empty and len(historical) > 1:
                    # Get the first (oldest) close price in the timeframe
                    start_price = float(historical['Close'].iloc[0])
                    change = current_price - start_price
                    if start_price > 0:
                        change_percent = (change / start_price) * 100
                else:
                    # Fallback to regular market change if historical data not available
                    change = info.get("regularMarketChange", 0)
                    change_percent = info.get("regularMarketChangePercent", 0)
            
            # Helper function to clean float values
            def clean_float(val):
                if val is None:
                    return None
                try:
                    f_val = float(val)
                    if pd.isna(f_val) or np.isnan(f_val) or np.isinf(f_val):
                        return None
                    return f_val
                except (ValueError, TypeError):
                    return None

            return {
                "symbol": ticker,
                "name": info.get("longName", info.get("shortName", ticker)),
                "price": clean_float(current_price),
                "change": clean_float(change),
                "changePercent": clean_float(change_percent),
                "volume": clean_float(info.get("regularMarketVolume", 0)),
                "marketCap": clean_float(info.get("marketCap")),
                "currency": info.get("currency", "USD")
            }
        
        return await loop.run_in_executor(None, fetch_quote)

    async def get_financials(self, ticker: str) -> Dict[str, Any]:
        """Get financial data (Revenue, Earnings, EPS History)"""
        loop = asyncio.get_event_loop()
        
        def fetch_financials():
            tk = yf.Ticker(ticker)
            result = {
                "symbol": ticker,
                "quarterly_financials": [],
                "earnings_history": []
            }
            
            # 1. Get Quarterly Financials (Revenue & Earnings)
            try:
                # quarterly_financials dataframe
                # Rows: 'Total Revenue', 'Net Income', etc.
                # Columns: Dates
                qf = tk.quarterly_financials
                if not qf.empty:
                    # Transpose to get dates as rows
                    qf_T = qf.T
                    qf_T.index = pd.to_datetime(qf_T.index)
                    qf_T = qf_T.sort_index()
                    
                    financials_data = []
                    for date_idx, row in qf_T.iterrows():
                        try:
                            revenue = row.get('Total Revenue') or row.get('Operating Revenue')
                            earnings = row.get('Net Income') or row.get('Net Income Common Stockholders')
                            
                            if revenue is not None or earnings is not None:
                                financials_data.append({
                                    "date": date_idx.strftime('%Y-%m-%d'),
                                    "revenue": float(revenue) if revenue is not None and not pd.isna(revenue) else None,
                                    "earnings": float(earnings) if earnings is not None and not pd.isna(earnings) else None
                                })
                        except:
                            continue
                    
                    result["quarterly_financials"] = financials_data
            except Exception as e:
                print(f"Error fetching quarterly financials for {ticker}: {e}")

            # 2. Get EPS History (Estimates vs Actuals)
            # Try yahoo_fin first
            try:
                if YAHOO_FIN_AVAILABLE:
                    history = si.get_earnings_history(ticker)
                    if history:
                        eps_data = []
                        for entry in history:
                            try:
                                # entry keys: 'startdatetime', 'epsestimate', 'epsactual', 'epssurprisepct'
                                date_str = entry.get('startdatetime', '')
                                if date_str:
                                    # Format: 2024-10-31T10:00:00.000Z
                                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                    
                                    eps_data.append({
                                        "date": dt.strftime('%Y-%m-%d'),
                                        "estimate": entry.get('epsestimate'),
                                        "actual": entry.get('epsactual'),
                                        "surprise": entry.get('epssurprisepct')
                                    })
                            except:
                                continue
                        
                        # Sort by date
                        eps_data.sort(key=lambda x: x['date'])
                        result["earnings_history"] = eps_data
            except Exception as e:
                print(f"Error fetching earnings history for {ticker} with yahoo_fin: {e}")
                
            # Fallback for EPS History if yahoo_fin failed or empty
            if not result["earnings_history"]:
                try:
                    # Try getting it from yfinance calendar (sometimes has next earnings)
                    # or info['earningsHistory'] if available (rare in new yfinance)
                    info = tk.info
                    if 'earningsHistory' in info:
                        history = info['earningsHistory']
                        eps_data = []
                        for entry in history:
                            # Map fields if possible
                            pass
                except:
                    pass
                    
            return result

        return await loop.run_in_executor(None, fetch_financials)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Calculate MACD indicator"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return pd.DataFrame({'macd': macd, 'signal': signal_line, 'histogram': histogram})

    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3, slowing: int = 3) -> pd.DataFrame:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        if slowing > 1:
            k = k.rolling(window=slowing).mean()
            
        d = k.rolling(window=d_period).mean()
        
        return pd.DataFrame({'k': k, 'd': d})

    async def calculate_indicator(self, ticker: str, timeframe: str, indicator_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate technical indicators based on configuration list"""
        loop = asyncio.get_event_loop()
        
        # Ensure input is a list
        if isinstance(indicator_configs, dict):
            indicator_configs = [indicator_configs]
        
        def calculate():
            params = self.timeframe_map.get(timeframe, self.timeframe_map["1y"])
            tk = yf.Ticker(ticker)
            data = tk.history(**params)
            
            if data.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Clean data
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            data = data.dropna()
            
            results = []
            
            for config in indicator_configs:
                if not isinstance(config, dict):
                    print(f"Skipping invalid config item: {config} (type: {type(config)})")
                    continue
                    
                indicator_type = config.get("indicator", "").upper()
                ind_params = config.get("params", {})
                result_data = []
                
                try:
                    if indicator_type == "SMA":
                        period = int(ind_params.get("period", 20))
                        sma = data['Close'].rolling(window=period).mean()
                        
                        for idx, val in sma.items():
                            if not pd.isna(val):
                                timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
                                result_data.append({
                                    "time": timestamp,
                                    "value": float(val)
                                })
                                
                    elif indicator_type == "EMA":
                        period = int(ind_params.get("period", 20))
                        ema = data['Close'].ewm(span=period, adjust=False).mean()
                        
                        for idx, val in ema.items():
                            if not pd.isna(val):
                                timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
                                result_data.append({
                                    "time": timestamp,
                                    "value": float(val)
                                })
                                
                    elif indicator_type == "RSI":
                        period = int(ind_params.get("period", 14))
                        rsi = self._calculate_rsi(data['Close'], period)
                        
                        for idx, val in rsi.items():
                            if not pd.isna(val):
                                timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
                                result_data.append({
                                    "time": timestamp,
                                    "value": float(val)
                                })
                                
                    elif indicator_type == "BB":
                        period = int(ind_params.get("period", 20))
                        std_dev = float(ind_params.get("std_dev", 2))
                        
                        sma = data['Close'].rolling(window=period).mean()
                        std = data['Close'].rolling(window=period).std()
                        
                        upper = sma + (std * std_dev)
                        lower = sma - (std * std_dev)
                        
                        for idx in data.index:
                            if idx in upper.index and not pd.isna(upper[idx]):
                                timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
                                result_data.append({
                                    "time": timestamp,
                                    "upper": float(upper[idx]),
                                    "lower": float(lower[idx]),
                                    "basis": float(sma[idx])
                                })

                    elif indicator_type == "MACD":
                        fast = int(ind_params.get("fast_period", 12))
                        slow = int(ind_params.get("slow_period", 26))
                        signal = int(ind_params.get("signal_period", 9))
                        
                        macd_data = self._calculate_macd(data['Close'], fast, slow, signal)
                        
                        for idx in data.index:
                            if idx in macd_data.index and not pd.isna(macd_data.loc[idx, 'macd']):
                                timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
                                result_data.append({
                                    "time": timestamp,
                                    "macd": float(macd_data.loc[idx, 'macd']),
                                    "signal": float(macd_data.loc[idx, 'signal']),
                                    "histogram": float(macd_data.loc[idx, 'histogram'])
                                })

                    elif indicator_type == "VOL":
                        for idx in data.index:
                            timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
                            result_data.append({
                                "time": timestamp,
                                "value": float(data.loc[idx, 'Volume']),
                                "color": "#26a69a" if data.loc[idx, 'Close'] >= data.loc[idx, 'Open'] else "#ef5350"
                            })

                    elif indicator_type == "STOCH":
                        k_period = int(ind_params.get("k_period", 14))
                        d_period = int(ind_params.get("d_period", 3))
                        slowing = int(ind_params.get("slowing", 3))
                        
                        stoch_data = self._calculate_stochastic(data['High'], data['Low'], data['Close'], k_period, d_period, slowing)
                        
                        for idx in data.index:
                            if idx in stoch_data.index and not pd.isna(stoch_data.loc[idx, 'k']):
                                timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
                                result_data.append({
                                    "time": timestamp,
                                    "k": float(stoch_data.loc[idx, 'k']),
                                    "d": float(stoch_data.loc[idx, 'd'])
                                })
                    
                    results.append({
                        "indicator": indicator_type,
                        "data": result_data,
                        "config": config
                    })
                except Exception as e:
                    print(f"Error calculating {indicator_type}: {e}")
                    # Continue to next indicator even if one fails
                    continue

            return results

        return await loop.run_in_executor(None, calculate)

