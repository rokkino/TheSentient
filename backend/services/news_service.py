"""
News Service - Handles news fetching and monitoring
"""
import sys
import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import yfinance as yf
import feedparser
from sqlalchemy.orm import Session
import requests
from bs4 import BeautifulSoup
import re

class NewsService:
    def __init__(self):
        self.seen_links = set()
        self.is_monitoring = False
        self.rss_feeds = [
            "https://finance.yahoo.com/news/rssindex",
            "http://feeds.marketwatch.com/marketwatch/topstories/",
            "https://www.investing.com/rss/news.rss",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html"
        ]
        
        # Setup memory cache directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        self.cache_dir = os.path.join(backend_dir, 'memory', 'news')
        
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
                print(f"[NEWS] Created memory directory: {self.cache_dir}")
            except Exception as e:
                print(f"[NEWS] Warning: Could not create memory directory {self.cache_dir}: {e}")
                
        # In-memory cache for fast access
        self.memory_cache = []
        self._load_cache()

    def _load_cache(self):
        """Load news from individual JSON files in memory directory"""
        try:
            if not os.path.exists(self.cache_dir):
                return

            loaded_items = []
            count = 0
            
            # Iterate over all files in the cache directory
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            import json
                            item = json.load(f)
                            
                            # Basic validation
                            if 'link' in item and 'timestamp' in item:
                                loaded_items.append(item)
                                count += 1
                    except Exception as e:
                        print(f"[NEWS] Error loading cache file {filename}: {e}")
            
            # Sort by timestamp descending
            loaded_items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            self.memory_cache = loaded_items
            print(f"[NEWS] Loaded {count} news items from memory cache")
        except Exception as e:
            print(f"[NEWS] Error loading cache: {e}")
            self.memory_cache = []

    def _save_news_to_memory(self, news_items: List[Dict[str, Any]]):
        """Save news items to individual JSON files"""
        import hashlib
        import json
        
        count = 0
        for item in news_items:
            try:
                link = item.get('link', '')
                if not link:
                    continue
                    
                # Create a unique filename based on the link hash
                # Using MD5 of link is a good way to get a unique, safe filename
                link_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
                filename = f"news_{link_hash}.json"
                file_path = os.path.join(self.cache_dir, filename)
                
                # Only save if it doesn't exist (immutable news items)
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(item, f, indent=2, ensure_ascii=False)
                    count += 1
                    
                    # Also update in-memory cache
                    self.memory_cache.append(item)
            except Exception as e:
                print(f"[NEWS] Error saving news item to memory: {e}")
        
        if count > 0:
            print(f"[NEWS] Saved {count} new news items to memory cache")
            # Re-sort memory cache
            self.memory_cache.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    async def get_news(self, tickers: Optional[List[str]] = None, limit: int = 50, allowed_publishers: Optional[List[str]] = None, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Get news items with optional publisher filtering and caching"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 1. Fetch from Memory Cache first (DB is secondary/legacy now)
        cached_news = []
        
        # Filter memory cache based on request
        if self.memory_cache:
            filtered_cache = self.memory_cache
            
            # Filter by tickers if provided
            if tickers:
                filtered_cache = [n for n in filtered_cache if n.get('ticker') in tickers]
                
            # Filter by publishers if provided
            if allowed_publishers:
                filtered_cache = [n for n in filtered_cache if n.get('publisher') in allowed_publishers]
                
            cached_news = filtered_cache[:limit]
            print(f"Loaded {len(cached_news)} news items from memory cache")
            
        # Fallback to DB if provided and memory cache empty (migration path)
        if not cached_news and db:
            try:
                cached_news = await self.get_news_from_db(db, tickers, limit, allowed_publishers)
                print(f"Loaded {len(cached_news)} news items from DB cache")
            except Exception as e:
                print(f"Error reading from DB cache: {e}")

        # 2. Fetch fresh news
        def fetch_news_sync():
            # Only fetch news for tickers explicitly provided
            # No automatic/default tickers - must be explicitly requested
            if not tickers:
                # Return empty list instead of fetching default tickers
                print("No tickers provided, returning empty news list")
                return []
            
            target_tickers = tickers
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
                    
                    
                    for item in news_data:
                        try:
                            # Handle new yfinance structure where data is nested in 'content'
                            content = item.get('content')
                            if content and isinstance(content, dict):
                                title = content.get('title', '').strip()
                                
                                link_obj = content.get('clickThroughUrl') or content.get('canonicalUrl')
                                link = link_obj.get('url', '') if link_obj else ''
                                
                                provider = content.get('provider') or {}
                                publisher = provider.get('displayName', 'Yahoo Finance')
                                
                                pub_date_str = content.get('pubDate', '')
                                try:
                                    if pub_date_str:
                                        # Handle ISO format with Z
                                        if pub_date_str.endswith('Z'):
                                            pub_date_str = pub_date_str[:-1]
                                        dt = datetime.fromisoformat(pub_date_str)
                                        ts = dt.timestamp()
                                        timestamp = dt.isoformat()
                                    else:
                                        ts = datetime.now().timestamp()
                                        timestamp = datetime.now().isoformat()
                                except Exception:
                                    ts = datetime.now().timestamp()
                                    timestamp = datetime.now().isoformat()
                                
                                thumbnail_obj = content.get('thumbnail') or {}
                                thumbnail_url = thumbnail_obj.get('originalUrl', '')
                                if not thumbnail_url and thumbnail_obj.get('resolutions'):
                                    thumbnail_url = thumbnail_obj['resolutions'][0].get('url', '')
                                
                                summary = content.get('summary', '')
                            else:
                                # Fallback to old structure
                                title = item.get('title', '').strip()
                                link = item.get('link', '').strip()
                                publisher = item.get('publisher', 'Yahoo Finance')
                                summary = ''
                                
                                # Convert timestamp
                                ts = item.get('providerPublishTime', 0)
                                if not ts:
                                    # Try to parse pubDate string if available
                                    pub_date = item.get('pubDate', '')
                                    if pub_date:
                                        ts = datetime.now().timestamp() # Fallback for now if parsing fails
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

                            if not title:
                                continue
                            
                            # Clean up publisher
                            if not publisher:
                                publisher = 'Yahoo Finance'
                            
                            # Filter by publisher if specified
                            if allowed_publishers and len(allowed_publishers) > 0:
                                if publisher not in allowed_publishers:
                                    continue
                            
                            news_dict = {
                                "source": "Yahoo Finance",
                                "ticker": ticker,
                                "title": title,
                                "link": link or f"https://finance.yahoo.com/quote/{ticker}",
                                "publisher": publisher,
                                "timestamp": timestamp,
                                "text": summary if summary else title, 
                                "thumbnail": thumbnail_url,
                                "trading_signal": None
                            }
                            
                            # Simple duplicate check based on title
                            if not any(n['title'] == news_dict['title'] for n in all_news_items):
                                all_news_items.append(news_dict)
                        except Exception as e:
                            print(f"Error processing item for {ticker}: {e}")
                            continue

                
                except Exception as e:
                    print(f"Error processing news for {ticker}: {e}")
                    continue
            
            return all_news_items
        
        fresh_news = await loop.run_in_executor(None, fetch_news_sync)
        
        # 3. Save fresh news to Memory Cache and DB
        if fresh_news:
            try:
                # Save to file-based memory cache
                self._save_news_to_memory(fresh_news)
                
                # Also save to DB if available (legacy support)
                if db:
                    await self.save_news_to_db(db, fresh_news)
                    await self.cleanup_old_news(db)
            except Exception as e:
                print(f"Error saving to cache: {e}")
        
        # 4. Merge and sort
        # Create a dict by link to merge (fresh news overwrites cache if same link)
        merged_news = {item['link']: item for item in cached_news}
        for item in fresh_news:
            merged_news[item['link']] = item
            
        final_list = list(merged_news.values())
        
        # Sort by timestamp descending
        final_list.sort(key=lambda x: x['timestamp'], reverse=True)
        result = final_list[:limit]
        print(f"Returning {len(result)} news items (limit: {limit})")
        return result
    
    async def get_news_from_db(self, db: Session, tickers: Optional[List[str]], limit: int, allowed_publishers: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Fetch news from database"""
        from models.news import News
        from sqlalchemy import desc
        
        query = db.query(News)
        
        if tickers:
            query = query.filter(News.ticker.in_(tickers))
            
        if allowed_publishers:
            query = query.filter(News.publisher.in_(allowed_publishers))
            
        # Get more than limit to allow for some post-filtering if needed, but limit is good
        news_objs = query.order_by(desc(News.timestamp)).limit(limit).all()
        
        return [{
            "source": "Yahoo Finance", # Hardcoded as we mostly use YF
            "ticker": n.ticker,
            "title": n.title,
            "link": n.link,
            "publisher": n.publisher,
            "timestamp": n.timestamp.isoformat(),
            "text": n.content,
            "thumbnail": n.thumbnail_url,
            "trading_signal": None
        } for n in news_objs]

    async def save_news_to_db(self, db: Session, news_items: List[Dict[str, Any]]):
        """Save new news items to database"""
        from models.news import News
        
        count = 0
        for item in news_items:
            try:
                # Check if exists
                exists = db.query(News).filter(News.link == item['link']).first()
                if not exists:
                    # Parse timestamp
                    ts_str = item['timestamp']
                    try:
                        ts = datetime.fromisoformat(ts_str)
                    except:
                        ts = datetime.utcnow()
                        
                    new_news = News(
                        ticker=item['ticker'],
                        title=item['title'],
                        link=item['link'],
                        publisher=item['publisher'],
                        timestamp=ts,
                        content=item['text'],
                        thumbnail_url=item['thumbnail']
                    )
                    db.add(new_news)
                    count += 1
            except Exception as e:
                print(f"Error saving news item: {e}")
                continue
        
        if count > 0:
            db.commit()
            print(f"Saved {count} new news items to database")

    async def cleanup_old_news(self, db: Session, days: int = 7):
        """Remove news older than N days"""
        from models.news import News
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        try:
            deleted = db.query(News).filter(News.timestamp < cutoff).delete()
            db.commit()
            if deleted > 0:
                print(f"Cleaned up {deleted} old news items (older than {days} days)")
        except Exception as e:
            print(f"Error cleaning up old news: {e}")
            db.rollback()

    async def get_ticker_news(self, ticker: str, limit: int = 20, allowed_publishers: Optional[List[str]] = None, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Get news for a specific ticker"""
        return await self.get_news([ticker], limit, allowed_publishers, db)
        
    async def get_available_publishers(self) -> List[str]:
        """Get list of available publishers from recent news"""
        # No longer fetching default tickers - return empty list or hardcoded common publishers
        # Publishers will be discovered from actual news requests when tickers are provided
        common_publishers = [
            'Yahoo Finance', 'MarketWatch', 'CNBC', 'Bloomberg', 'Reuters',
            'Wall Street Journal', 'Financial Times', 'Investing.com', 'Seeking Alpha',
            'Benzinga', 'The Motley Fool', 'Zacks', 'Barron\'s', 'Forbes'
        ]
        return sorted(common_publishers)
    
    async def start_news_monitor(self, ws_manager, tickers: Optional[List[str]] = None):
        """Start monitoring news and sending updates via WebSocket"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        # Only monitor tickers explicitly provided - no default tickers
        # If no tickers provided, don't monitor anything
        if not tickers:
            print("[NEWS] No tickers provided for monitoring, stopping monitor")
            self.is_monitoring = False
            return
        
        print(f"[NEWS] Starting news monitor for tickers: {tickers}")
        
        while self.is_monitoring:
            try:
                # Use self.get_news with provided tickers only
                # Note: Monitor doesn't use DB cache to avoid complexity with session management in loop
                # It just fetches fresh and broadcasts
                current_news = await self.get_news(tickers, limit=20)
                
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


    async def fetch_article_content(self, url: str) -> str:
        """Fetch and parse full article content from URL"""
        try:
            # Basic headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Run blocking request in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers, timeout=10))
            
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for script in soup(["script", "style", "nav", "header", "footer", "iframe", "noscript"]):
                script.decompose()
            
            # Try to find the main content
            # Strategy 1: Known selectors
            article_text = ""
            
            # Common selectors for article bodies
            selectors = [
                'div.caas-body', # Yahoo Finance
                'div.article-body',
                'div.story-body',
                'article',
                'div.content',
                'div.post-content',
                'div.entry-content',
                'section[itemprop="articleBody"]'
            ]
            
            content_element = None
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    # Check if it has substantial content
                    text = element.get_text().strip()
                    if len(text) > 500:
                        content_element = element
                        print(f"Found content using selector: {selector}")
                        break
            
            # Strategy 2: Heuristic - Find div/article with most p tags or text
            if not content_element:
                print("Selectors failed or returned short text, trying heuristic...")
                candidates = soup.find_all(['div', 'article', 'section'])
                best_candidate = None
                max_score = 0
                
                for candidate in candidates:
                    # Score based on length of text in p tags
                    paragraphs = candidate.find_all('p', recursive=False) # Direct children preferred
                    if not paragraphs:
                        paragraphs = candidate.find_all('p') # Or all descendants
                        
                    score = sum(len(p.get_text().strip()) for p in paragraphs)
                    
                    # Penalize if too many links (nav menus etc)
                    links = candidate.find_all('a')
                    link_text_length = sum(len(a.get_text().strip()) for a in links)
                    if score > 0 and link_text_length / score > 0.5:
                        score = 0
                        
                    if score > max_score:
                        max_score = score
                        best_candidate = candidate
                
                if best_candidate and max_score > 200:
                    content_element = best_candidate
                    print(f"Found content using heuristic (score: {max_score})")

            if content_element:
                # Get text from paragraphs
                paragraphs = content_element.find_all('p')
                article_text = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            else:
                # Fallback: get all text from body
                print("Heuristic failed, falling back to body text")
                body = soup.find('body')
                if body:
                    # Get text but try to preserve some structure
                    text = body.get_text(separator='\n\n')
                    # Clean up excessive newlines
                    article_text = re.sub(r'\n\s*\n', '\n\n', text).strip()
            
            # Clean up text
            if len(article_text) < 100: # If too short, it's probably failed
                print(f"Fetched text too short: {len(article_text)} chars")
                return ""
                
            return article_text
            
        except Exception as e:
            print(f"Error fetching article content: {e}")
            return ""
