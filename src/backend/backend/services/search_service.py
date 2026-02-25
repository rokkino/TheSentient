"""
Search Service - Handles asset search
"""
import requests
import asyncio
from typing import List, Dict, Any
from services.ticker_database import search_local

# Common futures symbols that don't have =F suffix
COMMON_FUTURES = {
    'XAU': 'Gold Futures',
    'XAG': 'Silver Futures',
    'XPD': 'Palladium Futures',
    'XPT': 'Platinum Futures',
    'NG': 'Natural Gas Futures',
    'CL': 'Crude Oil Futures',
    'GC': 'Gold Futures',
    'SI': 'Silver Futures',
    'HG': 'Copper Futures',
    'ZC': 'Corn Futures',
    'ZS': 'Soybean Futures',
    'ZW': 'Wheat Futures',
    'ES': 'S&P 500 Futures',
    'NQ': 'Nasdaq 100 Futures',
    'YM': 'Dow Jones Futures',
    'RTY': 'Russell 2000 Futures',
    'ZB': 'U.S. Treasury Bond Futures',
    'ZN': '10-Year T-Note Futures',
}

class SearchService:
    def __init__(self):
        self.search_url = "https://query1.finance.yahoo.com/v1/finance/search"
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for assets - fast local search first, then Yahoo Finance"""
        if not query:
            return []
        
        query_upper = query.strip().upper()
        query_lower = query.strip().lower()
        
        # Step 1: Fast local search (instant, no network)
        local_results = search_local(query)
        if local_results:
            # If we found exact match or good results, return immediately
            if len(local_results) == 1 and local_results[0]['symbol'] == query_upper:
                return local_results  # Exact ticker match, return immediately
            if len(local_results) >= 3:  # Good number of results, return them
                return local_results
        
        # Step 2: If query looks like a ticker but not in local DB, return it directly
        # Only do this if we didn't find any local results, otherwise prefer local results or Yahoo
        if not local_results and len(query_upper) >= 1 and len(query_upper) <= 10:  # Increased length for crypto/futures (e.g., BTC-USD, CL=F)
            # Detect asset type based on symbol pattern
            asset_type = "EQUITY"
            name = query_upper
            
            # Check for common futures first
            if query_upper in COMMON_FUTURES:
                asset_type = "FUTURE"
                name = COMMON_FUTURES[query_upper]
            elif query_upper.endswith("-USD") or query_upper.endswith("-EUR") or query_upper.endswith("-GBP"):
                asset_type = "CRYPTOCURRENCY"
            elif query_upper.endswith("=F"):
                asset_type = "FUTURE"
                # Try to get friendly name for common futures
                base_symbol = query_upper[:-2]
                if base_symbol in COMMON_FUTURES:
                    name = COMMON_FUTURES[base_symbol]
            elif query_upper.startswith("^"):
                asset_type = "INDEX"
            
            # Check if it looks like a valid ticker (alphanumeric with allowed separators)
            cleaned = query_upper.replace('-', '').replace('=', '').replace('^', '').replace('.', '')
            if cleaned.isalnum():
                return [{
                    "symbol": query_upper,
                    "name": name,
                    "type": asset_type,
                    "exchange": "N/A"
                }]
        
        # Step 3: Try Yahoo Finance API (only if local search didn't find enough)
        loop = asyncio.get_event_loop()
        
        def fetch_results():
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            params = {'q': query, 'quotesCount': 10, 'newsCount': 0}
            
            try:
                response = requests.get(self.search_url, headers=headers, params=params, timeout=3)
                
                # Handle rate limiting
                if response.status_code == 429:
                    print(f"Rate limited by Yahoo Finance for query: {query}")
                    # Return fallback for ticker-like queries
                    if len(query_upper) >= 1 and len(query_upper) <= 10:
                        asset_type = "EQUITY"
                        name = query_upper
                        
                        # Check for common futures first
                        if query_upper in COMMON_FUTURES:
                            asset_type = "FUTURE"
                            name = COMMON_FUTURES[query_upper]
                        elif query_upper.endswith("-USD") or query_upper.endswith("-EUR") or query_upper.endswith("-GBP"):
                            asset_type = "CRYPTOCURRENCY"
                        elif query_upper.endswith("=F"):
                            asset_type = "FUTURE"
                            base_symbol = query_upper[:-2]
                            if base_symbol in COMMON_FUTURES:
                                name = COMMON_FUTURES[base_symbol]
                        elif query_upper.startswith("^"):
                            asset_type = "INDEX"
                        
                        cleaned = query_upper.replace('-', '').replace('=', '').replace('^', '').replace('.', '')
                        if cleaned.isalnum():
                            return [{
                                "symbol": query_upper,
                                "name": name,
                                "type": asset_type,
                                "exchange": "N/A"
                            }]
                    return []
                
                response.raise_for_status()
                data = response.json()
                
                results = []
                for quote in data.get('quotes', []):
                    quote_type = quote.get('quoteType', '')
                    symbol = quote.get('symbol', '')
                    
                    # Override type detection for common futures that Yahoo might misclassify
                    if symbol.upper() in COMMON_FUTURES and quote_type != 'FUTURE':
                        quote_type = 'FUTURE'
                    
                    if quote_type in ['EQUITY', 'ETF', 'CRYPTOCURRENCY', 'FUTURE', 'INDEX']:
                        name = quote.get('longname', quote.get('shortname', quote.get('name', 'No Name')))
                        # Use friendly name for common futures if available
                        if quote_type == 'FUTURE' and symbol.upper() in COMMON_FUTURES:
                            name = COMMON_FUTURES[symbol.upper()]
                        
                        results.append({
                            "symbol": symbol,
                            "name": name,
                            "type": quote_type,
                            "exchange": quote.get('exchange', '')
                        })
                
                # Merge with local results and remove duplicates
                all_results = local_results.copy()
                existing_symbols = {r['symbol'] for r in all_results}
                for result in results:
                    if result['symbol'] not in existing_symbols:
                        all_results.append(result)
                
                # If still no results but query looks like a ticker, add it
                if not all_results and len(query_upper) >= 1 and len(query_upper) <= 10:
                    asset_type = "EQUITY"
                    name = query_upper
                    
                    # Check for common futures first
                    if query_upper in COMMON_FUTURES:
                        asset_type = "FUTURE"
                        name = COMMON_FUTURES[query_upper]
                    elif query_upper.endswith("-USD") or query_upper.endswith("-EUR") or query_upper.endswith("-GBP"):
                        asset_type = "CRYPTOCURRENCY"
                    elif query_upper.endswith("=F"):
                        asset_type = "FUTURE"
                        base_symbol = query_upper[:-2]
                        if base_symbol in COMMON_FUTURES:
                            name = COMMON_FUTURES[base_symbol]
                    elif query_upper.startswith("^"):
                        asset_type = "INDEX"
                    cleaned = query_upper.replace('-', '').replace('=', '').replace('^', '').replace('.', '')
                    if cleaned.isalnum():
                        all_results.append({
                            "symbol": query_upper,
                            "name": name,
                            "type": asset_type,
                            "exchange": "N/A"
                        })
                
                return all_results[:10]  # Limit to 10 results
            except requests.exceptions.Timeout:
                print(f"Search timeout for query: {query}")
                # Return local results if available, otherwise fallback
                if local_results:
                    return local_results
                if len(query_upper) >= 1 and len(query_upper) <= 10:
                    asset_type = "EQUITY"
                    name = query_upper
                    
                    if query_upper in COMMON_FUTURES:
                        asset_type = "FUTURE"
                        name = COMMON_FUTURES[query_upper]
                    elif query_upper.endswith("-USD") or query_upper.endswith("-EUR") or query_upper.endswith("-GBP"):
                        asset_type = "CRYPTOCURRENCY"
                    elif query_upper.endswith("=F"):
                        asset_type = "FUTURE"
                        base_symbol = query_upper[:-2]
                        if base_symbol in COMMON_FUTURES:
                            name = COMMON_FUTURES[base_symbol]
                    elif query_upper.startswith("^"):
                        asset_type = "INDEX"
                    cleaned = query_upper.replace('-', '').replace('=', '').replace('^', '').replace('.', '')
                    if cleaned.isalnum():
                        return [{
                            "symbol": query_upper,
                            "name": name,
                            "type": asset_type,
                            "exchange": "N/A"
                        }]
                return []
            except requests.exceptions.RequestException as e:
                print(f"Search request error for query '{query}': {e}")
                # Return local results if available, otherwise fallback
                if local_results:
                    return local_results
                if len(query_upper) >= 1 and len(query_upper) <= 10:
                    asset_type = "EQUITY"
                    name = query_upper
                    
                    if query_upper in COMMON_FUTURES:
                        asset_type = "FUTURE"
                        name = COMMON_FUTURES[query_upper]
                    elif query_upper.endswith("-USD") or query_upper.endswith("-EUR") or query_upper.endswith("-GBP"):
                        asset_type = "CRYPTOCURRENCY"
                    elif query_upper.endswith("=F"):
                        asset_type = "FUTURE"
                        base_symbol = query_upper[:-2]
                        if base_symbol in COMMON_FUTURES:
                            name = COMMON_FUTURES[base_symbol]
                    elif query_upper.startswith("^"):
                        asset_type = "INDEX"
                    cleaned = query_upper.replace('-', '').replace('=', '').replace('^', '').replace('.', '')
                    if cleaned.isalnum():
                        return [{
                            "symbol": query_upper,
                            "name": name,
                            "type": asset_type,
                            "exchange": "N/A"
                        }]
                return []
            except Exception as e:
                print(f"Search error for query '{query}': {e}")
                # Return local results if available, otherwise fallback
                if local_results:
                    return local_results
                if len(query_upper) >= 1 and len(query_upper) <= 10:
                    asset_type = "EQUITY"
                    name = query_upper
                    
                    if query_upper in COMMON_FUTURES:
                        asset_type = "FUTURE"
                        name = COMMON_FUTURES[query_upper]
                    elif query_upper.endswith("-USD") or query_upper.endswith("-EUR") or query_upper.endswith("-GBP"):
                        asset_type = "CRYPTOCURRENCY"
                    elif query_upper.endswith("=F"):
                        asset_type = "FUTURE"
                        base_symbol = query_upper[:-2]
                        if base_symbol in COMMON_FUTURES:
                            name = COMMON_FUTURES[base_symbol]
                    elif query_upper.startswith("^"):
                        asset_type = "INDEX"
                    cleaned = query_upper.replace('-', '').replace('=', '').replace('^', '').replace('.', '')
                    if cleaned.isalnum():
                        return [{
                            "symbol": query_upper,
                            "name": name,
                            "type": asset_type,
                            "exchange": "N/A"
                        }]
                return []
        
        return await loop.run_in_executor(None, fetch_results)

