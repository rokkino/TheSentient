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
    
    async def get_chart_data(self, ticker: str, timeframe: str, chart_type: str = "candle", include_earnings: bool = True) -> Dict[str, Any]:
        """Get chart data for a ticker"""
        loop = asyncio.get_event_loop()
        
        params = self.timeframe_map.get(timeframe, self.timeframe_map["1y"])
        
        def fetch_data():
            tk = yf.Ticker(ticker)
            data = tk.history(**params)
            
            if data.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Clean timezone if needed
            if params.get("interval", "1d").endswith(("m", "h")):
                try:
                    data.index = data.index.tz_convert(None)
                except (TypeError, AttributeError):
                    pass
            
            # Convert to numeric
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            data = data.dropna()
            
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
            
            # Format data for frontend
            chart_data = []
            for idx, row in data.iterrows():
                timestamp = int(idx.timestamp() * 1000) if isinstance(idx, pd.Timestamp) else int(idx)
                
                # RSI value
                rsi_value = None
                if rsi_data is not None and idx in rsi_data.index:
                    try:
                        rsi_value = float(rsi_data.loc[idx]) if not pd.isna(rsi_data.loc[idx]) else None
                    except:
                        pass
                
                # MA values
                ma_values = {}
                for period in ma_periods:
                    ma_key = f'ma{period}'
                    if ma_key in ma_data and idx in ma_data[ma_key].index:
                        try:
                            ma_val = ma_data[ma_key].loc[idx]
                            if not pd.isna(ma_val):
                                ma_values[f'ma{period}'] = float(ma_val)
                        except:
                            pass
                
                # Bull run signal
                bull_run_value = None
                if bull_run_data is not None and idx in bull_run_data.index:
                    try:
                        bull_run_value = int(bull_run_data.loc[idx]) if not pd.isna(bull_run_data.loc[idx]) else None
                    except:
                        pass
                
                chart_data.append({
                    "time": timestamp,
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": float(row['Volume']),
                    "rsi": rsi_value,
                    **ma_values,  # Spread MA values into the object
                    "bull_run": bull_run_value
                })
            
            return {
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
        
        return await loop.run_in_executor(None, fetch_data)
    
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
            
            return {
                "symbol": ticker,
                "name": info.get("longName", info.get("shortName", ticker)),
                "price": current_price,
                "change": change,
                "changePercent": change_percent,
                "volume": info.get("regularMarketVolume", 0),
                "marketCap": info.get("marketCap"),
                "currency": info.get("currency", "USD")
            }
        
        return await loop.run_in_executor(None, fetch_quote)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

