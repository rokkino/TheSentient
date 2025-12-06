"""
News Service - Handles news fetching and monitoring
"""
import sys
import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import yfinance as yf

class NewsService:
    def __init__(self):
        self.seen_links = set()
        self.is_monitoring = False
    
    async def get_news(self, tickers: Optional[List[str]] = None, limit: int = 50, allowed_publishers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get news items with optional publisher filtering"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        def fetch_news_sync():
            target_tickers = tickers if tickers else ['GC=F', 'CL=F', '^GSPC', 'NVDA', 'MSFT', 'GOOGL', 'AAPL', 'TSLA', 'AMD', 'INTC']
            print(f"Fetching news for tickers: {target_tickers}")
            all_news_items = []
            
            for ticker in target_tickers:
                try:
                    print(f"Fetching news for {ticker}...")
                    tk = yf.Ticker(ticker)
                    news_data = tk.news
                    
                    if not news_data:
                        print(f"No news data returned for {ticker}")
                        continue
                    
                    print(f"Found {len(news_data)} news items for {ticker}")
                    
                    for item in news_data:
                        # Skip items without title
                        title = item.get('title', '').strip()
                        if not title:
                            continue
                        
                        link = item.get('link', '').strip()
                        
                        # Extract publisher
                        publisher = item.get('publisher', 'Yahoo Finance')
                        if not publisher:
                            publisher = 'Yahoo Finance'
                        
                        # Filter by publisher if specified
                        if allowed_publishers and len(allowed_publishers) > 0:
                            if publisher not in allowed_publishers:
                                continue
                        
                        # Convert timestamp
                        ts = item.get('providerPublishTime', 0)
                        if not ts:
                            # Try to parse pubDate string if available
                            pub_date = item.get('pubDate', '')
                            if pub_date:
                                # You might need specific parsing here depending on format
                                ts = datetime.now().timestamp() # Fallback for now
                            else:
                                ts = datetime.now().timestamp()
                        
                        try:
                            timestamp = datetime.fromtimestamp(ts).isoformat()
                        except (ValueError, OSError):
                            timestamp = datetime.now().isoformat()
                        
                        # Extract thumbnail URL
                        thumbnail_url = ''
                        if item.get('thumbnail'):
                            if isinstance(item['thumbnail'], dict):
                                resolutions = item['thumbnail'].get('resolutions', [])
                                if resolutions and len(resolutions) > 0:
                                    thumbnail_url = resolutions[0].get('url', '')
                            elif isinstance(item['thumbnail'], str):
                                thumbnail_url = item['thumbnail']
                        
                        news_dict = {
                            "source": "Yahoo Finance",
                            "ticker": ticker,
                            "title": title,
                            "link": link or f"https://finance.yahoo.com/quote/{ticker}",
                            "publisher": publisher,
                            "timestamp": timestamp,
                            "text": title, # Usually yfinance news doesn't provide full text
                            "thumbnail": thumbnail_url,
                            "trading_signal": None # AI analysis would go here
                        }
                        
                        # Simple duplicate check based on title
                        if not any(n['title'] == news_dict['title'] for n in all_news_items):
                            all_news_items.append(news_dict)
                            
                except Exception as e:
                    print(f"Error fetching news for {ticker}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Sort by timestamp descending
            all_news_items.sort(key=lambda x: x['timestamp'], reverse=True)
            result = all_news_items[:limit]
            print(f"Returning {len(result)} news items (limit: {limit})")
            return result
        
        return await loop.run_in_executor(None, fetch_news_sync)
    
    async def get_ticker_news(self, ticker: str, limit: int = 20, allowed_publishers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get news for a specific ticker"""
        return await self.get_news([ticker], limit, allowed_publishers)
        
    async def get_available_publishers(self) -> List[str]:
        """Get list of available publishers from recent news"""
        # Fetch news from a broad set of tickers to get publishers
        tickers = ['GC=F', 'CL=F', '^GSPC', 'NVDA', 'MSFT', 'GOOGL', 'AAPL', 'TSLA']
        news_items = await self.get_news(tickers, limit=100)
        
        publishers = set()
        for item in news_items:
            if item.get('publisher'):
                publishers.add(item.get('publisher'))
        
        return sorted(list(publishers))
    
    async def start_news_monitor(self, ws_manager):
        """Start monitoring news and sending updates via WebSocket"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        default_tickers = ['GC=F', 'CL=F', '^GSPC', 'NVDA', 'MSFT', 'GOOGL']
        
        while self.is_monitoring:
            try:
                # Use self.get_news directly
                current_news = await self.get_news(default_tickers, limit=20)
                
                new_items = []
                for item in current_news:
                    link = item.get('link')
                    if link and link not in self.seen_links:
                        new_items.append(item)
                        self.seen_links.add(link)
                
                if new_items:
                    # Convert and send via WebSocket
                    await ws_manager.broadcast({
                        "type": "new_news",
                        "data": new_items
                    })
                
                # Wait before next check (e.g., 60 seconds)
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"Error in news monitor: {e}")
                await asyncio.sleep(60)
