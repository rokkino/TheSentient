"""
News Service - Handles news fetching and monitoring

This service can be extended to support multiple news sources:
- Yahoo Finance (current implementation)
- Twitter/X API (future)
- Financial news APIs (Bloomberg, Reuters, etc.)
- RSS feeds
- Custom news aggregators
"""
import sys
import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import news
except ImportError:
    news = None

class NewsService:
    def __init__(self):
        self.seen_links = set()
        self.is_monitoring = False
    
    async def get_news(self, tickers: Optional[List[str]] = None, limit: int = 50, allowed_publishers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get news items with optional publisher filtering"""
        if not news:
            return []
        
        loop = asyncio.get_event_loop()
        
        def fetch_news():
            if tickers:
                all_news = news.fetch_all_news(tickers)
            else:
                # Default tickers
                default_tickers = ['GC=F', 'CL=F', '^GSPC', 'NVDA', 'MSFT', 'GOOGL']
                all_news = news.fetch_all_news(default_tickers)
            
            # Convert to dict format and filter by publisher if specified
            news_list = []
            for item in all_news:
                publisher = item.get('publisher', '')
                
                # Filter by publisher if allowed_publishers is specified
                if allowed_publishers and len(allowed_publishers) > 0:
                    # If publisher is empty or not in allowed list, skip
                    if not publisher or publisher not in allowed_publishers:
                        continue
                
                news_dict = {
                    "source": item.get('source', 'Yahoo Finance'),
                    "ticker": item.get('ticker', ''),
                    "title": item.get('title', ''),
                    "link": item.get('link', ''),
                    "publisher": publisher,
                    "timestamp": item.get('timestamp').isoformat() if item.get('timestamp') else datetime.now().isoformat(),
                    "text": item.get('text', item.get('title', '')),
                    "trading_signal": item.get('trading_signal')
                }
                news_list.append(news_dict)
            
            # Apply limit after filtering
            return news_list[:limit]
        
        return await loop.run_in_executor(None, fetch_news)
    
    async def get_ticker_news(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get news for a specific ticker"""
        return await self.get_news([ticker], limit)
    
    async def start_news_monitor(self, ws_manager):
        """Start monitoring news and sending updates via WebSocket"""
        if not news or self.is_monitoring:
            return
        
        self.is_monitoring = True
        default_tickers = ['GC=F', 'CL=F', '^GSPC', 'NVDA', 'MSFT', 'GOOGL']
        
        while self.is_monitoring:
            try:
                all_news = news.fetch_all_news(default_tickers)
                
                new_items = []
                for item in all_news:
                    link = item.get('link')
                    if link and link not in self.seen_links:
                        new_items.append(item)
                        self.seen_links.add(link)
                
                if new_items:
                    # Convert and send via WebSocket
                    for item in new_items:
                        news_dict = {
                            "source": item.get('source', 'Yahoo Finance'),
                            "ticker": item.get('ticker', ''),
                            "title": item.get('title', ''),
                            "link": item.get('link', ''),
                            "publisher": item.get('publisher', ''),
                            "timestamp": item.get('timestamp').isoformat() if item.get('timestamp') else datetime.now().isoformat(),
                            "text": item.get('text', item.get('title', '')),
                            "trading_signal": item.get('trading_signal')
                        }
                        await ws_manager.broadcast({
                            "type": "new_news",
                            "data": news_dict
                        })
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
            except Exception as e:
                print(f"Error in news monitor: {e}")
                await asyncio.sleep(60)

