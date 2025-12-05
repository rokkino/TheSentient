"""
Search Service - Handles asset search
"""
import requests
import asyncio
from typing import List, Dict, Any

class SearchService:
    def __init__(self):
        self.search_url = "https://query1.finance.yahoo.com/v1/finance/search"
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for assets"""
        loop = asyncio.get_event_loop()
        
        def fetch_results():
            if not query:
                return []
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            params = {'q': query}
            
            try:
                response = requests.get(self.search_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for quote in data.get('quotes', []):
                    quote_type = quote.get('quoteType', '')
                    if quote_type in ['EQUITY', 'ETF', 'CRYPTOCURRENCY', 'FUTURE']:
                        results.append({
                            "symbol": quote.get('symbol', ''),
                            "name": quote.get('longname', quote.get('shortname', 'No Name')),
                            "type": quote_type,
                            "exchange": quote.get('exchange', '')
                        })
                
                return results
            except Exception as e:
                print(f"Search error: {e}")
                return []
        
        return await loop.run_in_executor(None, fetch_results)

