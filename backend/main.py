"""
FastAPI Backend for The Sentient Portfolio Tracker
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio
from datetime import datetime
import json
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from services.market_data import MarketDataService
from services.news_service import NewsService
from services.watchlist_service import WatchlistService
from services.search_service import SearchService
from services.ai_service import AIService
from services.earnings_service import EarningsService
from websocket_manager import WebSocketManager

app = FastAPI(title="The Sentient API", version="1.0.0")

# CORS middleware for Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
market_data_service = MarketDataService()
news_service = NewsService()
watchlist_service = WatchlistService()
search_service = SearchService()
ai_service = AIService()
earnings_service = EarningsService()
ws_manager = WebSocketManager()

# Pydantic models
class WatchlistItem(BaseModel):
    symbol: str
    name: str

class NewsItem(BaseModel):
    source: str
    ticker: str
    title: str
    link: str
    publisher: Optional[str] = None
    timestamp: datetime
    text: str
    trading_signal: Optional[Dict[str, Any]] = None

class ChartRequest(BaseModel):
    ticker: str
    timeframe: str
    chart_type: str = "candle"

class SearchRequest(BaseModel):
    query: str

# API Routes
@app.get("/")
async def root():
    return {"message": "The Sentient API", "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Market Data Endpoints
@app.post("/api/chart")
async def get_chart(request: ChartRequest):
    """Get chart data for a ticker"""
    try:
        data = await market_data_service.get_chart_data(
            request.ticker,
            request.timeframe,
            request.chart_type
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quote/{ticker}")
async def get_quote(ticker: str):
    """Get current quote for a ticker"""
    try:
        quote = await market_data_service.get_quote(ticker)
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search Endpoints
@app.post("/api/search")
async def search(request: SearchRequest):
    """Search for assets"""
    try:
        results = await search_service.search(request.query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Watchlist Endpoints
@app.get("/api/watchlist")
async def get_watchlist():
    """Get current watchlist"""
    return {"watchlist": watchlist_service.get_watchlist()}

@app.post("/api/watchlist")
async def add_to_watchlist(item: WatchlistItem):
    """Add item to watchlist"""
    watchlist_service.add_item(item.symbol, item.name)
    return {"message": "Item added", "watchlist": watchlist_service.get_watchlist()}

@app.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    """Remove item from watchlist"""
    watchlist_service.remove_item(symbol)
    return {"message": "Item removed", "watchlist": watchlist_service.get_watchlist()}

# News Endpoints
@app.get("/api/news")
async def get_news(tickers: Optional[str] = None, limit: int = 50, publishers: Optional[str] = None):
    """Get news feed with optional publisher filtering"""
    try:
        ticker_list = tickers.split(",") if tickers else None
        publisher_list = publishers.split(",") if publishers else None
        if publisher_list:
            publisher_list = [p.strip() for p in publisher_list if p.strip()]
        news_items = await news_service.get_news(ticker_list, limit, publisher_list)
        return {"news": news_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/{ticker}")
async def get_ticker_news(ticker: str, limit: int = 20, publishers: Optional[str] = None):
    """Get news for specific ticker with optional publisher filtering"""
    try:
        publisher_list = publishers.split(",") if publishers else None
        if publisher_list:
            publisher_list = [p.strip() for p in publisher_list if p.strip()]
        news_items = await news_service.get_news([ticker], limit, publisher_list)
        return {"news": news_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/publishers")
async def get_news_publishers():
    """Get list of all available news publishers"""
    try:
        # Get a sample of news to extract publishers
        sample_news = await news_service.get_news(None, 200)
        publishers = set()
        for item in sample_news:
            if item.get('publisher'):
                publishers.add(item['publisher'])
        return {"publishers": sorted(list(publishers))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI Analysis Endpoints
@app.post("/api/analyze")
async def analyze_news(news_item: Dict[str, Any]):
    """Analyze news item with AI"""
    try:
        analysis = await ai_service.analyze_news(news_item)
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Earnings Endpoints
@app.get("/api/earnings")
async def get_earnings(start_date: Optional[str] = None, weeks: int = 1, offset: int = 0):
    """Get earnings calendar"""
    try:
        earnings = await earnings_service.get_earnings_calendar(start_date, weeks, offset)
        return {"earnings": earnings, "offset": offset, "weeks": weeks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/earnings/{ticker}")
async def get_ticker_earnings(ticker: str):
    """Get earnings for a specific ticker"""
    try:
        earnings = await earnings_service.get_ticker_earnings(ticker)
        if earnings:
            return {"earnings": earnings}
        else:
            raise HTTPException(status_code=404, detail="Earnings not found for this ticker")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time news and updates"""
    await ws_manager.connect(websocket)
    try:
        # Start background tasks
        asyncio.create_task(news_service.start_news_monitor(ws_manager))
        
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
            message = json.loads(data)
            if message.get("type") == "subscribe_news":
                await ws_manager.send_personal_message(
                    {"type": "subscribed", "tickers": message.get("tickers")},
                    websocket
                )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot reload for development
        log_level="info"
    )

