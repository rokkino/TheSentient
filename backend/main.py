"""
FastAPI Backend for The Sentient Portfolio Tracker
"""
from __future__ import annotations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio
from datetime import datetime, timezone
import json
import sys

import os
import shutil
import uuid
from pathlib import Path

# Ensure imports work no matter the working directory:
# - prefer backend/ on sys.path so `services.*` and `models.*` resolve to our local code
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Helpful for debugging "wrong server process" issues
SERVER_BUILD = f"backend-main.py@{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"

from services.market_data import MarketDataService
from services.news_service import NewsService
from services.watchlist_service import WatchlistService
from services.search_service import SearchService
from services.ai_service import AIService
from services.earnings_service import EarningsService
from services.auth_service import create_user, authenticate_user, create_access_token, get_user_by_id, verify_token, get_user_by_username, get_user_by_email
from services.chat_service import chat_service
from services.strategy_service import strategy_service
# AlpacaService is optional - only import if needed
try:
    from services.alpaca_service import AlpacaService
    ALPACA_AVAILABLE = True
except Exception:
    ALPACA_AVAILABLE = False
    AlpacaService = None
from services.bot_service import bot_service
from services.llama_service import llama_service
from services.gemini_service import GeminiService
from websocket_manager import WebSocketManager
from models.user import init_db, get_db, User, SessionLocal
from models.bot import Bot
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

app = FastAPI(title="The Sentient API", version="1.0.0")

# Add build header to all responses (helps confirm you're hitting the right backend process)
@app.middleware("http")
async def _add_build_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-TheSentient-Build"] = SERVER_BUILD
    return response

@app.get("/api/debug/build")
async def debug_build():
    """Return backend build marker (debugging)."""
    return {"build": SERVER_BUILD}

# Initialize database (non-blocking)
try:
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")
    print("The app will continue, but database operations may fail")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user_id = payload.get("sub")
    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# CORS middleware for Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads/profile_pictures")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Initialize services
market_data_service = MarketDataService()
news_service = NewsService()
watchlist_service = WatchlistService()
search_service = SearchService()
ai_service = AIService()
earnings_service = EarningsService()
# Initialize Alpaca service only if available (optional - we use IG Markets now)
alpaca_service = AlpacaService() if ALPACA_AVAILABLE and AlpacaService else None
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

class ChartAnalysisRequest(BaseModel):
    ticker: str
    timeframe: str
    query: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    use_local_llama: bool = False
    gemini_api_key: Optional[str] = None
    ai_provider: Optional[str] = "gemini"
    gemini_pro_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    profile_picture_url: Optional[str] = None
    use_local_llama: Optional[bool] = None
    gemini_api_key: Optional[str] = None
    ai_provider: Optional[str] = None
    gemini_pro_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

class TabsUpdate(BaseModel):
    tabs: List[Dict[str, Any]]

class ChatMessage(BaseModel):
    message: str
    type: str = "text"  # "text" or "image"
    image_data: Optional[str] = None  # Base64 encoded image
    recipient_id: Optional[int] = None
    invite_llama: bool = False
    invite_gemini: bool = False
    is_search: bool = False
    
class ChatHistoryClear(BaseModel):
    recipient_id: Optional[int] = None

class AlpacaOrderRequest(BaseModel):
    symbol: str
    qty: float
    side: str  # "buy" or "sell"
    order_type: str = "market"  # "market", "limit", "stop", "stop_limit"
    time_in_force: str = "day"  # "day", "gtc", "opg", "cls", "ioc", "fok"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

class BotCreate(BaseModel):
    name: str
    bot_type: str
    description: Optional[str] = None

class BotConfig(BaseModel):
    # IG Markets Configuration (required for Earnings Report Genius bot)
    ig_username: Optional[str] = None
    ig_password: Optional[str] = None
    ig_api_key: Optional[str] = None
    ig_acc_type: Optional[str] = None  # "DEMO" or "LIVE"
    # AI Analysis (optional but recommended)
    gemini_api_key: Optional[str] = None
    # Legacy Alpaca (deprecated, kept for backward compatibility)
    alpaca_api_key: Optional[str] = None
    alpaca_api_secret: Optional[str] = None

class BotImport(BaseModel):
    name: str
    bot_type: str
    description: Optional[str] = None
    config: dict  # The bot configuration (including API credentials if provided in export)

class AskLlamaRequest(BaseModel):
    symbol: Optional[str] = None
    company: Optional[str] = None
    date: Optional[str] = None
    question: Optional[str] = None
    provider: Optional[str] = "local"


class AskLlamaNewsRequest(BaseModel):
    title: str
    text: Optional[str] = None
    ticker: Optional[str] = None
    publisher: Optional[str] = None
    date: Optional[str] = None
    question: str

class BotChatRequest(BaseModel):
    prompt: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None

class NewsContentRequest(BaseModel):
    url: str

class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    definition: Dict[str, Any]

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None

