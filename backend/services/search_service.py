"""
Search Service - Handles asset search
"""
import requests
import asyncio
from typing import List, Dict, Any
from services.ticker_database import search_local

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
        if len(query_upper) >= 1 and len(query_upper) <= 5 and query_upper.replace('.', '').replace('=', '').replace('^', '').isalnum():
            return [{
                "symbol": query_upper,
                "name": f"{query_upper}",
                "type": "EQUITY",
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
                    if len(query_upper) >= 1 and len(query_upper) <= 5:
                        return [{
                            "symbol": query_upper,
                            "name": f"{query_upper}",
                            "type": "EQUITY",
                            "exchange": "N/A"
                        }]
                    return []
                
                response.raise_for_status()
                data = response.json()
                
                results = []
                for quote in data.get('quotes', []):
                    quote_type = quote.get('quoteType', '')
                    if quote_type in ['EQUITY', 'ETF', 'CRYPTOCURRENCY', 'FUTURE', 'INDEX']:
                        results.append({
                            "symbol": quote.get('symbol', ''),
                            "name": quote.get('longname', quote.get('shortname', quote.get('name', 'No Name'))),
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
                if not all_results and len(query_upper) >= 1 and len(query_upper) <= 5:
                    all_results.append({
                        "symbol": query_upper,
                        "name": f"{query_upper}",
                        "type": "EQUITY",
                        "exchange": "N/A"
                    })
                
                return all_results[:10]  # Limit to 10 results
            except requests.exceptions.Timeout:
                print(f"Search timeout for query: {query}")
                # Return local results if available, otherwise fallback
                if local_results:
                    return local_results
                if len(query_upper) >= 1 and len(query_upper) <= 5:
                    return [{
                        "symbol": query_upper,
                        "name": f"{query_upper}",
                        "type": "EQUITY",
                        "exchange": "N/A"
                    }]
                return []
            except requests.exceptions.RequestException as e:
                print(f"Search request error for query '{query}': {e}")
                # Return local results if available, otherwise fallback
                if local_results:
                    return local_results
                if len(query_upper) >= 1 and len(query_upper) <= 5:
                    return [{
                        "symbol": query_upper,
                        "name": f"{query_upper}",
                        "type": "EQUITY",
                        "exchange": "N/A"
                    }]
                return []
            except Exception as e:
                print(f"Search error for query '{query}': {e}")
                # Return local results if available, otherwise fallback
                if local_results:
                    return local_results
                if len(query_upper) >= 1 and len(query_upper) <= 5:
                    return [{
                        "symbol": query_upper,
                        "name": f"{query_upper}",
                        "type": "EQUITY",
                        "exchange": "N/A"
                    }]
                return []
        
        return await loop.run_in_executor(None, fetch_results)

