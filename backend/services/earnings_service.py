"""
Earnings Service - Handles earnings calendar data
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

class EarningsService:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
    
    async def get_earnings_calendar(self, start_date: Optional[str] = None, weeks: int = 1, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get earnings calendar for the next N weeks starting from start_date (or today)
        Returns paginated results (1 week per page)
        """
        loop = asyncio.get_event_loop()
        
        if start_date is None:
            start_date = datetime.now().date()
        else:
            start_date = datetime.fromisoformat(start_date).date()
        
        # Calculate date range for this page (1 week)
        # Use a wider range to catch more earnings (include past week and future weeks)
        # For offset 0, include past week to catch recent earnings
        page_start = start_date + timedelta(weeks=offset) - timedelta(days=7)  # Include past week
        page_end = page_start + timedelta(weeks=weeks) + timedelta(days=14)  # Include 2 weeks ahead
        
        def fetch_earnings():
            earnings_list = []
            
            # Method 1: Use yfinance for popular tickers (primary method)
            # Limit to avoid timeout - only check most popular tickers
            try:
                earnings_list.extend(self._get_popular_tickers_earnings(page_start, page_end))
                print(f"Found {len(earnings_list)} earnings from popular tickers")
            except Exception as e:
                print(f"Error getting earnings from yfinance: {e}")
            
            # If we have results, return early to avoid timeout
            if earnings_list:
                return earnings_list
            
            # Method 2: Try earningswhispers.com scraping (fallback) - skip if we have results
            try:
                scraped = self._scrape_earningswhispers(page_start, page_end)
                if scraped:
                    earnings_list.extend(scraped)
                    print(f"Found {len(scraped)} earnings from scraping")
            except Exception as e:
                print(f"Error scraping earningswhispers: {e}")
            
            # Filter to only include earnings in the requested range
            # Use a wider range to catch earnings near the target week
            filtered_earnings = []
            actual_start = start_date + timedelta(weeks=offset) - timedelta(days=7)  # Include past week
            actual_end = actual_start + timedelta(weeks=weeks) + timedelta(days=7)  # Include next week
            
            for earning in earnings_list:
                try:
                    earning_date = datetime.fromisoformat(earning['date']).date()
                    if actual_start <= earning_date <= actual_end:
                        filtered_earnings.append(earning)
                except Exception as e:
                    # Skip earnings with invalid dates
                    continue
            
            # Remove duplicates based on symbol and date
            seen = set()
            unique_earnings = []
            for earning in filtered_earnings:
                key = (earning.get('symbol'), earning.get('date'))
                if key not in seen:
                    seen.add(key)
                    unique_earnings.append(earning)
            
            # Sort by date
            unique_earnings.sort(key=lambda x: x.get('date', ''))
            
            print(f"Returning {len(unique_earnings)} filtered earnings for range {actual_start} to {actual_end}")
            return unique_earnings
        
        return await loop.run_in_executor(None, fetch_earnings)
    
    def _scrape_earningswhispers(self, start_date, end_date) -> List[Dict[str, Any]]:
        """Scrape earnings calendar from earningswhispers.com"""
        earnings = []
        
        try:
            # EarningsWhispers calendar URL
            url = "https://www.earningswhispers.com/calendar"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse earnings table (structure may vary)
                # This is a simplified parser - may need adjustment based on actual HTML structure
                table = soup.find('table', class_='calendar') or soup.find('table')
                
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 3:
                            try:
                                date_str = cells[0].get_text(strip=True)
                                symbol = cells[1].get_text(strip=True)
                                company = cells[2].get_text(strip=True)
                                
                                # Parse date
                                try:
                                    earnings_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                                except:
                                    earnings_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                                
                                # Check if date is in range
                                if start_date <= earnings_date <= end_date:
                                    earnings.append({
                                        'symbol': symbol,
                                        'company': company,
                                        'date': earnings_date.isoformat(),
                                        'time': cells[3].get_text(strip=True) if len(cells) > 3 else 'TBD',
                                        'source': 'earningswhispers'
                                    })
                            except Exception as e:
                                continue
        except Exception as e:
            print(f"Error in earningswhispers scrape: {e}")
        
        return earnings
    
    def _get_popular_tickers_earnings(self, start_date, end_date) -> List[Dict[str, Any]]:
        """Get earnings for popular tickers using yfinance"""
        earnings = []
        
        # Expanded list of popular tickers
        popular_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
            'AMD', 'INTC', 'JPM', 'BAC', 'WMT', 'DIS', 'V', 'MA',
            'CRM', 'ORCL', 'ADBE', 'CSCO', 'IBM', 'QCOM', 'AVGO',
            'COST', 'HD', 'MCD', 'NKE', 'TGT', 'GS', 'JNJ', 'PG',
            'KO', 'PEP', 'WFC', 'C', 'AXP', 'UNH', 'JNJ', 'VZ', 'T'
        ]
        
        print(f"Searching earnings for {len(popular_tickers)} tickers from {start_date} to {end_date}")
        
        for ticker in popular_tickers:
            try:
                tk = yf.Ticker(ticker)
                # Use timeout for info fetch - skip if it takes too long
                try:
                    info = tk.info
                    # Skip if info is empty or None
                    if not info:
                        continue
                except Exception as e:
                    # Skip this ticker if there's an error
                    continue
                
                # Method 1: Check earningsDate from info
                earnings_date_str = info.get('earningsDate')
                if earnings_date_str:
                    if isinstance(earnings_date_str, list) and len(earnings_date_str) > 0:
                        earnings_date_str = earnings_date_str[0]
                    
                    try:
                        # Convert timestamp to date
                        if isinstance(earnings_date_str, (int, float)):
                            earnings_date = datetime.fromtimestamp(earnings_date_str).date()
                        else:
                            # Try parsing as string
                            earnings_date = pd.to_datetime(str(earnings_date_str)).date()
                        
                        # Check if date is in range (include past earnings too)
                        if start_date <= earnings_date <= end_date:
                            earnings.append({
                                'symbol': ticker,
                                'company': info.get('longName', info.get('shortName', ticker)),
                                'date': earnings_date.isoformat(),
                                'time': 'TBD',
                                'source': 'yfinance'
                            })
                            print(f"Found earnings for {ticker} on {earnings_date}")
                    except Exception as e:
                        pass
                
                # Method 2: Try to get from calendar (more reliable)
                try:
                    calendar = tk.calendar
                    if calendar is not None and not calendar.empty:
                        for idx in calendar.index:
                            try:
                                if isinstance(idx, pd.Timestamp):
                                    cal_date = idx.date()
                                else:
                                    cal_date = pd.to_datetime(idx).date()
                                
                                # Check if date is in range
                                if start_date <= cal_date <= end_date:
                                    # Check if we already added this ticker for this date
                                    existing = [e for e in earnings if e['symbol'] == ticker and e['date'] == cal_date.isoformat()]
                                    if not existing:
                                        earnings.append({
                                            'symbol': ticker,
                                            'company': info.get('longName', info.get('shortName', ticker)),
                                            'date': cal_date.isoformat(),
                                            'time': 'TBD',
                                            'source': 'yfinance'
                                        })
                                        print(f"Found earnings for {ticker} on {cal_date} from calendar")
                            except Exception as e:
                                continue
                except Exception as e:
                    pass
                    
            except Exception as e:
                continue
        
        print(f"Total earnings found: {len(earnings)}")
        return earnings
    
    def _get_sp500_earnings(self, start_date, end_date) -> List[Dict[str, Any]]:
        """Get earnings for a sample of S&P 500 tickers"""
        earnings = []
        
        # Sample of S&P 500 tickers
        sp500_sample = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'BRK.B',
            'UNH', 'JNJ', 'V', 'PG', 'JPM', 'MA', 'HD', 'DIS', 'BAC', 'ABBV',
            'AVGO', 'PFE', 'KO', 'PEP', 'TMO', 'COST', 'WMT', 'MRK', 'ABT',
            'ACN', 'NFLX', 'ADBE', 'CRM', 'NKE', 'T', 'LIN', 'DHR', 'VZ'
        ]
        
        for ticker in sp500_sample:
            try:
                tk = yf.Ticker(ticker)
                info = tk.info
                
                if not info:
                    continue
                
                earnings_date_str = info.get('earningsDate')
                if earnings_date_str:
                    if isinstance(earnings_date_str, list) and len(earnings_date_str) > 0:
                        earnings_date_str = earnings_date_str[0]
                    
                    try:
                        if isinstance(earnings_date_str, (int, float)):
                            earnings_date = datetime.fromtimestamp(earnings_date_str).date()
                        else:
                            earnings_date = pd.to_datetime(str(earnings_date_str)).date()
                        
                        if start_date <= earnings_date <= end_date:
                            earnings.append({
                                'symbol': ticker,
                                'company': info.get('longName', info.get('shortName', ticker)),
                                'date': earnings_date.isoformat(),
                                'time': 'TBD',
                                'source': 'yfinance'
                            })
                    except:
                        continue
            except:
                continue
        
        return earnings
    
    async def get_ticker_earnings(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get earnings information for a specific ticker"""
        loop = asyncio.get_event_loop()
        
        def fetch_ticker_earnings():
            try:
                tk = yf.Ticker(ticker)
                info = tk.info
                
                earnings_date_str = info.get('earningsDate')
                earnings_date = None
                
                if earnings_date_str:
                    if isinstance(earnings_date_str, list) and len(earnings_date_str) > 0:
                        earnings_date_str = earnings_date_str[0]
                    
                    try:
                        if isinstance(earnings_date_str, (int, float)):
                            earnings_date = datetime.fromtimestamp(earnings_date_str).date()
                        else:
                            earnings_date = datetime.fromisoformat(str(earnings_date_str)).date()
                    except:
                        pass
                
                return {
                    'symbol': ticker,
                    'company': info.get('longName', info.get('shortName', ticker)),
                    'date': earnings_date.isoformat() if earnings_date else None,
                    'time': 'TBD',
                    'source': 'yfinance'
                }
            except Exception as e:
                return None
        
        return await loop.run_in_executor(None, fetch_ticker_earnings)
    
    async def get_ticker_historical_earnings(self, ticker: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get historical earnings dates for a ticker within a date range
        This is used to show earnings lines on charts
        """
        loop = asyncio.get_event_loop()
        
        def fetch_historical_earnings():
            earnings_dates = []
            
            try:
                tk = yf.Ticker(ticker)
                info = tk.info
                
                # Get calendar events which include earnings dates
                try:
                    calendar = tk.calendar
                    if calendar is not None and not calendar.empty:
                        # Calendar contains earnings dates
                        for idx, row in calendar.iterrows():
                            earnings_date = None
                            if isinstance(idx, pd.Timestamp):
                                earnings_date = idx.date()
                            elif isinstance(idx, datetime):
                                earnings_date = idx.date()
                            else:
                                try:
                                    earnings_date = pd.to_datetime(idx).date()
                                except:
                                    continue
                            
                            if earnings_date:
                                # Check if date is in range
                                if start_date and earnings_date < start_date.date():
                                    continue
                                if end_date and earnings_date > end_date.date():
                                    continue
                                
                                earnings_dates.append({
                                    'date': earnings_date.isoformat(),
                                    'timestamp': int(datetime.combine(earnings_date, datetime.min.time()).timestamp() * 1000)
                                })
                except Exception as e:
                    # Fallback: try to get from info
                    pass
                
                # Alternative method: try to get from earnings history
                # Some tickers have earningsHistory in info
                try:
                    earnings_history = info.get('earningsHistory', [])
                    if isinstance(earnings_history, list):
                        for earning in earnings_history:
                            if isinstance(earning, dict):
                                earnings_date_str = earning.get('date')
                                if earnings_date_str:
                                    try:
                                        if isinstance(earnings_date_str, (int, float)):
                                            earnings_date = datetime.fromtimestamp(earnings_date_str).date()
                                        else:
                                            earnings_date = datetime.fromisoformat(str(earnings_date_str)).date()
                                        
                                        # Check if date is in range
                                        if start_date and earnings_date < start_date.date():
                                            continue
                                        if end_date and earnings_date > end_date.date():
                                            continue
                                        
                                        earnings_dates.append({
                                            'date': earnings_date.isoformat(),
                                            'timestamp': int(datetime.combine(earnings_date, datetime.min.time()).timestamp() * 1000)
                                        })
                                    except:
                                        continue
                except:
                    pass
                
                # Remove duplicates and sort
                seen = set()
                unique_earnings = []
                for earning in earnings_dates:
                    if earning['date'] not in seen:
                        seen.add(earning['date'])
                        unique_earnings.append(earning)
                
                unique_earnings.sort(key=lambda x: x['timestamp'])
                return unique_earnings
                
            except Exception as e:
                print(f"Error fetching historical earnings for {ticker}: {e}")
                return []
        
        return await loop.run_in_executor(None, fetch_historical_earnings)

