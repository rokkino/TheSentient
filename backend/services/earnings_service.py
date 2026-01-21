"""
Earnings Service - Handles earnings calendar data
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta, date
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
try:
    from yahoo_earnings_calendar import YahooEarningsCalendar
    YAHOO_EARNINGS_AVAILABLE = True
except ImportError:
    YAHOO_EARNINGS_AVAILABLE = False
    print("Warning: yahoo-earnings-calendar not installed. Install it with: pip install yahoo-earnings-calendar")
    
    # Try to install it programmatically if not available
    try:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yahoo-earnings-calendar"])
        from yahoo_earnings_calendar import YahooEarningsCalendar
        YAHOO_EARNINGS_AVAILABLE = True
        print("Successfully installed yahoo-earnings-calendar")
    except:
        pass

def get_next_business_day(target_date: date) -> date:
    """
    Get the next business day (skip weekends)
    If target_date is Saturday (5) or Sunday (6), return next Monday
    """
    weekday = target_date.weekday()  # 0=Monday, 6=Sunday
    if weekday == 5:  # Saturday
        return target_date + timedelta(days=2)  # Skip to Monday
    elif weekday == 6:  # Sunday
        return target_date + timedelta(days=1)  # Skip to Monday
    else:
        return target_date

def get_next_business_days(target_date: date, count: int = 2) -> tuple[date, date]:
    """
    Get the next business days (skip weekends)
    Returns (today_business_day, tomorrow_business_day)
    """
    # Get today's business day (skip weekend if needed)
    today_bd = get_next_business_day(target_date)
    
    # Get tomorrow's business day (next business day after today_bd)
    tomorrow_candidate = today_bd + timedelta(days=1)
    tomorrow_bd = get_next_business_day(tomorrow_candidate)
    
    return (today_bd, tomorrow_bd)

class EarningsService:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache = {}
        self.cache_ttl = 86400  # 24 hours cache (in seconds) - refresh every 24h
        self.calendar_cache_ttl = 86400  # 24 hours for calendar cache (6 months data)
        
        # Use memory directory in backend root
        if cache_dir is None:
            # Try to find the backend directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(current_dir)
            cache_dir = os.path.join(backend_dir, 'memory', 'earnings')
        
        self.cache_dir = cache_dir
        # self.cache_file is no longer used for monolithic cache
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir, exist_ok=True)
                print(f"[EARNINGS] Created memory directory: {cache_dir}")
            except Exception as e:
                print(f"[EARNINGS] Warning: Could not create memory directory {cache_dir}: {e}")
        
        # Load existing cache
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from individual JSON files in memory directory"""
        try:
            if not os.path.exists(self.cache_dir):
                return

            count = 0
            # Iterate over all files in the cache directory
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            cache_entry = json.load(f)
                            
                            # Extract key from filename (remove .json)
                            key = filename[:-5]
                            
                            # Verify cache is not expired
                            cache_time = cache_entry.get('timestamp', 0)
                            current_time = time.time()
                            
                            # Check TTL based on key type
                            ttl = self.calendar_cache_ttl if 'calendar' in key else self.cache_ttl
                            
                            if current_time - cache_time < ttl:
                                self.cache[key] = cache_entry
                                count += 1
                            else:
                                # Optional: Delete expired files to keep directory clean
                                # os.remove(file_path)
                                pass
                    except Exception as e:
                        print(f"[EARNINGS] Error loading cache file {filename}: {e}")
            
            print(f"[EARNINGS] Loaded {count} valid cache entries from {self.cache_dir}")
        except Exception as e:
            print(f"[EARNINGS] Error loading cache: {e}")
            self.cache = {}
    
    def _save_entry(self, key: str, data: Dict[str, Any]):
        """Save a single cache entry to a JSON file"""
        try:
            # Sanitize key for filename
            safe_key = "".join([c for c in key if c.isalpha() or c.isdigit() or c in ('-', '_')]).strip()
            if not safe_key:
                safe_key = "unknown_entry"
                
            file_path = os.path.join(self.cache_dir, f"{safe_key}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"[EARNINGS] Error saving cache entry {key}: {e}")
    
    def _get_cache_key(self, target_date: date) -> str:
        """Genera una chiave per il cache basata sulla data"""
        return f"earnings_{target_date.isoformat()}"
    
    def _get_from_cache(self, target_date: date) -> Optional[List[Dict[str, Any]]]:
        """Recupera earnings dal cache se disponibili e non scaduti"""
        cache_key = self._get_cache_key(target_date)
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            cache_time = cache_entry.get('timestamp', 0)
            current_time = time.time()
            
            if current_time - cache_time < self.cache_ttl:
                print(f"[EARNINGS] ✅ Cache hit for {target_date.isoformat()} (age: {int((current_time - cache_time) / 3600)}h)")
                return cache_entry.get('data', [])
            else:
                # Cache scaduto, rimuovilo
                del self.cache[cache_key]
                print(f"[EARNINGS] ⏰ Cache expired for {target_date.isoformat()}")
        
        return None
    
    def _save_to_cache(self, target_date: date, earnings: List[Dict[str, Any]]):
        """Salva earnings nel cache"""
        cache_key = self._get_cache_key(target_date)
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'data': earnings,
            'date': target_date.isoformat()
        }
        self._save_entry(cache_key, self.cache[cache_key])
        print(f"[EARNINGS] 💾 Saved to cache: {target_date.isoformat()} ({len(earnings)} earnings)")
    
    def _get_nasdaq_earnings_api(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Get earnings from Nasdaq API (metodo principale, veloce e affidabile)
        """
        date_str = target_date.strftime("%Y-%m-%d")
        url = "https://api.nasdaq.com/api/calendar/earnings"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.nasdaq.com/'
        }
        
        params = {'date': date_str}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'rows' in data['data']:
                    rows = data['data']['rows']
                    earnings_list = []
                    
                    for row in rows:
                        try:
                            if isinstance(row, dict):
                                symbol = str(row.get('symbol', '')).strip().upper()
                                # Validate symbol - must be alphanumeric with dots, dashes, but no special chars
                                if not symbol or len(symbol) > 10 or not re.match(r'^[A-Z0-9\.\-]+$', symbol):
                                    print(f"[EARNINGS] Invalid symbol skipped: {symbol}")
                                    continue
                                
                                company = str(row.get('name', row.get('companyName', symbol))).strip()
                                # Clean company name - remove any weird characters
                                if not company or company == symbol:
                                    company = symbol
                                # Remove any = signs or other malformed data
                                if '=' in company or len(company) > 100:
                                    company = symbol
                                
                                time_str = str(row.get('time', 'time-not-supplied'))
                                
                                # Informazioni aggiuntive
                                eps_forecast = row.get('epsForecast', row.get('epsEstimate'))
                                last_year_eps = row.get('lastYearEPS', row.get('lastYearEps'))
                                market_cap = row.get('marketCap')
                                fiscal_quarter = row.get('fiscalQuarterEnding')
                                num_estimates = row.get('noOfEsts')
                                last_year_date = row.get('lastYearRptDt')
                                
                                time_info = 'TBD'
                                time_lower = time_str.lower()
                                if 'before' in time_lower or 'bmo' in time_lower or 'pre' in time_lower:
                                    time_info = 'Before Market Open'
                                elif 'after' in time_lower or 'amc' in time_lower or 'post' in time_lower:
                                    time_info = 'After Market Close'
                                elif 'time-not-supplied' in time_lower:
                                    time_info = 'TBD'
                                
                                earnings_list.append({
                                    'symbol': symbol,
                                    'ticker': symbol,  # Per compatibilità
                                    'company': company,
                                    'companymearningsshortname': company,
                                    'date': target_date.isoformat(),
                                    'time': time_info,
                                    'source': 'nasdaq_api',
                                    'epsestimate': eps_forecast if eps_forecast not in [None, 'N/A', ''] else 'N/A',
                                    'epsactual': last_year_eps if last_year_eps not in [None, 'N/A', ''] else 'N/A',
                                    'marketCap': market_cap if market_cap not in [None, 'N/A', ''] else 'N/A',
                                    'fiscalQuarter': fiscal_quarter if fiscal_quarter not in [None, 'N/A', ''] else 'N/A',
                                    'numEstimates': num_estimates if num_estimates not in [None, 'N/A', ''] else 'N/A',
                                    'lastYearDate': last_year_date if last_year_date not in [None, 'N/A', ''] else 'N/A'
                                })
                        except Exception as e:
                            continue
                    
                    return earnings_list
        except Exception as e:
            print(f"[EARNINGS] Nasdaq API error: {e}")
        
        return []
    
    def _get_nasdaq_earnings(self, target_date: date, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get earnings from Nasdaq API with caching (12 hours)
        """
        # Controlla cache prima
        if use_cache:
            cached_earnings = self._get_from_cache(target_date)
            if cached_earnings is not None:
                return cached_earnings
        
        # Recupera da API Nasdaq
        earnings_list = self._get_nasdaq_earnings_api(target_date)
        
        # Salva in cache se abbiamo risultati
        if earnings_list and use_cache:
            self._save_to_cache(target_date, earnings_list)
        
        return earnings_list
        """
        Get earnings from Nasdaq - multiple methods
        """
        earnings_list = []
        
        # Method 1: Try Nasdaq API
        try:
            url = "https://api.nasdaq.com/api/calendar/earnings"
            date_str = target_date.strftime("%Y-%m-%d")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.nasdaq.com/'
            }
            
            params = {'date': date_str}
            
            print(f"[EARNINGS] Fetching Nasdaq API for {date_str}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'data' in data and 'rows' in data['data']:
                        rows = data['data']['rows']
                        print(f"[EARNINGS] Nasdaq API returned {len(rows)} earnings")
                        
                        for row in rows:
                            try:
                                symbol = str(row.get('symbol', '')).strip().upper()
                                if not symbol or len(symbol) > 10:
                                    continue
                                
                                company = row.get('companyName', symbol)
                                time_str = str(row.get('time', 'TBD'))
                                
                                time_info = 'TBD'
                                time_lower = time_str.lower()
                                if 'before' in time_lower or 'bmo' in time_lower or 'pre' in time_lower:
                                    time_info = 'Before Market Open'
                                elif 'after' in time_lower or 'amc' in time_lower or 'post' in time_lower:
                                    time_info = 'After Market Close'
                                
                                earnings_list.append({
                                    'symbol': symbol,
                                    'company': company,
                                    'date': target_date.isoformat(),
                                    'time': time_info,
                                    'source': 'nasdaq_api'
                                })
                            except:
                                continue
                except:
                    pass
        except Exception as e:
            print(f"[EARNINGS] Nasdaq API error: {e}")
        
        # Method 2: Scrape Nasdaq page directly
        if not earnings_list:
            try:
                print("[EARNINGS] Scraping Nasdaq earnings page...")
                url = f"https://www.nasdaq.com/earnings-calendar?date={target_date.strftime('%Y-%m-%d')}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for earnings data in various formats
                    # Try to find table or JSON data
                    scripts = soup.find_all('script', type='application/json')
                    for script in scripts:
                        try:
                            data = json.loads(script.string)
                            if 'earnings' in str(data).lower():
                                # Parse JSON data if found
                                pass
                        except:
                            continue
                    
                    # Look for tables
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')[1:]
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                try:
                                    symbol = cells[0].get_text(strip=True).upper()
                                    if symbol and len(symbol) <= 10:
                                        company = cells[1].get_text(strip=True) if len(cells) > 1 else symbol
                                        time_info = 'TBD'
                                        if len(cells) > 2:
                                            time_str = cells[2].get_text(strip=True).lower()
                                            if 'before' in time_str or 'pre' in time_str:
                                                time_info = 'Before Market Open'
                                            elif 'after' in time_str or 'post' in time_str:
                                                time_info = 'After Market Close'
                                        
                                        earnings_list.append({
                                            'symbol': symbol,
                                            'company': company,
                                            'date': target_date.isoformat(),
                                            'time': time_info,
                                            'source': 'nasdaq_scrape'
                                        })
                                except:
                                    continue
            except Exception as e:
                print(f"[EARNINGS] Nasdaq scraping error: {e}")
        
        # Method 3: Try Finviz (very reliable)
        if not earnings_list:
            finviz_earnings = self._get_finviz_earnings(target_date)
            if finviz_earnings:
                earnings_list.extend(finviz_earnings)
                print(f"[EARNINGS] Finviz returned {len(finviz_earnings)} earnings")
        
        # Method 4: Try MarketWatch
        if not earnings_list:
            mw_earnings = self._get_marketwatch_earnings(target_date)
            if mw_earnings:
                earnings_list.extend(mw_earnings)
                print(f"[EARNINGS] MarketWatch returned {len(mw_earnings)} earnings")
        
        # Method 5: Try EarningsWhispers
        if not earnings_list:
            ew_earnings = self._get_earningswhispers_earnings(target_date)
            if ew_earnings:
                earnings_list.extend(ew_earnings)
                print(f"[EARNINGS] EarningsWhispers returned {len(ew_earnings)} earnings")
        
        # Method 6: Try Zacks
        if not earnings_list:
            zacks_earnings = self._get_zacks_earnings(target_date)
            if zacks_earnings:
                earnings_list.extend(zacks_earnings)
                print(f"[EARNINGS] Zacks returned {len(zacks_earnings)} earnings")
        
        # Remove duplicates
        if earnings_list:
            seen = set()
            unique_earnings = []
            for earning in earnings_list:
                key = (earning['symbol'], earning['date'])
                if key not in seen:
                    seen.add(key)
                    unique_earnings.append(earning)
            earnings_list = unique_earnings
        
        return earnings_list
    
    def _get_earningswhispers_earnings(self, target_date: date) -> List[Dict[str, Any]]:
        """Get earnings from EarningsWhispers"""
        earnings_list = []
        try:
            print(f"[EARNINGS] Trying EarningsWhispers for {target_date}...")
            date_str = target_date.strftime("%Y-%m-%d")
            url = f"https://www.earningswhispers.com/calendar?date={date_str}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')[1:]
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            try:
                                symbol = cells[0].get_text(strip=True).upper()
                                if symbol and len(symbol) <= 10:
                                    company = cells[1].get_text(strip=True) if len(cells) > 1 else symbol
                                    time_info = 'TBD'
                                    if len(cells) > 2:
                                        time_str = cells[2].get_text(strip=True).lower()
                                        if 'before' in time_str or 'bmo' in time_str:
                                            time_info = 'Before Market Open'
                                        elif 'after' in time_str or 'amc' in time_str:
                                            time_info = 'After Market Close'
                                    
                                    earnings_list.append({
                                        'symbol': symbol,
                                        'company': company,
                                        'date': target_date.isoformat(),
                                        'time': time_info,
                                        'source': 'earningswhispers'
                                    })
                            except:
                                continue
        except Exception as e:
            print(f"[EARNINGS] EarningsWhispers error: {e}")
        
        return earnings_list
    
    def _get_finviz_earnings(self, target_date: date) -> List[Dict[str, Any]]:
        """Get earnings from Finviz - very reliable source"""
        earnings_list = []
        try:
            print(f"[EARNINGS] Trying Finviz for {target_date}...")
            # Finviz earnings calendar
            date_str = target_date.strftime("%b-%d-%Y")  # Format: Jan-13-2025
            url = f"https://finviz.com/calendar.ashx?d={target_date.day}&m={target_date.month}&y={target_date.year}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finviz.com/'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Finviz returns CSV-like data
                try:
                    lines = response.text.strip().split('\n')
                    for line in lines[1:]:  # Skip header
                        parts = line.split('|')
                        if len(parts) >= 3:
                            try:
                                symbol = parts[0].strip().upper()
                                company = parts[1].strip() if len(parts) > 1 else symbol
                                time_str = parts[2].strip().lower() if len(parts) > 2 else ''
                                
                                if symbol and len(symbol) <= 10:
                                    time_info = 'TBD'
                                    if 'bmo' in time_str or 'before' in time_str:
                                        time_info = 'Before Market Open'
                                    elif 'amc' in time_str or 'after' in time_str:
                                        time_info = 'After Market Close'
                                    elif 'dmh' in time_str:
                                        time_info = 'During Market Hours'
                                    
                                    earnings_list.append({
                                        'symbol': symbol,
                                        'company': company,
                                        'date': target_date.isoformat(),
                                        'time': time_info,
                                        'source': 'finviz'
                                    })
                            except:
                                continue
                except:
                    # Try HTML parsing as fallback
                    soup = BeautifulSoup(response.content, 'html.parser')
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')[1:]
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                try:
                                    symbol = cells[0].get_text(strip=True).upper()
                                    if symbol and len(symbol) <= 10:
                                        company = cells[1].get_text(strip=True) if len(cells) > 1 else symbol
                                        time_info = 'TBD'
                                        if len(cells) > 2:
                                            time_str = cells[2].get_text(strip=True).lower()
                                            if 'bmo' in time_str or 'before' in time_str:
                                                time_info = 'Before Market Open'
                                            elif 'amc' in time_str or 'after' in time_str:
                                                time_info = 'After Market Close'
                                        
                                        earnings_list.append({
                                            'symbol': symbol,
                                            'company': company,
                                            'date': target_date.isoformat(),
                                            'time': time_info,
                                            'source': 'finviz'
                                        })
                                except:
                                    continue
        except Exception as e:
            print(f"[EARNINGS] Finviz error: {e}")
        
        return earnings_list
    
    def _get_marketwatch_earnings(self, target_date: date) -> List[Dict[str, Any]]:
        """Get earnings from MarketWatch"""
        earnings_list = []
        try:
            print(f"[EARNINGS] Trying MarketWatch for {target_date}...")
            # MarketWatch earnings calendar
            date_str = target_date.strftime("%Y-%m-%d")
            url = f"https://www.marketwatch.com/tools/calendars/earnings?date={date_str}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.marketwatch.com/'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # MarketWatch uses various structures - try to find earnings table
                tables = soup.find_all('table', class_=lambda x: x and ('earnings' in x.lower() or 'calendar' in x.lower()))
                if not tables:
                    tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')[1:]
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            try:
                                symbol = cells[0].get_text(strip=True).upper()
                                if symbol and len(symbol) <= 10 and not symbol.startswith('$'):
                                    company = cells[1].get_text(strip=True) if len(cells) > 1 else symbol
                                    time_info = 'TBD'
                                    if len(cells) > 2:
                                        time_str = cells[2].get_text(strip=True).lower()
                                        if 'before' in time_str or 'bmo' in time_str:
                                            time_info = 'Before Market Open'
                                        elif 'after' in time_str or 'amc' in time_str:
                                            time_info = 'After Market Close'
                                    
                                    earnings_list.append({
                                        'symbol': symbol,
                                        'company': company,
                                        'date': target_date.isoformat(),
                                        'time': time_info,
                                        'source': 'marketwatch'
                                    })
                            except:
                                continue
        except Exception as e:
            print(f"[EARNINGS] MarketWatch error: {e}")
        
        return earnings_list

    def _get_yahoo_earnings_calendar(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get earnings from Yahoo Earnings Calendar (range)"""
        earnings_list = []
        if not YAHOO_EARNINGS_AVAILABLE:
            return []
            
        try:
            print(f"[EARNINGS] Fetching Yahoo Earnings Calendar from {start_date} to {end_date}...")
            yec = YahooEarningsCalendar()
            
            # Convert dates to datetime (start of day / end of day)
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            # fetch earnings between dates
            data = yec.earnings_between(start_dt, end_dt)
            
            print(f"[EARNINGS] Yahoo Earnings Calendar returned {len(data)} raw entries")
            
            for entry in data:
                try:
                    symbol = entry.get('ticker', '').strip().upper()
                    if not symbol:
                        continue
                        
                    # Parse date
                    date_str = entry.get('startdatetime', '')
                    if not date_str:
                        continue
                        
                    # format: 2025-01-15T10:00:00.000Z
                    earning_date = date_str.split('T')[0]
                    
                    company = entry.get('companyshortname', symbol)
                    
                    time_info = 'TBD'
                    start_type = entry.get('startdatetimetype', '').lower()
                    if 'bmo' in start_type or 'before' in start_type:
                        time_info = 'Before Market Open'
                    elif 'amc' in start_type or 'after' in start_type:
                        time_info = 'After Market Close'
                    elif 'tas' in start_type:
                        time_info = 'Time Not Supplied'
                        
                    earnings_list.append({
                        'symbol': symbol,
                        'company': company,
                        'date': earning_date,
                        'time': time_info,
                        'epsestimate': entry.get('epsestimate'),
                        'epsactual': entry.get('epsactual'),
                        'source': 'yahoo_earnings_calendar'
                    })
                except:
                    continue
                    
        except Exception as e:
            print(f"[EARNINGS] Yahoo Earnings Calendar error: {e}")
            
        return earnings_list

    async def get_earnings(self, start_date: date, end_date: date, alpaca_api_key: Optional[str] = None, 
                          alpaca_api_secret: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get earnings for a date range
        """
        loop = asyncio.get_event_loop()
        print(f"\n[EARNINGS] Getting earnings from {start_date} to {end_date}")
        
        earnings_list = []
        
        # 1. Try Yahoo Earnings Calendar (Best for ranges)
        if YAHOO_EARNINGS_AVAILABLE:
            yahoo_earnings = await loop.run_in_executor(None, self._get_yahoo_earnings_calendar, start_date, end_date)
            if yahoo_earnings:
                earnings_list.extend(yahoo_earnings)
                print(f"[EARNINGS] ✅ Yahoo Earnings Calendar: {len(yahoo_earnings)} earnings")
                
                # Cache results by day
                # Group by date
                earnings_by_date = {}
                for e in yahoo_earnings:
                    d = e['date']
                    if d not in earnings_by_date:
                        earnings_by_date[d] = []
                    earnings_by_date[d].append(e)
                
                # Save to cache
                for d_str, items in earnings_by_date.items():
                    try:
                        d = date.fromisoformat(d_str)
                        self._save_to_cache(d, items)
                    except:
                        pass
                        
                return earnings_list

        # 2. Fallback: If range is small (<= 5 days), try Nasdaq/Finviz day by day
        delta = (end_date - start_date).days
        if delta <= 5:
            print(f"[EARNINGS] Range small ({delta} days), using fallback sources...")
            current = start_date
            while current <= end_date:
                # Use existing _get_nasdaq_earnings which handles caching
                day_earnings = await loop.run_in_executor(None, self._get_nasdaq_earnings, current, True)
                earnings_list.extend(day_earnings)
                current += timedelta(days=1)
        else:
            print("[EARNINGS] Range too large for fallback methods, and Yahoo failed. Returning empty list.")
            
        # Remove duplicates
        seen = set()
        unique_earnings = []
        for earning in earnings_list:
            key = (earning.get('symbol', ''), earning.get('date', ''))
            if key not in seen:
                seen.add(key)
                unique_earnings.append(earning)
        
        unique_earnings.sort(key=lambda x: (x.get('date', ''), x.get('symbol', '')))
        return unique_earnings

    async def get_earnings_today_tomorrow(self, alpaca_api_key: Optional[str] = None, 
                                         alpaca_api_secret: Optional[str] = None) -> List[Dict[str, Any]]:
        """Wrapper for backward compatibility"""
        now = datetime.now().date()
        today, tomorrow = get_next_business_days(now)
        return await self.get_earnings(today, tomorrow, alpaca_api_key, alpaca_api_secret)
    
    def _get_calendar_cache_key(self, start_date: date, months: int) -> str:
        """Generate cache key for calendar range (6 months at a time)"""
        return f"calendar_{start_date.isoformat()}_months_{months}"
    
    def _get_from_calendar_cache(self, start_date: date, months: int) -> Optional[List[Dict[str, Any]]]:
        """Get earnings from calendar cache (6 months at a time, 24h TTL)"""
        cache_key = self._get_calendar_cache_key(start_date, months)
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            cache_time = cache_entry.get('timestamp', 0)
            current_time = time.time()
            
            if current_time - cache_time < self.calendar_cache_ttl:
                age_hours = int((current_time - cache_time) / 3600)
                print(f"[EARNINGS] ✅ Calendar cache hit for {start_date.isoformat()} ({months} months) (age: {age_hours}h)")
                return cache_entry.get('data', [])
            else:
                del self.cache[cache_key]
                print(f"[EARNINGS] ⏰ Calendar cache expired for {start_date.isoformat()} ({months} months)")
        
        return None
    
    def _save_to_calendar_cache(self, start_date: date, months: int, earnings: List[Dict[str, Any]]):
        """Save earnings to calendar cache (6 months at a time)"""
        cache_key = self._get_calendar_cache_key(start_date, months)
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'data': earnings,
            'start_date': start_date.isoformat(),
            'months': months
        }
        self._save_entry(cache_key, self.cache[cache_key])
        print(f"[EARNINGS] 💾 Saved to calendar cache: {start_date.isoformat()} ({months} months, {len(earnings)} earnings)")
    
    async def get_earnings_calendar(self, start_date: Optional[str] = None, months: int = 6, offset_months: int = 0) -> List[Dict[str, Any]]:
        """
        Get earnings calendar for N months starting from start_date (or today)
        Default: 6 months at a time with 24h cache refresh
        Uses Nasdaq API as PRIMARY source - FAST and RELIABLE
        """
        loop = asyncio.get_event_loop()
        
        if start_date is None:
            start_date_obj = datetime.now().date()
        else:
            try:
                start_date_obj = datetime.fromisoformat(start_date).date()
            except:
                start_date_obj = datetime.now().date()
        
        # Calculate date range: offset_months determines which 6-month block to load
        # For infinite scroll: offset_months=0 (first 6 months), offset_months=1 (next 6 months), etc.
        calendar_start = start_date_obj + timedelta(days=offset_months * 180)  # ~6 months
        calendar_end = calendar_start + timedelta(days=months * 30)  # ~N months
        
        # Adjust end date to be more precise (approximately 6 months = 180 days)
        if months == 6:
            calendar_end = calendar_start + timedelta(days=180)
        
        # Check calendar cache first (6-month blocks with 24h TTL)
        cached_earnings = self._get_from_calendar_cache(calendar_start, months)
        if cached_earnings is not None:
            # Filter to the requested date range
            filtered = [e for e in cached_earnings if calendar_start <= datetime.fromisoformat(e.get('date', '')).date() <= calendar_end]
            print(f"[EARNINGS] ✅ Returning {len(filtered)} earnings from cache (filtered to range)")
            return filtered

        print("=" * 60)
        print(f"[EARNINGS] STARTING CALENDAR FETCH (Nasdaq API with 24h cache)")
        print(f"[EARNINGS] Date range: {calendar_start} to {calendar_end} ({months} months, offset: {offset_months})")
        print("=" * 60)
        
        earnings_list = []
        start_time = time.time()
        
        # Fetch earnings for each day in the range (respects per-date cache)
        current_date = calendar_start
        dates_to_fetch = []
        
        while current_date <= calendar_end:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:  # Monday=0 to Friday=4
                dates_to_fetch.append(current_date)
            current_date += timedelta(days=1)
        
        print(f"[EARNINGS] Fetching earnings for {len(dates_to_fetch)} dates (with 24h cache per date)...")
        
        # Fetch in parallel using asyncio (respects per-date cache)
        async def fetch_date_earnings(target_date: date):
            return await loop.run_in_executor(None, self._get_nasdaq_earnings, target_date, True)
        
        # Fetch all dates (uses cache per date, very fast)
        # Process in batches to avoid overwhelming the API
        batch_size = 30  # Process 30 days at a time
        for i in range(0, len(dates_to_fetch), batch_size):
            batch = dates_to_fetch[i:i+batch_size]
            tasks = [fetch_date_earnings(date) for date in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"[EARNINGS] Error fetching {batch[idx]}: {result}")
                elif result:
                    earnings_list.extend(result)
        
        elapsed = time.time() - start_time
        
        # Remove duplicates and sort
        print(f"\n[EARNINGS] Processing results...")
        seen = set()
        unique_earnings = []
        for earning in earnings_list:
            key = (earning.get('symbol', earning.get('ticker', '')), earning.get('date', ''))
            if key not in seen:
                seen.add(key)
                unique_earnings.append(earning)
        
        # Sort by date
        unique_earnings.sort(key=lambda x: x.get('date', ''))
        
        # Save to calendar cache (6-month block)
        if unique_earnings:
            self._save_to_calendar_cache(calendar_start, months, unique_earnings)
        
        print(f"[EARNINGS] ✅ FETCH COMPLETE: {len(unique_earnings)} unique earnings in {elapsed:.2f} seconds")
        print(f"[EARNINGS] Date range covered: {calendar_start} to {calendar_end}")
        if unique_earnings:
            print(f"[EARNINGS] First: {unique_earnings[0].get('symbol')} on {unique_earnings[0].get('date')}")
            print(f"[EARNINGS] Last: {unique_earnings[-1].get('symbol')} on {unique_earnings[-1].get('date')}")
        print("=" * 60)
        
        return unique_earnings

    def _filter_earnings(self, earnings_list, start_date, weeks, offset):
        # Filter to only include earnings in the requested range
        # Use a wider range to catch earnings near the target week
        filtered_earnings = []
        actual_start = start_date + timedelta(weeks=offset) 
        # Ensure we cover at least the week requested (7 days)
        actual_end = actual_start + timedelta(weeks=max(1, weeks))
        
        # Expand range slightly to catch earnings just outside (e.g. weekend before/after)
        display_start = actual_start - timedelta(days=1)
        display_end = actual_end + timedelta(days=1)
        
        print(f"Filtering earnings for display range: {display_start} to {display_end}")
        
        for earning in earnings_list:
            try:
                earning_date = datetime.fromisoformat(earning['date']).date()
                # Relaxed filtering: Include if within range OR if list is empty and it's close
                if display_start <= earning_date <= display_end:
                    filtered_earnings.append(earning)
                else:
                    # Debug print for skipped items
                    # print(f"Skipping earning for {earning['symbol']} on {earning_date} (outside {display_start}-{display_end})")
                    pass
            except Exception as e:
                # Skip earnings with invalid dates
                continue
        
        # If filtering removed everything, return the original list (fallback)
        # taking only the first 20 items to avoid overwhelming the UI
        if not filtered_earnings and earnings_list:
            print("Filter removed all earnings! Returning unfiltered list (truncated).")
            # Sort by date anyway
            earnings_list.sort(key=lambda x: x.get('date', ''))
            return earnings_list[:20]

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
        
        print(f"Returning {len(unique_earnings)} filtered earnings")
        return unique_earnings

    def _generate_mock_earnings(self, start_date, end_date) -> List[Dict[str, Any]]:
        """Generate mock earnings for demonstration when no data is found"""
        mock_earnings = []
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'NFLX', 'AMD', 'META', 'JPM', 'BAC', 'DIS', 'WMT', 'KO', 'PEP', 'COST', 'ADBE', 'CRM', 'INTC', 'PYPL']
        
        # Generate earnings for every day in the range
        current_date = start_date
        ticker_idx = 0
        
        # Ensure we have at least one earning for today if it's a weekday
        today = datetime.now().date()
        
        while current_date <= end_date:
            # Generate for weekdays, and maybe some for today even if it's weekend (for demo purposes)
            if current_date.weekday() < 5 or current_date == today:
                # Add 3-5 earnings per day to ensure density
                count = 4
                for _ in range(count):
                    if ticker_idx < len(tickers):
                        ticker = tickers[ticker_idx]
                        mock_earnings.append({
                            'symbol': ticker,
                            'company': f"{ticker} Inc.",
                            'date': current_date.isoformat(),
                            'time': 'After Close' if ticker_idx % 2 == 0 else 'Before Open',
                            'source': 'mock'
                        })
                        ticker_idx = (ticker_idx + 1) % len(tickers)
            current_date += timedelta(days=1)
            
        return mock_earnings
    
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
    
    def _get_sp500_tickers(self) -> List[str]:
        """Get comprehensive list of S&P 500 tickers - expanded list for complete earnings coverage"""
        # Comprehensive S&P 500 ticker list (top 200+ companies)
        return [
            # Tech Giants (30+)
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
            'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'CSCO', 'IBM', 'QCOM', 'AVGO',
            'NOW', 'SNPS', 'CDNS', 'ANSS', 'FTNT', 'ZS', 'CRWD', 'PANW', 'NET',
            'DDOG', 'TEAM', 'DOCN', 'FROG', 'ESTC', 'INTU', 'PYPL', 'COIN', 'MU',
            'LRCX', 'AMAT', 'KLAC', 'MCHP', 'SWKS', 'QRVO', 'MPWR', 'ON', 'TXN',
            # Financials (40+)
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'MA', 'V',
            'COF', 'USB', 'PNC', 'TFC', 'BK', 'STT', 'CFG', 'HBAN', 'KEY', 'MTB',
            'AIG', 'ALL', 'AON', 'AFL', 'BEN', 'BRO', 'CBOE', 'CINF', 'FDS', 'FITB',
            'GL', 'HIG', 'L', 'MCO', 'MMC', 'PGR', 'PRU', 'RJF', 'TROW', 'TRV',
            # Healthcare (50+)
            'UNH', 'JNJ', 'ABBV', 'MRK', 'PFE', 'TMO', 'ABT', 'DHR', 'LLY', 'BMY',
            'AMGN', 'GILD', 'REGN', 'VRTX', 'BIIB', 'ILMN', 'ALXN', 'MRNA', 'SYK',
            'ZBH', 'BAX', 'EW', 'BSX', 'ISRG', 'HCA', 'CI', 'HUM', 'ELV', 'CNC',
            'CVS', 'WBA', 'DGX', 'LH', 'TECH', 'ALGN', 'COO', 'DXCM', 'HOLX', 'IDXX',
            'IQV', 'MTD', 'RMD', 'STE', 'TFX', 'WAT', 'ZTS', 'A', 'BDX', 'BIO',
            # Consumer Discretionary (40+)
            'WMT', 'HD', 'TGT', 'COST', 'LOW', 'TJX', 'DG', 'ROST', 'BBY', 'NKE',
            'SBUX', 'MCD', 'YUM', 'CMG', 'DPZ', 'WEN', 'DIN', 'CAKE', 'EBAY', 'ETSY',
            'GRMN', 'GPS', 'HAS', 'LEG', 'LULU', 'MHK', 'NKE', 'NWL', 'PHM', 'POOL',
            'RL', 'ROST', 'TPR', 'ULTA', 'VFC', 'WHR', 'WSM', 'BBWI', 'DKS', 'FIVE',
            # Communication (20+)
            'VZ', 'T', 'CMCSA', 'DIS', 'NFLX', 'FOXA', 'FOX', 'VIAC', 'PARA', 'LUMN',
            'OMC', 'IPG', 'WPP', 'PUBM', 'TTD', 'MGNI', 'PERI', 'TRMR', 'ADTN',
            # Industrials (50+)
            'BA', 'CAT', 'GE', 'HON', 'DE', 'RTX', 'LMT', 'NOC', 'GD', 'TDG',
            'ETN', 'EMR', 'ITW', 'PH', 'ROK', 'AME', 'GGG', 'DOV', 'AOS', 'ARNC',
            'AYI', 'BWA', 'CARR', 'CHRW', 'CTAS', 'FAST', 'FERG', 'FTV', 'GWW', 'HWM',
            'IR', 'J', 'LDOS', 'MAS', 'NDAQ', 'NLSN', 'OTIS', 'PCAR', 'PNR', 'ROL',
            'ROP', 'RSG', 'TDY', 'TXT', 'URI', 'VRSK', 'WWD', 'XYL', 'ZBRA',
            # Energy (20+)
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'HAL', 'OXY',
            'FANG', 'MRO', 'OVV', 'CTRA', 'DVN', 'EQT', 'HES', 'MTDR', 'PR', 'SM',
            # Materials (30+)
            'LIN', 'APD', 'ECL', 'SHW', 'PPG', 'DD', 'DOW', 'FCX', 'NEM', 'VALE',
            'ALB', 'AMCR', 'AVY', 'BALL', 'CCK', 'CF', 'CMC', 'CRH', 'FMC', 'IFF',
            'IP', 'MOS', 'NUE', 'PKG', 'SEE', 'SHW', 'VMC', 'WRK', 'X', 'CLF',
            # Utilities (20+)
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'SRE', 'EXC', 'XEL', 'PEG', 'ES',
            'AES', 'ATO', 'CMS', 'CNP', 'ED', 'EIX', 'ETR', 'FE', 'LNT', 'NI',
            # Real Estate (30+)
            'AMT', 'PLD', 'EQIX', 'PSA', 'WELL', 'SPG', 'O', 'DLR', 'EXPI', 'AVB',
            'BXP', 'CBRE', 'CPT', 'EQR', 'ESS', 'FR', 'HST', 'IRM', 'KIM', 'MAA',
            'PEAK', 'PLD', 'PSA', 'REG', 'SBAC', 'UDR', 'VICI', 'VTR', 'WELL', 'WPC',
            # Consumer Staples (30+)
            'PG', 'KO', 'PEP', 'WMT', 'COST', 'TGT', 'CL', 'KMB', 'CHD', 'CLX',
            'CAG', 'CPB', 'GIS', 'HRL', 'HSY', 'K', 'KHC', 'MDLZ', 'SJM', 'STZ',
            'TAP', 'TSN', 'WBA', 'WDFC', 'BF.B', 'BF-B'
        ]
    
    def _get_popular_tickers_earnings(self, start_date, end_date, custom_tickers=None) -> List[Dict[str, Any]]:
        """Get earnings for popular tickers using yfinance"""
        earnings = []
        
        if custom_tickers:
            popular_tickers = custom_tickers
        else:
            # Expanded list of popular tickers
            popular_tickers = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
                'AMD', 'INTC', 'JPM', 'BAC', 'WMT', 'DIS', 'V', 'MA',
                'CRM', 'ORCL', 'ADBE', 'CSCO', 'IBM', 'QCOM', 'AVGO',
                'COST', 'HD', 'MCD', 'NKE', 'TGT', 'GS', 'JNJ', 'PG',
                'KO', 'PEP', 'WFC', 'C', 'AXP', 'UNH', 'JNJ', 'VZ', 'T'
            ]
        
        print(f"\n[EARNINGS] _get_popular_tickers_earnings called")
        print(f"[EARNINGS] Date range: {start_date} to {end_date}")
        print(f"[EARNINGS] Total tickers available: {len(popular_tickers)}")
        
        # Process tickers in batches to avoid timeout
        # Limit to first 100 tickers to avoid timeout, but process them all
        max_tickers = 100
        tickers_to_check = popular_tickers[:max_tickers] if len(popular_tickers) > max_tickers else popular_tickers
        print(f"[EARNINGS] Processing {len(tickers_to_check)} tickers (out of {len(popular_tickers)} available)")
        print(f"[EARNINGS] Tickers to check: {', '.join(tickers_to_check[:10])}... (showing first 10)")
        
        for idx, ticker in enumerate(tickers_to_check):
            try:
                if idx % 10 == 0:
                    print(f"[{idx+1}/{len(tickers_to_check)}] Checking {ticker}...")
                tk = yf.Ticker(ticker)
                # Use timeout for info fetch - skip if it takes too long
                try:
                    info = tk.info
                    # Skip if info is empty or None
                    if not info:
                        continue
                except Exception as e:
                    # Skip this ticker if there's an error - don't print every error to avoid spam
                    if idx % 20 == 0:
                        print(f"  {ticker}: Error getting info (skipping)")
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
                            if idx % 10 == 0:
                                print(f"  [EARNINGS] Found earnings for {ticker} on {earnings_date}")
                    except Exception as e:
                        # Skip parsing errors silently
                        pass
                
                # Method 2: Try to get from calendar (more reliable)
                try:
                    calendar = tk.calendar
                    if calendar is not None:
                        # Calendar is a dict with 'Earnings Date' key containing a list of dates
                        if isinstance(calendar, dict):
                            earnings_dates = calendar.get('Earnings Date', [])
                            if earnings_dates:
                                # Only print for every 10th ticker to avoid spam
                                if idx % 10 == 0:
                                    print(f"  {ticker}: Calendar has {len(earnings_dates)} earnings dates")
                                for earning_date_obj in earnings_dates:
                                    try:
                                        # earnings_dates is a list of datetime.date objects
                                        if isinstance(earning_date_obj, datetime):
                                            cal_date = earning_date_obj.date()
                                        elif isinstance(earning_date_obj, pd.Timestamp):
                                            cal_date = earning_date_obj.date()
                                        elif isinstance(earning_date_obj, date):
                                            cal_date = earning_date_obj
                                        else:
                                            cal_date = pd.to_datetime(earning_date_obj).date()
                                        
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
                                                if idx % 10 == 0:
                                                    print(f"  [EARNINGS] Found earnings for {ticker} on {cal_date} from calendar")
                                    except Exception as e:
                                        # Skip parsing errors silently
                                        continue
                            # else: No Earnings Date in calendar - skip silently
                        elif hasattr(calendar, 'empty') and not calendar.empty:
                            # Old DataFrame format (for backwards compatibility)
                            if idx % 10 == 0:
                                print(f"  {ticker}: Calendar has {len(calendar)} entries (DataFrame)")
                            for idx in calendar.index:
                                try:
                                    if isinstance(idx, pd.Timestamp):
                                        cal_date = idx.date()
                                    else:
                                        cal_date = pd.to_datetime(idx).date()
                                    
                                    if start_date <= cal_date <= end_date:
                                        existing = [e for e in earnings if e['symbol'] == ticker and e['date'] == cal_date.isoformat()]
                                        if not existing:
                                            earnings.append({
                                                'symbol': ticker,
                                                'company': info.get('longName', info.get('shortName', ticker)),
                                                'date': cal_date.isoformat(),
                                                'time': 'TBD',
                                                'source': 'yfinance'
                                            })
                                            if idx % 10 == 0:
                                                print(f"  [EARNINGS] Found earnings for {ticker} on {cal_date} from calendar")
                                except Exception as e:
                                    # Skip processing errors silently
                                    continue
                        # else: Calendar is empty or None - skip silently
                    # else: No calendar data - skip silently
                except Exception as e:
                    # Skip calendar errors silently to avoid spam
                    pass
                    
            except Exception as e:
                # Skip unexpected errors silently
                continue
        
        print(f"\n[EARNINGS] _get_popular_tickers_earnings complete")
        print(f"[EARNINGS] Total earnings found: {len(earnings)}")
        if earnings:
            print(f"[EARNINGS] Sample: {earnings[0].get('symbol')} on {earnings[0].get('date')}")
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
    
    async def get_ticker_eps_history(self, ticker: str, years: int = 2) -> List[Dict[str, Any]]:
        """
        Get EPS history for a ticker for the last N years (default 2 years = ~8 quarters)
        Returns list of quarterly earnings with EPS actual and estimate
        """
        loop = asyncio.get_event_loop()
        
        def fetch_eps_history():
            eps_history = []
            
            try:
                # Method 1: Try yahoo_fin (most reliable for EPS history)
                try:
                    import yahoo_fin.stock_info as si
                    print(f"[EARNINGS] Fetching EPS history for {ticker} using yahoo_fin...")
                    history = si.get_earnings_history(ticker)
                    
                    if history and len(history) > 0:
                        # Calculate cutoff date (years ago)
                        cutoff_date = datetime.now() - timedelta(days=years * 365)
                        
                        for entry in history:
                            try:
                                if isinstance(entry, dict):
                                    # Yahoo_fin format
                                    earnings_date_str = entry.get('startdatetime', entry.get('startdatetimetype', entry.get('date')))
                                    eps_estimate = entry.get('epsestimate')
                                    eps_actual = entry.get('epsactual')
                                    
                                    if earnings_date_str:
                                        # Parse date (could be timestamp, datetime string, etc.)
                                        if isinstance(earnings_date_str, (int, float)):
                                            earnings_date = datetime.fromtimestamp(earnings_date_str).date()
                                        elif isinstance(earnings_date_str, datetime):
                                            earnings_date = earnings_date_str.date()
                                        elif isinstance(earnings_date_str, str):
                                            try:
                                                earnings_date = datetime.fromisoformat(earnings_date_str.split('T')[0]).date()
                                            except:
                                                try:
                                                    earnings_date = datetime.strptime(earnings_date_str.split()[0], '%Y-%m-%d').date()
                                                except:
                                                    continue
                                        else:
                                            continue
                                        
                                        # Only include if within time range
                                        if earnings_date >= cutoff_date.date():
                                            eps_history.append({
                                                'date': earnings_date.isoformat(),
                                                'quarter': entry.get('quarter', f"Q{(earnings_date.month - 1) // 3 + 1} {earnings_date.year}"),
                                                'eps_estimate': float(eps_estimate) if eps_estimate is not None and eps_estimate != '' else None,
                                                'eps_actual': float(eps_actual) if eps_actual is not None and eps_actual != '' else None,
                                                'surprise': entry.get('epsdifference', entry.get('surprise')),
                                                'surprise_percent': entry.get('surprisepercent', entry.get('surprise_percent')),
                                                'year': earnings_date.year,
                                                'quarter_number': (earnings_date.month - 1) // 3 + 1
                                            })
                            except Exception as e:
                                print(f"[EARNINGS] Error parsing yahoo_fin entry for {ticker}: {e}")
                                continue
                        
                        # Sort by date descending (most recent first)
                        eps_history.sort(key=lambda x: x['date'], reverse=True)
                        
                        print(f"[EARNINGS] ✅ yahoo_fin returned {len(eps_history)} quarters for {ticker}")
                        return eps_history
                except ImportError:
                    print(f"[EARNINGS] yahoo_fin not available, trying yfinance...")
                except Exception as e:
                    print(f"[EARNINGS] yahoo_fin error for {ticker}: {e}")
                
                # Method 2: Try yfinance (fallback)
                try:
                    print(f"[EARNINGS] Fetching EPS history for {ticker} using yfinance...")
                    tk = yf.Ticker(ticker)
                    
                    # Get earnings history - yfinance might have this in earnings or info
                    try:
                        earnings_data = tk.earnings
                        if earnings_data is not None and not earnings_data.empty:
                            cutoff_date = datetime.now() - timedelta(days=years * 365)
                            
                            for idx, row in earnings_data.iterrows():
                                try:
                                    if isinstance(idx, pd.Timestamp):
                                        earnings_date = idx.date()
                                    elif isinstance(idx, datetime):
                                        earnings_date = idx.date()
                                    else:
                                        earnings_date = pd.to_datetime(idx).date()
                                    
                                    if earnings_date >= cutoff_date.date():
                                        eps_history.append({
                                            'date': earnings_date.isoformat(),
                                            'quarter': f"Q{(earnings_date.month - 1) // 3 + 1} {earnings_date.year}",
                                            'eps_estimate': float(row.get('Earnings Estimate', 0)) if pd.notna(row.get('Earnings Estimate')) else None,
                                            'eps_actual': float(row.get('Reported EPS', row.get('Actual EPS', 0))) if pd.notna(row.get('Reported EPS', row.get('Actual EPS'))) else None,
                                            'surprise': None,
                                            'surprise_percent': None,
                                            'year': earnings_date.year,
                                            'quarter_number': (earnings_date.month - 1) // 3 + 1
                                        })
                                except:
                                    continue
                            
                            if eps_history:
                                eps_history.sort(key=lambda x: x['date'], reverse=True)
                                print(f"[EARNINGS] ✅ yfinance returned {len(eps_history)} quarters for {ticker}")
                                return eps_history
                    except:
                        pass
                    
                    # Alternative: try to get from quarterly_financials
                    try:
                        financials = tk.quarterly_financials
                        if financials is not None and not financials.empty:
                            # This is more complex, skip for now
                            pass
                    except:
                        pass
                    
                    # Alternative: try to get from earnings_dates
                    try:
                        earnings_dates = tk.earnings_dates
                        if earnings_dates is not None and not earnings_dates.empty:
                            cutoff_date = datetime.now() - timedelta(days=years * 365)
                            
                            for idx, row in earnings_dates.iterrows():
                                try:
                                    if isinstance(idx, pd.Timestamp):
                                        earnings_date = idx.date()
                                    else:
                                        earnings_date = pd.to_datetime(idx).date()
                                    
                                    if earnings_date >= cutoff_date.date():
                                        eps_history.append({
                                            'date': earnings_date.isoformat(),
                                            'quarter': f"Q{(earnings_date.month - 1) // 3 + 1} {earnings_date.year}",
                                            'eps_estimate': float(row.get('EPS Estimate', 0)) if pd.notna(row.get('EPS Estimate')) else None,
                                            'eps_actual': float(row.get('EPS Actual', 0)) if pd.notna(row.get('EPS Actual')) else None,
                                            'surprise': float(row.get('Surprise(%)', 0)) if pd.notna(row.get('Surprise(%)')) else None,
                                            'surprise_percent': float(row.get('Surprise(%)', 0)) if pd.notna(row.get('Surprise(%)')) else None,
                                            'year': earnings_date.year,
                                            'quarter_number': (earnings_date.month - 1) // 3 + 1
                                        })
                                except:
                                    continue
                            
                            if eps_history:
                                eps_history.sort(key=lambda x: x['date'], reverse=True)
                                print(f"[EARNINGS] ✅ yfinance earnings_dates returned {len(eps_history)} quarters for {ticker}")
                                return eps_history
                    except Exception as e:
                        print(f"[EARNINGS] yfinance earnings_dates error: {e}")
                
                except Exception as e:
                    print(f"[EARNINGS] yfinance error for {ticker}: {e}")
                
            except Exception as e:
                print(f"[EARNINGS] Error fetching EPS history for {ticker}: {e}")
                import traceback
                traceback.print_exc()
            
            return eps_history
        
        eps_history = await loop.run_in_executor(None, fetch_eps_history)
        
        # Calculate reliability metrics
        if eps_history:
            total_quarters = len(eps_history)
            beat_count = 0
            miss_count = 0
            meet_count = 0
            
            for entry in eps_history:
                eps_actual = entry.get('eps_actual')
                eps_estimate = entry.get('eps_estimate')
                
                if eps_actual is not None and eps_estimate is not None:
                    if float(eps_actual) > float(eps_estimate):
                        beat_count += 1
                        entry['result'] = 'beat'
                    elif float(eps_actual) < float(eps_estimate):
                        miss_count += 1
                        entry['result'] = 'miss'
                    else:
                        meet_count += 1
                        entry['result'] = 'meet'
            
            # Calculate beat rate
            quarters_with_data = beat_count + miss_count + meet_count
            beat_rate = (beat_count / quarters_with_data * 100) if quarters_with_data > 0 else 0
            
            # Add reliability score (0-100)
            reliability_score = beat_rate  # Simple score based on beat rate
            
            print(f"[EARNINGS] 📊 Reliability for {ticker}: Beat Rate {beat_rate:.1f}% ({beat_count}/{quarters_with_data} quarters)")
            
            return {
                'quarters': eps_history,
                'reliability': {
                    'beat_rate': round(beat_rate, 2),
                    'beat_count': beat_count,
                    'miss_count': miss_count,
                    'meet_count': meet_count,
                    'total_quarters': total_quarters,
                    'quarters_with_data': quarters_with_data,
                    'reliability_score': round(reliability_score, 2)
                }
            }
        
        return {
            'quarters': [],
            'reliability': {
                'beat_rate': 0,
                'beat_count': 0,
                'miss_count': 0,
                'meet_count': 0,
                'total_quarters': 0,
                'quarters_with_data': 0,
                'reliability_score': 0
            }
        }

