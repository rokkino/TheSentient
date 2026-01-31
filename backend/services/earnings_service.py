"""
Earnings Service - Handles earnings calendar data using Nasdaq API with caching
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import aiohttp
import asyncio
import os
import json
import time

class EarningsService:
    def __init__(self):
        # Cache directory for earnings data
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory', 'earnings')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache TTL: 12 hours (43200 seconds)
        self.cache_ttl = 12 * 60 * 60
    
    def _get_cached_earnings_for_date(self, target_date: date) -> Optional[List[Dict[str, Any]]]:
        """Get cached earnings for a specific date if available and not expired"""
        try:
            date_str = target_date.strftime('%Y-%m-%d')
            cache_file = os.path.join(self.cache_dir, f"earnings_{date_str}.json")
            
            if not os.path.exists(cache_file):
                print(f"[EarningsService] No cache file found for {date_str}: {cache_file}")
                return None
            
            print(f"[EarningsService] Found cache file for {date_str}, loading...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache has data (be lenient with timestamp - use cache if it exists)
            if 'data' not in cache_data:
                print(f"[EarningsService] Cache file for {date_str} has no 'data' field")
                return None
            
            # If timestamp exists, check age but be very lenient (30 days)
            if 'timestamp' in cache_data:
                cache_age = time.time() - cache_data['timestamp']
                max_cache_age = 30 * 24 * 60 * 60  # 30 days - very lenient
                if cache_age > max_cache_age:
                    print(f"[EarningsService] Cache too old for {date_str} (age: {cache_age/(24*3600):.1f} days), will refresh")
                    return None
                age_str = f"{cache_age/3600:.1f}h" if cache_age < 24*3600 else f"{cache_age/(24*3600):.1f}d"
                print(f"[EarningsService] Using cached earnings for {date_str} ({len(cache_data['data'])} items, age: {age_str})")
            else:
                # No timestamp - use it anyway if it has data
                print(f"[EarningsService] Using cached earnings for {date_str} ({len(cache_data['data'])} items, no timestamp)")
            
            return cache_data['data']
        except Exception as e:
            print(f"[EarningsService] Error reading cache for {target_date}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_earnings_to_cache(self, target_date: date, earnings: List[Dict[str, Any]]):
        """Save earnings to cache file"""
        try:
            date_str = target_date.strftime('%Y-%m-%d')
            cache_file = os.path.join(self.cache_dir, f"earnings_{date_str}.json")
            
            cache_data = {
                'timestamp': time.time(),
                'date': date_str,
                'data': earnings
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[EarningsService] Cached {len(earnings)} earnings for {date_str}")
        except Exception as e:
            print(f"[EarningsService] Error saving cache for {target_date}: {e}")
    
    def _get_cached_calendar(self, start_date: date, months: int) -> Optional[List[Dict[str, Any]]]:
        """Try to load a cached calendar file that covers the requested range"""
        try:
            # Look for calendar cache files
            # Format: calendar_YYYY-MM-DD_months_N.json
            start_str = start_date.strftime('%Y-%m-%d')
            cache_pattern = f"calendar_{start_str}_months_{months}.json"
            cache_file = os.path.join(self.cache_dir, cache_pattern)
            
            print(f"[EarningsService] Looking for calendar cache: {cache_file}")
            if os.path.exists(cache_file):
                print(f"[EarningsService] Found calendar cache file, loading...")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Check if cache has data
                if 'data' not in cache_data:
                    print(f"[EarningsService] Calendar cache has no 'data' field")
                    return None
                
                # Check if cache is still valid (be very lenient - 30 days)
                if 'timestamp' in cache_data:
                    cache_age = time.time() - cache_data['timestamp']
                    max_cache_age = 30 * 24 * 60 * 60  # 30 days
                    if cache_age <= max_cache_age:
                        age_str = f"{cache_age/3600:.1f}h" if cache_age < 24*3600 else f"{cache_age/(24*3600):.1f}d"
                        print(f"[EarningsService] Using cached calendar ({len(cache_data['data'])} items, age: {age_str})")
                        return cache_data['data']
                    else:
                        print(f"[EarningsService] Calendar cache too old (age: {cache_age/(24*3600):.1f} days)")
                else:
                    # No timestamp - use it anyway if it has data
                    print(f"[EarningsService] Using cached calendar ({len(cache_data['data'])} items, no timestamp)")
                    return cache_data['data']
            else:
                print(f"[EarningsService] Calendar cache file not found: {cache_file}")
            
            # Also try to find any calendar cache file that might cover our range
            # This helps if cache was created with a slightly different start date or months
            try:
                print(f"[EarningsService] Searching for alternative calendar cache files...")
                end_date = start_date + timedelta(days=30 * months)
                dates_in_range = set()
                current = start_date
                while current <= end_date:
                    dates_in_range.add(current)
                    current += timedelta(days=1)
                
                best_cache = None
                best_coverage = 0
                
                for filename in os.listdir(self.cache_dir):
                    if filename.startswith('calendar_') and filename.endswith('.json'):
                        alt_cache_file = os.path.join(self.cache_dir, filename)
                        try:
                            with open(alt_cache_file, 'r', encoding='utf-8') as f:
                                alt_cache_data = json.load(f)
                            
                            if 'data' not in alt_cache_data:
                                continue
                            
                            # Check timestamp if it exists
                            if 'timestamp' in alt_cache_data:
                                cache_age = time.time() - alt_cache_data['timestamp']
                                max_cache_age = 30 * 24 * 60 * 60  # 30 days
                                if cache_age > max_cache_age:
                                    continue
                            
                            # Check if the cached data covers our date range
                            cached_dates = set()
                            for earning in alt_cache_data['data']:
                                if 'date' in earning:
                                    try:
                                        date_str = earning['date']
                                        if 'T' in date_str:
                                            date_str = date_str.split('T')[0]
                                        earning_date = datetime.fromisoformat(date_str).date()
                                        cached_dates.add(earning_date)
                                    except Exception as parse_err:
                                        pass
                            
                            # Calculate coverage
                            matching_dates = dates_in_range.intersection(cached_dates)
                            coverage = len(matching_dates) / len(dates_in_range) if dates_in_range else 0
                            
                            if coverage > best_coverage and coverage >= 0.3:  # At least 30% coverage
                                best_coverage = coverage
                                best_cache = alt_cache_data['data']
                                print(f"[EarningsService] Found better calendar cache: {filename} ({len(alt_cache_data['data'])} items, {len(matching_dates)}/{len(dates_in_range)} dates covered, {coverage*100:.1f}%)")
                        except Exception as e:
                            print(f"[EarningsService] Error reading cache file {filename}: {e}")
                            continue
                
                if best_cache:
                    print(f"[EarningsService] Using best matching calendar cache ({len(best_cache)} items, {best_coverage*100:.1f}% coverage)")
                    return best_cache
            except Exception as e:
                print(f"[EarningsService] Error checking alternative calendar caches: {e}")
                import traceback
                traceback.print_exc()
            
            return None
        except Exception as e:
            print(f"[EarningsService] Error reading calendar cache: {e}")
            return None
    
    def _save_calendar_to_cache(self, start_date: date, months: int, earnings: List[Dict[str, Any]]):
        """Save calendar earnings to cache file"""
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            cache_file = os.path.join(self.cache_dir, f"calendar_{start_str}_months_{months}.json")
            
            cache_data = {
                'timestamp': time.time(),
                'start_date': start_str,
                'months': months,
                'data': earnings
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[EarningsService] Cached calendar: {len(earnings)} earnings for {months} months starting {start_str}")
        except Exception as e:
            print(f"[EarningsService] Error saving calendar cache: {e}")
    
    async def _get_nasdaq_earnings_for_date(self, target_date: date, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get earnings from Nasdaq API for a specific date, with caching"""
        # Check cache first
        if use_cache:
            cached = self._get_cached_earnings_for_date(target_date)
            if cached is not None:
                return cached
        
        # Fetch from API
        try:
            date_str = target_date.strftime('%Y-%m-%d')
            url = "https://api.nasdaq.com/api/calendar/earnings"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.nasdaq.com/'
            }
            
            params = {'date': date_str}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'data' in data and 'rows' in data['data']:
                            rows = data['data']['rows']
                            earnings = []
                            
                            for row in rows:
                                try:
                                    # Il formato Nasdaq è un dizionario con tutte le informazioni
                                    if isinstance(row, dict):
                                        symbol = str(row.get('symbol', row.get('Symbol', ''))).strip().upper()
                                        company = row.get('name', row.get('companyName', row.get('Company Name', symbol)))
                                        time_str = str(row.get('time', row.get('Time', 'time-not-supplied')))
                                        
                                        # Informazioni aggiuntive disponibili
                                        eps_forecast = row.get('epsForecast', row.get('epsEstimate', row.get('EPS Forecast')))
                                        last_year_eps = row.get('lastYearEPS', row.get('lastYearEps'))
                                        market_cap = row.get('marketCap', row.get('Market Cap'))
                                        fiscal_quarter = row.get('fiscalQuarterEnding', row.get('Fiscal Quarter Ending'))
                                        num_estimates = row.get('noOfEsts', row.get('noOfEstimates', row.get('# of Ests')))
                                        last_year_date = row.get('lastYearRptDt', row.get('lastYearReportDate'))
                                        
                                    elif isinstance(row, (list, tuple)) and len(row) >= 2:
                                        # Formato lista (meno comune)
                                        symbol = str(row[0]).strip().upper() if row[0] else None
                                        company = str(row[1]).strip() if len(row) > 1 and row[1] else symbol
                                        time_str = str(row[2]) if len(row) > 2 else 'time-not-supplied'
                                        eps_forecast = row[3] if len(row) > 3 else None
                                        last_year_eps = row[4] if len(row) > 4 else None
                                        market_cap = None
                                        fiscal_quarter = None
                                        num_estimates = None
                                        last_year_date = None
                                    else:
                                        continue
                                    
                                    if not symbol or len(symbol) > 10:
                                        continue
                                    
                                    if not company or company == 'N/A':
                                        company = symbol
                                    
                                    time_info = 'TBD'
                                    if time_str:
                                        time_lower = str(time_str).lower()
                                        if 'before' in time_lower or 'bmo' in time_lower or 'pre' in time_lower or 'pre-market' in time_lower:
                                            time_info = 'Before Market Open'
                                        elif 'after' in time_lower or 'amc' in time_lower or 'post' in time_lower or 'after-market' in time_lower:
                                            time_info = 'After Market Close'
                                        elif 'time-not-supplied' in time_lower or 'not supplied' in time_lower or time_lower == 'tbd':
                                            time_info = 'TBD'
                                    
                                    earnings.append({
                                        'symbol': symbol,
                                        'ticker': symbol,
                                        'company': company,
                                        'companymearningsshortname': company,
                                        'date': date_str,
                                        'time': time_info,
                                        'epsestimate': eps_forecast if eps_forecast not in [None, 'N/A', '', 'N/A'] else 'N/A',
                                        'epsactual': last_year_eps if last_year_eps not in [None, 'N/A', ''] else 'N/A',
                                        'marketCap': market_cap if market_cap not in [None, 'N/A', ''] else 'N/A',
                                        'fiscalQuarter': fiscal_quarter if fiscal_quarter not in [None, 'N/A', ''] else 'N/A',
                                        'numEstimates': num_estimates if num_estimates not in [None, 'N/A', ''] else 'N/A',
                                        'lastYearDate': last_year_date if last_year_date not in [None, 'N/A', ''] else 'N/A',
                                        'source': 'nasdaq_api'
                                    })
                                except Exception as e:
                                    print(f"Error parsing earning row: {e}")
                                    continue
                            
                            # Save to cache
                            if use_cache:
                                self._save_earnings_to_cache(target_date, earnings)
                            
                            return earnings
        except Exception as e:
            print(f"Error fetching earnings from Nasdaq for {target_date}: {e}")
            return []
        
        return []
    
    async def get_earnings_calendar(
        self,
        start_date: Optional[str] = None,
        months: int = 6,
        offset_months: int = 0,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Get earnings calendar data from Nasdaq API with caching"""
        try:
            # Calculate date range
            if start_date:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
            else:
                start = datetime.now().date()
            
            # Apply offset
            start = start + timedelta(days=30 * offset_months)
            
            # Calculate end date
            end = start + timedelta(days=30 * months)
            
            # Try to load from calendar cache first
            if use_cache:
                cached_calendar = self._get_cached_calendar(start, months)
                if cached_calendar is not None:
                    return cached_calendar
            
            # Get earnings from Nasdaq for each date in range
            earnings_list = []
            current_date = start
            
            # Collect dates to fetch (includiamo anche sabato e domenica)
            dates_to_fetch = []
            while current_date <= end:
                dates_to_fetch.append(current_date)
                current_date += timedelta(days=1)
            
            # Check cache for each date first, then fetch missing ones
            dates_to_fetch_from_api = []
            for d in dates_to_fetch:
                if use_cache:
                    cached = self._get_cached_earnings_for_date(d)
                    if cached is not None:
                        earnings_list.extend(cached)
                        continue
                dates_to_fetch_from_api.append(d)
            
            # Fetch missing dates from API in batches
            if dates_to_fetch_from_api:
                batch_size = 5
                for i in range(0, len(dates_to_fetch_from_api), batch_size):
                    batch = dates_to_fetch_from_api[i:i + batch_size]
                    batch_tasks = [self._get_nasdaq_earnings_for_date(d, use_cache=use_cache) for d in batch]
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, list):
                            earnings_list.extend(result)
                        elif isinstance(result, Exception):
                            print(f"Error in batch fetch: {result}")
                    
                    # Small delay between batches to be respectful to the API
                    if i + batch_size < len(dates_to_fetch_from_api):
                        await asyncio.sleep(0.1)
            
            # Save calendar to cache
            if use_cache and earnings_list:
                self._save_calendar_to_cache(start, months, earnings_list)
            
            print(f"[EarningsService] Retrieved {len(earnings_list)} earnings (from cache + API)")
            return earnings_list
            
        except Exception as e:
            print(f"Error in get_earnings_calendar: {e}")
            import traceback
            traceback.print_exc()
            return []

# Singleton instance
earnings_service = EarningsService()