class StrategyGenerateRequest(BaseModel):
    prompt: str

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
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chart/analyze")
async def analyze_chart(request: ChartAnalysisRequest):
    """Analyze chart request using AI and return indicator data"""
    try:
        # 1. Parse request with Llama
        indicator_configs = llama_service.parse_chart_request(request.query)
        
        # 2. Calculate indicator data
        results = await market_data_service.calculate_indicator(
            request.ticker,
            request.timeframe,
            indicator_configs
        )
        
        return {"data": results}
    except Exception as e:
        print(f"Error analyzing chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quote/{ticker}")
async def get_quote(ticker: str, timeframe: str = "1d"):
    """Get current quote for a ticker with change calculated based on timeframe"""
    try:
        quote = await market_data_service.get_quote(ticker, timeframe)
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{ticker}/financials")
async def get_stock_financials(ticker: str):
    """Get financial data (Revenue, Earnings, EPS History) for a ticker"""
    try:
        data = await market_data_service.get_financials(ticker)
        return data
    except Exception as e:
        print(f"Error getting financials for {ticker}: {e}")
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
    print(f"API: Adding to watchlist: {item.symbol}, {item.name}")
    try:
        watchlist_service.add_item(item.symbol, item.name)
        print("API: Item added successfully")
        return {"message": "Item added", "watchlist": watchlist_service.get_watchlist()}
    except Exception as e:
        print(f"API: Error adding item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    """Remove item from watchlist"""
    watchlist_service.remove_item(symbol)
    return {"message": "Item removed", "watchlist": watchlist_service.get_watchlist()}

# News Endpoints
@app.get("/api/news")
async def get_news(tickers: Optional[str] = None, limit: int = 50, publishers: Optional[str] = None, db: Session = Depends(get_db)):
    """Get news feed with optional publisher filtering"""
    try:
        print(f"News API called: tickers={tickers}, limit={limit}, publishers={publishers}")
        ticker_list = tickers.split(",") if tickers else None
        if ticker_list:
            ticker_list = [t.strip() for t in ticker_list if t.strip()]
        publisher_list = publishers.split(",") if publishers else None
        if publisher_list:
            publisher_list = [p.strip() for p in publisher_list if p.strip()]
        print(f"Processing news request: ticker_list={ticker_list}, limit={limit}, publisher_list={publisher_list}")
        news_items = await news_service.get_news(ticker_list, limit, publisher_list, db)
        print(f"Returning {len(news_items)} news items")
        return {"news": news_items}
    except Exception as e:
        import traceback
        print(f"Error in get_news endpoint: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/{ticker}")
async def get_ticker_news(ticker: str, limit: int = 20, publishers: Optional[str] = None, db: Session = Depends(get_db)):
    """Get news for specific ticker with optional publisher filtering"""
    try:
        publisher_list = publishers.split(",") if publishers else None
        if publisher_list:
            publisher_list = [p.strip() for p in publisher_list if p.strip()]
        news_items = await news_service.get_news([ticker], limit, publisher_list, db)
        return {"news": news_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/publishers")
async def get_news_publishers():
    """Get list of all available news publishers"""
    try:
        # Use the service method which returns a hardcoded list of common publishers
        # No longer fetches news with default tickers
        publishers = await news_service.get_available_publishers()
        return {"publishers": publishers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/news/fetch-content")
async def fetch_news_content(request: NewsContentRequest):
    """Fetch full content of a news article from its URL"""
    try:
        content = await news_service.fetch_article_content(request.url)
        if not content:
            raise HTTPException(status_code=404, detail="Could not fetch content")
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI Draw Endpoint
@app.post("/api/ai/draw")
async def ai_draw(request: Request, current_user: User = Depends(get_current_user)):
    """Generate a drawing via AI based on prompt.
    Expects JSON body with {"prompt": str, "color": optional str, "chartData": optional list}
    Returns a drawing object compatible with frontend drawing format.
    """
    try:
        data = await request.json()
        prompt = data.get("prompt")
        color = data.get("color") or "#2196F3"
        chart_data = data.get("chartData")
        
        # Determine provider
        use_gemini = False
        if current_user.gemini_api_key:
            use_gemini = True
        elif os.getenv("GOOGLE_GEMINI_API_KEY"):
            use_gemini = True
            
        # Check if user explicitly prefers local llama (if we had that setting, but for now fallback logic)
        if current_user.use_local_llama:
            use_gemini = False

        if use_gemini:
            try:
                print(f"[API] Using Gemini for AI Draw: {prompt}")
                gemini = GeminiService(api_key=current_user.gemini_api_key)
                drawing = await gemini.generate_drawing(prompt, color, chart_data)
                return {"drawing": drawing}
            except Exception as e:
                print(f"[API] Gemini failed, falling back to Llama: {e}")
                # Fallback to Llama
        
        print(f"[API] Using Llama for AI Draw: {prompt}")
        drawing = llama_service.generate_drawing(prompt, color, chart_data)
        return {"drawing": drawing}

    except Exception as e:
        print(f"[API] Error in AI draw endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Earnings Endpoints
@app.get("/api/earnings")
async def get_earnings(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    months: int = 6, 
    offset_months: int = 0, 
    db: Session = Depends(get_db)
):
    """Get earnings calendar - loads 6 months at a time with 24h cache refresh"""
    try:
        print("\n" + "=" * 80)
        print("[API] ENDPOINT CALLED: /api/earnings")
        
        # If start_date and end_date provided, use new get_earnings method (range)
        if start_date and end_date:
            print(f"[API] Fetching range: {start_date} to {end_date}")
            try:
                s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                earnings = await earnings_service.get_earnings(s_date, e_date)
                print(f"[API] Returning {len(earnings)} earnings for range")
                return {"earnings": earnings}
            except Exception as e:
                print(f"[API] Error getting earnings range: {e}")
                import traceback
                traceback.print_exc()
                return {"earnings": []}

        print(f"[API] start_date: {start_date}")
        print(f"[API] months: {months} (6-month blocks)")
        print(f"[API] offset_months: {offset_months} (for infinite scroll)")
        print("=" * 80)
        
        # Always use calendar method for 6-month blocks with 24h cache
        print("[API] Using get_earnings_calendar (Nasdaq API with 24h cache for 6-month blocks)...")
        earnings = []
        try:
            earnings = await asyncio.wait_for(
                earnings_service.get_earnings_calendar(start_date, months=months, offset_months=offset_months),
                timeout=300.0  # 5 minutes timeout for 6 months of data
            )
        except asyncio.TimeoutError:
            print("[API] ERROR: Request timed out after 300 seconds")
            earnings = []
        except Exception as e:
            print(f"[API] Error getting earnings calendar: {e}")
            import traceback
            traceback.print_exc()
            earnings = []
        
        print("=" * 80)
        print(f"[API] RESPONSE: Returning {len(earnings)} earnings")
        if earnings:
            print(f"[API] First: {earnings[0].get('symbol')} on {earnings[0].get('date')}")
            print(f"[API] Last: {earnings[-1].get('symbol')} on {earnings[-1].get('date')}")
        print("=" * 80 + "\n")
        
        return {"earnings": earnings, "offset_months": offset_months, "months": months}
    except Exception as e:
        print("=" * 80)
        print(f"[API] ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        # Return empty list instead of error to avoid breaking frontend
        return {"earnings": [], "offset": offset_months, "months": months}

@app.post("/api/earnings/ask")
async def ask_llama_earnings(request: AskLlamaRequest, current_user: Optional[User] = Depends(get_current_user)):
    """Ask Llama about an earning event or general question"""
    try:
        if request.symbol and request.company and request.date:
            # Context-aware question
            if not request.question:
                prompt = f"Tell me about the earnings for {request.company} ({request.symbol}) on {request.date}. What are the expectations?"
            else:
                prompt = f"Regarding {request.company} ({request.symbol}) earnings on {request.date}: {request.question}"
        elif request.question:
            # General question
            prompt = request.question
        else:
            raise HTTPException(status_code=400, detail="Either a question or earnings context (symbol, company, date) must be provided")
            
        # Determine provider and key
        provider = "local"
        api_key = None
        user_id = None
        
        if current_user:
            user_id = current_user.id
            if current_user.ai_provider and current_user.ai_provider != "local":
                provider = current_user.ai_provider
                if provider == "openai":
                    api_key = current_user.openai_api_key
                elif provider == "anthropic":
                    api_key = current_user.anthropic_api_key
                elif provider == "deepseek":
                    api_key = current_user.deepseek_api_key
                elif provider == "gemini_pro":
                    api_key = current_user.gemini_pro_api_key
                elif provider == "gemini":
                    # Use GeminiService directly or via factory if we added it
                    # For now, let's stick to the pattern
                    pass

        # Override provider if specified in request (and allowed)
        if request.provider and request.provider != "local":
             # Basic validation could go here, for now trust the frontend/user preference
             provider = request.provider
             
             # If provider is gemini, ensure we have a key
             if provider == "gemini":
                 if current_user and current_user.gemini_api_key:
                     api_key = current_user.gemini_api_key
                 elif os.getenv("GOOGLE_GEMINI_API_KEY"):
                     api_key = os.getenv("GOOGLE_GEMINI_API_KEY")

        response = llama_service.generate_response(prompt, user_id=user_id, provider=provider, api_key=api_key)
        return {"response": response}
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

@app.get("/api/earnings/{ticker}/eps-history")
async def get_ticker_eps_history(ticker: str, years: int = 2):
    """Get EPS history for a ticker for the last N years (default 2 years = ~8 quarters) with reliability metrics"""
    try:
        result = await earnings_service.get_ticker_eps_history(ticker.upper(), years=years)
        return {
            "ticker": ticker.upper(), 
            "eps_history": result.get('quarters', []), 
            "reliability": result.get('reliability', {}),
            "quarters_count": len(result.get('quarters', []))
        }
    except Exception as e:
        print(f"[API] Error getting EPS history for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Authentication Endpoints
@app.options("/api/auth/register")
async def register_options():
    """Handle CORS preflight for register endpoint"""
    return {}

@app.post("/api/auth/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if username or email already exists
        if get_user_by_username(db, user_data.username):
            raise HTTPException(status_code=400, detail="Username already registered")
        if get_user_by_email(db, user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        user = create_user(db, user_data.username, user_data.email, user_data.password)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "message": "User created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Registration error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.options("/api/auth/login")
async def login_options():
    """Handle CORS preflight for login endpoint"""
    return {"message": "OK"}

@app.post("/api/auth/login")
async def login(request: Request, db: Session = Depends(get_db)):
    """Login and get access token - accepts both JSON and form-data"""
    try:
        content_type = request.headers.get("content-type", "").lower()
        username = None
        password = None
        
        print(f"[LOGIN] Content-Type: {content_type}")
        
        # Try to parse as form-data first (OAuth2PasswordRequestForm standard)
        if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            try:
                form_data = await request.form()
                username = form_data.get("username")
                password = form_data.get("password")
                print(f"[LOGIN] Parsed form-data: username={username is not None}")
            except Exception as e:
                print(f"[LOGIN] Error parsing form-data: {e}")
                import traceback
                traceback.print_exc()
        
        # If form-data didn't work, try JSON
        if not username or not password:
            try:
                # Check if body is JSON
                if "application/json" in content_type or not content_type:
                    body = await request.json()
                    username = body.get("username")
                    password = body.get("password")
                    print(f"[LOGIN] Parsed JSON: username={username is not None}")
            except Exception as e:
                print(f"[LOGIN] Error parsing JSON: {e}")
        
        if not username or not password:
            print(f"[LOGIN] Missing credentials: username={username is not None}, password={password is not None}")
            raise HTTPException(status_code=400, detail="Username and password required")
        
        print(f"[LOGIN] Attempting login for user: {username}")
        
        # Authenticate user
        user = authenticate_user(db, username, password)
        if not user:
            print(f"[LOGIN] Authentication failed for user: {username}")
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        print(f"[LOGIN] Authentication successful for user: {username} (ID: {user.id})")
        
        # Generate access token
        access_token = create_access_token(data={"sub": str(user.id)})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "bio": user.bio,
                "phone": user.phone,
                "location": user.location,
                "website": user.website,
                "website": user.website,
                "profile_picture_url": user.profile_picture_url,
                "use_local_llama": user.use_local_llama,
                "gemini_api_key": user.gemini_api_key,
                "ai_provider": user.ai_provider,
                "gemini_pro_api_key": user.gemini_pro_api_key,
                "openai_api_key": user.openai_api_key,
                "anthropic_api_key": user.anthropic_api_key,
                "deepseek_api_key": user.deepseek_api_key,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[LOGIN] Error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "bio": current_user.bio,
        "phone": current_user.phone,
        "location": current_user.location,
        "website": current_user.website,
        "profile_picture_url": current_user.profile_picture_url,
        "use_local_llama": current_user.use_local_llama,
        "gemini_api_key": current_user.gemini_api_key,
        "ai_provider": current_user.ai_provider,
        "gemini_pro_api_key": current_user.gemini_pro_api_key,
        "openai_api_key": current_user.openai_api_key,
        "anthropic_api_key": current_user.anthropic_api_key,
        "deepseek_api_key": current_user.deepseek_api_key,
    }

@app.post("/api/auth/logout")
async def logout():
    """Logout (client-side token removal)"""
    return {"message": "Logged out successfully"}

@app.get("/api/user/tabs")
async def get_user_tabs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's tab configuration"""
    try:
        if current_user.tabs:
            tabs_data = json.loads(current_user.tabs)
            return {"tabs": tabs_data}
        return {"tabs": []}
    except Exception as e:
        print(f"Error loading tabs: {e}")
        return {"tabs": []}

@app.put("/api/user/tabs")
async def save_user_tabs(tabs_data: TabsUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Save user's tab configuration"""
    try:
        current_user.tabs = json.dumps(tabs_data.tabs)
        current_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(current_user)
        return {"message": "Tabs saved successfully", "tabs": tabs_data.tabs}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/auth/profile")
async def update_profile(profile_data: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user profile"""
    try:
        if profile_data.bio is not None:
            current_user.bio = profile_data.bio
        if profile_data.location is not None:
            current_user.location = profile_data.location
        if profile_data.website is not None:
            current_user.website = profile_data.website
        if profile_data.profile_picture_url is not None:
            current_user.profile_picture_url = profile_data.profile_picture_url
        if profile_data.use_local_llama is not None:
            current_user.use_local_llama = profile_data.use_local_llama
        if profile_data.gemini_api_key is not None:
            current_user.gemini_api_key = profile_data.gemini_api_key
        if profile_data.ai_provider is not None:
            current_user.ai_provider = profile_data.ai_provider
        if profile_data.gemini_pro_api_key is not None:
            current_user.gemini_pro_api_key = profile_data.gemini_pro_api_key
        if profile_data.openai_api_key is not None:
            current_user.openai_api_key = profile_data.openai_api_key
        if profile_data.anthropic_api_key is not None:
            current_user.anthropic_api_key = profile_data.anthropic_api_key
        if profile_data.deepseek_api_key is not None:
            current_user.deepseek_api_key = profile_data.deepseek_api_key
        
        current_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(current_user)
        
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "bio": current_user.bio,
            "phone": current_user.phone,
            "location": current_user.location,
            "website": current_user.website,
            "profile_picture_url": current_user.profile_picture_url,
            "use_local_llama": current_user.use_local_llama,
            "gemini_api_key": current_user.gemini_api_key,
            "ai_provider": current_user.ai_provider,
            "gemini_pro_api_key": current_user.gemini_pro_api_key,
            "openai_api_key": current_user.openai_api_key,
            "anthropic_api_key": current_user.anthropic_api_key,
            "deepseek_api_key": current_user.deepseek_api_key,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/profile_pictures")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{current_user.id}_{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update user profile picture URL
        # In production, you'd upload to S3/cloud storage and get a URL
        # For now, we'll use a relative path
        profile_picture_url = f"/uploads/profile_pictures/{unique_filename}"
        current_user.profile_picture_url = profile_picture_url
        db.commit()
        db.refresh(current_user)
        
        return {
            "url": profile_picture_url,
            "message": "Profile picture uploaded successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload profile picture: {str(e)}")

# Chat Endpoints
@app.get("/api/chat/messages")
async def get_chat_messages(
    limit: int = 100, 
    recipient_id: Optional[int] = None, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent chat messages"""
    messages = chat_service.get_messages(db, limit, user_id=current_user.id, recipient_id=recipient_id)
    return {"messages": messages}

@app.post("/api/chat/message")
async def send_chat_message(message: ChatMessage, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a chat message"""
    try:
        chat_msg = chat_service.add_message(
            db,
            current_user.id,
            current_user.username,
            message.message,
            message.type,
            message.image_data,
            message.recipient_id
        )
        
        # Broadcast to all connected WebSocket clients (or specific recipient)
        await ws_manager.broadcast({
            "type": "chat_message",
            "data": chat_msg
        }, recipient_id=message.recipient_id)
        
        # Also send to sender if it's a private message so they see it too (if they have other tabs open)
        if message.recipient_id:
             await ws_manager.broadcast({
                "type": "chat_message",
                "data": chat_msg
            }, recipient_id=current_user.id)
        
        # Process AI response in background
        # Note: In a real app, this should be a background task
        await chat_service.process_ai_response(
            current_user.id, 
            message.message, 
            db, 
            invite_llama=message.invite_llama, 
            invite_gemini=message.invite_gemini, 
            is_search=message.is_search,
            ws_manager=ws_manager
        )
        
        return {"message": chat_msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/message/{message_id}")
async def delete_chat_message(message_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a chat message"""
    try:
        # Check if message exists and belongs to user
        # For simplicity, we'll let the service handle deletion, but ideally we should check ownership here
        # However, ChatService.delete_message just deletes by ID. 
        # Let's fetch first to check ownership
        from models.chat import Message
        msg = db.query(Message).filter(Message.id == message_id).first()
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
            
        if msg.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this message")
            
        success = chat_service.delete_message(db, message_id)
        if success:
            # Broadcast deletion
            await ws_manager.broadcast({
                "type": "message_deleted",
                "message_id": message_id
            })
            return {"message": "Message deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete message")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Strategy Endpoints
@app.get("/api/strategies")
async def get_strategies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all user strategies"""
    try:
        strategies = strategy_service.get_strategies(db, current_user.id)
        # Parse JSON definition for response
        return {"strategies": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "definition": json.loads(s.definition),
                "created_at": s.created_at,
                "updated_at": s.updated_at
            } for s in strategies
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies")
async def create_strategy(strategy: StrategyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new strategy"""
    try:
        new_strategy = strategy_service.create_strategy(
            db, 
            current_user.id, 
            strategy.name, 
            strategy.description, 
            strategy.definition
        )
        return {
            "id": new_strategy.id,
            "name": new_strategy.name,
            "description": new_strategy.description,
            "definition": json.loads(new_strategy.definition),
            "created_at": new_strategy.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/strategies/{strategy_id}")
async def update_strategy(strategy_id: int, strategy: StrategyUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update a strategy"""
    try:
        updated = strategy_service.update_strategy(
            db,
            strategy_id,
            current_user.id,
            strategy.name,
            strategy.description,
            strategy.definition
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Strategy not found")
            
        return {
            "id": updated.id,
            "name": updated.name,
            "description": updated.description,
            "definition": json.loads(updated.definition),
            "updated_at": updated.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a strategy"""
    try:
        success = strategy_service.delete_strategy(db, strategy_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return {"message": "Strategy deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies/generate")
async def generate_strategy(request: StrategyGenerateRequest, current_user: User = Depends(get_current_user)):
    """Generate a strategy from natural language prompt"""
    try:
        strategy_json = llama_service.generate_strategy_from_prompt(request.prompt)
        return {"strategy": strategy_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload profile picture"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (max 5MB)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image size must be less than 5MB")
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{current_user.id}_{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # Generate URL (in production, use actual domain/CDN)
        file_url = f"/uploads/profile_pictures/{unique_filename}"
        
        # Update user profile
        db_gen = get_db()
        db = next(db_gen)
        try:
            current_user.profile_picture_url = file_url
            db.commit()
            db.refresh(current_user)
        finally:
            pass  # get_db() is a generator, we don't close it manually
        
        return {"url": file_url, "message": "Profile picture uploaded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

# Alpaca Paper Trading API endpoints (optional - deprecated, use IG Markets instead)
@app.get("/api/alpaca/account")
async def get_alpaca_account(current_user: User = Depends(get_current_user)):
    """Get Alpaca account information (deprecated - use IG Markets)"""
    if not alpaca_service:
        raise HTTPException(status_code=503, detail="Alpaca service not available. Use IG Markets instead.")
    try:
        account = await alpaca_service.get_account()
        return account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alpaca/positions")
async def get_alpaca_positions(current_user: User = Depends(get_current_user)):
    """Get all open positions (deprecated - use IG Markets)"""
    if not alpaca_service:
        raise HTTPException(status_code=503, detail="Alpaca service not available. Use IG Markets instead.")
    try:
        positions = await alpaca_service.get_positions()
        return {"positions": positions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alpaca/orders")
async def get_alpaca_orders(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get orders (deprecated - use IG Markets)"""
    if not alpaca_service:
        raise HTTPException(status_code=503, detail="Alpaca service not available. Use IG Markets instead.")
    try:
        orders = await alpaca_service.get_orders(status=status, limit=limit)
        return {"orders": orders}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alpaca/orders")
async def place_alpaca_order(
    order_data: AlpacaOrderRequest,
    current_user: User = Depends(get_current_user)
):
    """Place an order (deprecated - use IG Markets)"""
    if not alpaca_service:
        raise HTTPException(status_code=503, detail="Alpaca service not available. Use IG Markets instead.")
    try:
        order = await alpaca_service.place_order(
            symbol=order_data.symbol,
            qty=order_data.qty,
            side=order_data.side,
            order_type=order_data.order_type,
            time_in_force=order_data.time_in_force,
            limit_price=order_data.limit_price,
            stop_price=order_data.stop_price
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/alpaca/orders/{order_id}")
async def cancel_alpaca_order(order_id: str, current_user: User = Depends(get_current_user)):
    """Cancel an order (deprecated - use IG Markets)"""
    if not alpaca_service:
        raise HTTPException(status_code=503, detail="Alpaca service not available. Use IG Markets instead.")
    try:
        result = await alpaca_service.cancel_order(order_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/alpaca/orders")
async def cancel_all_alpaca_orders(current_user: User = Depends(get_current_user)):
    """Cancel all orders (deprecated - use IG Markets)"""
    if not alpaca_service:
        raise HTTPException(status_code=503, detail="Alpaca service not available. Use IG Markets instead.")
    try:
        result = await alpaca_service.cancel_all_orders()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alpaca/portfolio/history")
async def get_alpaca_portfolio_history(
    period: str = "1M",
    timeframe: str = "1Day",
    current_user: User = Depends(get_current_user)
):
    """Get portfolio history (deprecated - use IG Markets)"""
    if not alpaca_service:
        raise HTTPException(status_code=503, detail="Alpaca service not available. Use IG Markets instead.")
    try:
        history = await alpaca_service.get_portfolio_history(period=period, timeframe=timeframe)
        return history
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bot Endpoints
@app.post("/api/bots")
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new bot"""
    try:
        print(f"[API] Creating bot for user {current_user.id}: {bot_data.name}")
        bot = bot_service.create_bot(
            db=db,
            user_id=current_user.id,
            name=bot_data.name,
            bot_type=bot_data.bot_type,
            description=bot_data.description
        )
        bot_dict = bot.to_dict()
        print(f"[API] Bot created successfully: {bot_dict}")
        return bot_dict
    except Exception as e:
        print(f"[API] Error creating bot: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots")
async def get_bots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bots for the current user"""
    try:
        print(f"[API] Getting bots for user {current_user.id}")
        bots = bot_service.get_user_bots(db, current_user.id)
        print(f"[API] Found {len(bots)} bots for user {current_user.id}")
        result = []
        for bot in bots:
            bot_dict = bot.to_dict()
            bot_dict['owner'] = current_user.username
            result.append(bot_dict)
        print(f"[API] Returning {len(result)} bots")
        return {"bots": result}
    except Exception as e:
        print(f"[API] Error getting bots: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots/public")
async def get_public_bots(db: Session = Depends(get_db)):
    """Get all active bots (for public competition view)"""
    try:
        bots = bot_service.get_all_bots(db)
        # Get owner usernames
        result = []
        for bot in bots:
            bot_dict = bot.to_dict()
            user = get_user_by_id(db, bot.user_id)
            bot_dict['owner'] = user.username if user else 'Unknown'
            result.append(bot_dict)
        return {"bots": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots/{bot_id}")
async def get_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific bot"""
    try:
        bot = bot_service.get_bot(db, bot_id, current_user.id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return bot.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/bots/{bot_id}/config")
async def update_bot_config(
    bot_id: int,
    config: BotConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update bot configuration"""
    try:
        # Defensive import: prevents NameError if an older code path references Bot
        # (and also helps ensure local models package is used).
        # Defensive import removed - Bot is imported at module level

        # Build config dict with all fields (IG Markets + Gemini + legacy Alpaca)
        config_dict = {}
        
        # IG Markets configuration (required for Earnings Report Genius)
        if config.ig_username:
            config_dict['ig_username'] = config.ig_username
        if config.ig_password:
            config_dict['ig_password'] = config.ig_password
        if config.ig_api_key:
            config_dict['ig_api_key'] = config.ig_api_key
        if config.ig_acc_type:
            config_dict['ig_acc_type'] = config.ig_acc_type
        
        # Gemini AI configuration (optional)
        if config.gemini_api_key:
            config_dict['gemini_api_key'] = config.gemini_api_key
        
        # Legacy Alpaca (keep for backward compatibility if provided)
        if config.alpaca_api_key:
            config_dict['alpaca_api_key'] = config.alpaca_api_key
        if config.alpaca_api_secret:
            config_dict['alpaca_api_secret'] = config.alpaca_api_secret
        
        # Get existing bot using bot_service to merge config
        existing_bot = bot_service.get_bot(db, bot_id, current_user.id)
        if not existing_bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        existing_config = existing_bot.get_config()
        # Update only the fields provided in the request
        existing_config.update({k: v for k, v in config_dict.items() if v is not None})
        
        bot = bot_service.update_bot_config(db, bot_id, current_user.id, existing_config)
        return bot.to_dict()
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Error updating bot config: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/activate")
async def activate_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a bot"""
    try:
        bot = bot_service.activate_bot(db, bot_id, current_user.id)
        return bot.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/deactivate")
async def deactivate_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate a bot"""
    try:
        bot = bot_service.deactivate_bot(db, bot_id, current_user.id)
        return bot.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bots/{bot_id}")
async def delete_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a bot"""
    try:
        success = bot_service.delete_bot(db, bot_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Bot not found")
        return {"message": "Bot deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bots/{bot_id}/export")
async def export_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export bot configuration as JSON (including API credentials for easy import)"""
    try:
        bot = bot_service.get_bot(db, bot_id, current_user.id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        config = bot.get_config()
        # Include ALL configuration including API credentials for easy import
        # This allows users to quickly transfer bot settings between accounts/instances
        
        export_data = {
            "version": "1.0",
            "name": bot.name,
            "bot_type": bot.bot_type,
            "description": bot.description,
            "config": config  # Include all config including API keys
        }
        
        return export_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/import")
async def import_bot(
    import_data: BotImport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import a bot from JSON configuration (including API credentials)"""
    try:
        # Check if bot with same name already exists for this user
        existing_bot = bot_service.get_bot_by_name(db, current_user.id, import_data.name)
        
        if existing_bot:
            print(f"[Import] Updating existing bot: {existing_bot.name} (ID: {existing_bot.id})")
            # Update existing bot
            bot = existing_bot
            bot.bot_type = import_data.bot_type
            bot.description = import_data.description
            # Status remains as is, or could be reset to inactive if needed
            # bot.status = 'inactive' 
        else:
            print(f"[Import] Creating new bot: {import_data.name}")
            # Create a new bot with the imported settings
            bot = bot_service.create_bot(
                db=db,
                user_id=current_user.id,
                name=import_data.name,
                bot_type=import_data.bot_type,
                description=import_data.description
            )
        
        # Set the configuration (including API keys if provided in the import file)
        if import_data.config:
            bot.set_config(import_data.config)
            bot.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(bot)
        
        return bot.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/import")
async def import_bot_config(
    bot_id: int,
    import_data: BotImport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import configuration into a specific bot"""
    try:
        bot = bot_service.get_bot(db, bot_id, current_user.id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        print(f"[Import] Importing config into bot {bot_id}: {bot.name}")
        
        # Update bot details
        bot.bot_type = import_data.bot_type
        if import_data.description:
            bot.description = import_data.description
            
        # Update configuration
        if import_data.config:
            bot.set_config(import_data.config)
            
        bot.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(bot)
        
        return bot.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/call/llama")
async def call_llama_explanation(
    bot_id: int,
    request: Optional[BotChatRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get explanation from Llama about bot activity"""
    try:
        bot = bot_service.get_bot(db, bot_id, current_user.id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        # 1. Read profitto.json
        profit_data = {}
        profit_path = os.path.join("backend", "profitto.json")
        if os.path.exists(profit_path):
            with open(profit_path, "r") as f:
                profit_data = json.load(f)
        
        # 2. Read last 20 lines of bot_activity.log
        log_lines = []
        log_path = os.path.join("backend", "bot_activity.log")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                # Simple way to get last lines - for production use efficient tail
                lines = f.readlines()
                log_lines = lines[-20:] if len(lines) > 20 else lines
        
        # 3. Construct context
        context = f"Bot Name: {bot.name}\n"
        context += f"Profit Status: {json.dumps(profit_data, indent=2)}\n\n"
        context += "Recent Activity Log:\n" + "".join(log_lines)
        
        # 4. Call Llama
        if request and request.prompt:
            # Chat mode
            history = request.history or []
            explanation = llama_service.chat_about_bot(context, history, request.prompt)
        else:
            # Initial explanation mode
            explanation = llama_service.generate_explanation(context)
        
        return {"explanation": explanation}
    except Exception as e:
        print(f"Error calling Llama: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/call/gemini")
async def call_gemini_explanation(
    bot_id: int,
    request: Optional[BotChatRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get explanation from Gemini about bot activity"""
    try:
        bot = bot_service.get_bot(db, bot_id, current_user.id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        # 1. Read profitto.json
        profit_data = {}
        profit_path = os.path.join("backend", "profitto.json")
        if os.path.exists(profit_path):
            with open(profit_path, "r") as f:
                profit_data = json.load(f)
        
        # 2. Read last 20 lines of bot_activity.log
        log_lines = []
        log_path = os.path.join("backend", "bot_activity.log")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                lines = f.readlines()
                log_lines = lines[-20:] if len(lines) > 20 else lines
        
        # 3. Construct context
        context = f"Bot Name: {bot.name}\n"
        context += f"Profit Status: {json.dumps(profit_data, indent=2)}\n\n"
        context += "Recent Activity Log:\n" + "".join(log_lines)
        
        # 4. Call Gemini
        # Instantiate GeminiService with bot's API key
        config = bot.get_config()
        gemini_api_key = config.get('gemini_api_key')
        
        # Fallback to user profile key if not in bot config
        if not gemini_api_key:
            gemini_api_key = current_user.gemini_api_key
            
        gemini_service = GeminiService(api_key=gemini_api_key)
        
        if request and request.prompt:
            # Chat mode
            history = request.history or []
            explanation = await gemini_service.chat_about_bot(context, history, request.prompt)
        else:
            # Initial explanation mode
            explanation = await gemini_service.generate_explanation(context)
        
        return {"explanation": explanation}
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket endpoint for real-time news and chat updates"""
    user_id = None
    username = None
    
    # Try to authenticate if token is provided
    if token:
        try:
            payload = verify_token(token)
            if payload:
                user_id = int(payload.get("sub"))
                # We need to get username. We can't use Depends(get_db) here easily.
                # We'll use a fresh session.
                db = SessionLocal()
                try:
                    user = get_user_by_id(db, user_id)
                    if user:
                        username = user.username
                finally:
                    db.close()
        except Exception as e:
            print(f"WebSocket auth failed: {e}")
            
    await ws_manager.connect(websocket, user_id, username)
    try:
        # Start background tasks (only if tickers are provided)
        # News monitor no longer starts automatically - must be explicitly requested with tickers
        # asyncio.create_task(news_service.start_news_monitor(ws_manager))
        
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
            message = json.loads(data)
            if message.get("type") == "subscribe_news":
                await ws_manager.send_personal_message(
                    {"type": "subscribed", "tickers": message.get("tickers")},
                    websocket
                )
            elif message.get("type") == "chat_message":
                # Handle chat messages via WebSocket (alternative to REST)
                # For now, we use REST API for sending messages
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect_and_broadcast(websocket)

@app.get("/api/users/online")
async def get_online_users():
    """Get list of online users"""
    return {"users": ws_manager.get_online_users()}

# Earnings Endpoints
@app.get("/api/earnings")
async def get_earnings(
    start_date: Optional[str] = None,
    months: int = 6,
    offset_months: int = 0,
    end_date: Optional[str] = None
):
    """Get earnings calendar data"""
    try:
        print(f"[API] Earnings request: start_date={start_date}, months={months}, offset_months={offset_months}, end_date={end_date}")
        
        # Use the earnings service's calendar method which uses Nasdaq API
        earnings_data = await earnings_service.get_earnings_calendar(
            start_date=start_date,
            months=months,
            offset_months=offset_months
        )
        
        # Filter out weekend earnings (Saturday=5, Sunday=6)
        from datetime import datetime as dt
        filtered_earnings = []
        for earning in earnings_data:
            try:
                earning_date = dt.fromisoformat(earning.get('date', ''))
                # Only include weekdays (Monday=0 to Friday=4)
                if earning_date.weekday() < 5:
                    filtered_earnings.append(earning)
            except:
                # If date parsing fails, include it anyway
                filtered_earnings.append(earning)
        
        earnings_data = filtered_earnings
        print(f"[API] Filtered to {len(earnings_data)} weekday earnings (removed weekends)")
        
        # Save earnings data to JSON file for AI access
        try:
            earnings_file_path = os.path.join(BACKEND_DIR, "earnings_data.json")
            with open(earnings_file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "total_earnings": len(earnings_data),
                    "earnings": earnings_data
                }, f, indent=2, ensure_ascii=False, default=str)
            print(f"[API] Saved {len(earnings_data)} earnings to {earnings_file_path}")
        except Exception as save_error:
            print(f"[API] Warning: Failed to save earnings to JSON: {save_error}")
        
        print(f"[API] Returning {len(earnings_data)} earnings")
        return {"earnings": earnings_data}
    except Exception as e:
        print(f"[API] Error fetching earnings: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/message/{message_id}")
async def delete_chat_message(message_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a chat message"""
    try:
        success = chat_service.delete_message(db, message_id)
        if success:
            # Broadcast deletion
            await ws_manager.broadcast({
                "type": "message_deleted",
                "message_id": message_id
            })
            return {"message": "Message deleted"}
        else:
            raise HTTPException(status_code=404, detail="Message not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/history")
async def clear_chat_history(recipient_id: Optional[int] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clear chat history"""
    try:
        count = chat_service.clear_history(db, current_user.id, recipient_id)
        
        # Broadcast clear event so clients can clear their view
        await ws_manager.broadcast({
            "type": "history_cleared",
            "recipient_id": recipient_id
        })
        
        return {"message": f"History cleared, {count} messages deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot reload for development
        log_level="info"
    )

