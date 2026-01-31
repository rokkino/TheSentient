"""
FastAPI Backend for The Sentient Portfolio Tracker
"""
from __future__ import annotations

import warnings
from contextlib import asynccontextmanager

# Suppress noisy third-party deprecation warnings so terminal stays readable
warnings.filterwarnings("ignore", category=DeprecationWarning, module="jose.jwt")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn*")
warnings.filterwarnings("ignore", message=".*remove second argument of ws_handler.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic*")
warnings.filterwarnings("ignore", message=".*Field.*shadows.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*extra keyword arguments on Field.*", category=DeprecationWarning)

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

from services.auth_service import create_user, authenticate_user, create_access_token, get_user_by_id, verify_token, get_user_by_username, get_user_by_email
from services.chat_service import chat_service
from services.strategy_service import strategy_service
from services.symbol_mapper import symbol_mapper
# AlpacaService is optional - only available if alpaca-py is installed
from services.alpaca_service import AlpacaService, ALPACA_AVAILABLE
from services.bot_service import bot_service
from services.llama_service import llama_service
from services.gemini_service import GeminiService
from services.scheduler_service import scheduler_service
from services.scheduler_jobs import execute_orders_job, analyze_earnings_job, refresh_earnings_cache_job
from services.earnings_service import earnings_service
from websocket_manager import WebSocketManager
from models.user import init_db, get_db, User, SessionLocal
from models.bot import Bot, Decision
from models.account import Account
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle - replaces deprecated on_event."""
    # Startup
    print("Starting up...")
    scheduler_service.start()
    scheduler_service.add_job(execute_orders_job, 'interval', minutes=1, id='execute_orders')
    scheduler_service.add_job(analyze_earnings_job, 'interval', minutes=30, id='analyze_earnings')
    scheduler_service.add_job(refresh_earnings_cache_job, 'interval', days=30, id='refresh_earnings_cache')
    print("Scheduled execute_orders_job, analyze_earnings_job, refresh_earnings_cache_job")
    yield
    # Shutdown
    print("Shutting down...")
    scheduler_service.shutdown()

app = FastAPI(title="The Sentient API", version="1.0.0", lifespan=lifespan)

# Add build header to all responses (helps confirm you're hitting the right backend process)
@app.middleware("http")
async def _add_build_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-TheSentient-Build"] = SERVER_BUILD
    return response

@app.get("/api/debug/build")
async def debug_build():
    """Return backend build marker and Alpaca availability (debugging)."""
    try:
        from services.alpaca_service import ALPACA_AVAILABLE
        return {"build": SERVER_BUILD, "alpaca_available": ALPACA_AVAILABLE}
    except Exception:
        return {"build": SERVER_BUILD, "alpaca_available": False}

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
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://127.0.0.1:5173",
        "http://34.53.28.120",  # Production VM IP
    ],
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
    gemini_api_key: Optional[str] = None
    ai_provider: Optional[str] = None
    gemini_pro_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    llama_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_model: Optional[str] = None
    anthropic_model: Optional[str] = None
    deepseek_model: Optional[str] = None
    llama_model: Optional[str] = None

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
    # Global Account (Alternative to manual credentials)
    account_id: Optional[int] = None
    broker: Optional[str] = 'IG'

    # IG Markets configuration (required for Earnings Report Genius)
    ig_username: Optional[str] = None
    ig_password: Optional[str] = None
    ig_api_key: Optional[str] = None
    ig_acc_type: Optional[str] = None  # 'DEMO' or 'LIVE'
    
    # AI Analysis (optional but recommended)
    gemini_api_key: Optional[str] = None
    # Legacy Alpaca (deprecated, kept for backward compatibility)
    alpaca_api_key: Optional[str] = None
    alpaca_api_secret: Optional[str] = None
    alpaca_paper: Optional[bool] = None

def _verify_alpaca_credentials_rest(api_key: str, api_secret: str, paper: bool = True) -> tuple[bool, str]:
    """
    Verify Alpaca API credentials via direct REST call (no alpaca-py required).
    Returns (success, message).
    """
    import requests
    base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
    url = f"{base_url}/v2/account"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return True, "Credentials valid"
        if r.status_code in (401, 403):
            return False, "Invalid API key or secret"
        return False, f"Alpaca API returned {r.status_code}: {r.text[:200] if r.text else 'No body'}"
    except requests.RequestException as e:
        return False, f"Network error: {str(e)}"


class TestConnectionRequest(BaseModel):
    broker: str
    config: Dict[str, Any]

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

class SchedulerStatusResponse(BaseModel):
    running: bool
    jobs: List[Dict[str, Any]]
    logs: List[Dict[str, Any]]

class DecisionCreate(BaseModel):
    bot_id: int
    symbol: str
    decision: str  # BUY, SELL, HOLD, WAIT
    execution_time: Optional[str] = None  # ISO datetime
    reasoning: Optional[str] = None

class DecisionUpdate(BaseModel):
    symbol: Optional[str] = None
    decision: Optional[str] = None
    execution_time: Optional[str] = None
    reasoning: Optional[str] = None
    status: Optional[str] = None  # PENDING, EXECUTED, CANCELLED, FAILED

# API Routes
@app.get("/")
async def root():
    return {"message": "The Sentient API", "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/time")
async def get_time():
    """Get current server time"""
    now = datetime.now()
    return {
        "server_time_iso": now.isoformat(),
        "server_time_formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": now.timestamp()
    }

# Scheduler Endpoints
@app.get("/api/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(current_user: User = Depends(get_current_user)):
    """Get scheduler status, jobs, and logs"""
    return {
        "running": scheduler_service.scheduler.running,
        "jobs": scheduler_service.get_jobs(),
        "logs": scheduler_service.get_logs()
    }

@app.get("/api/bot/decisions")
async def get_bot_decisions(limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get recent bot decisions"""
    from models.bot import Decision
    decisions = db.query(Decision).order_by(Decision.created_at.desc()).limit(limit).all()
    return {"decisions": [d.to_dict() for d in decisions]}

@app.get("/api/bot/profit")
async def get_bot_profit(current_user: User = Depends(get_current_user)):
    """Get P&L and portfolio summary from profitto.json"""
    profit_path = os.path.join(BACKEND_DIR, "profitto.json")
    if not os.path.exists(profit_path):
        return {
            "profit_loss_value": 0.0,
            "profit_loss_percent": 0.0,
            "total_balance": 0.0,
            "available_cash": 0.0,
            "currency": "USD",
            "timestamp": None,
            "bot_name": None,
        }
    try:
        with open(profit_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "profit_loss_value": float(data.get("profit_loss_value", 0)),
            "profit_loss_percent": float(data.get("profit_loss_percent", 0)),
            "total_balance": float(data.get("total_balance", 0)),
            "available_cash": float(data.get("available_cash", 0)),
            "currency": data.get("currency", "USD"),
            "timestamp": data.get("timestamp"),
            "bot_name": data.get("bot_name"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot/decisions")
async def create_bot_decision(
    body: DecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new decision (manual order)"""
    from models.bot import Decision, Bot
    from datetime import datetime as dt
    try:
        # Verify bot exists and user has access
        bot = db.query(Bot).filter(Bot.id == body.bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        exec_time = None
        if body.execution_time:
            try:
                s = str(body.execution_time).strip()
                s = s.replace("Z", "+00:00")
                exec_time = dt.fromisoformat(s)
            except Exception:
                exec_time = dt.now(timezone.utc)
        if not exec_time:
            exec_time = dt.now(timezone.utc)
        d = Decision(
            bot_id=body.bot_id,
            symbol=body.symbol.strip().upper(),
            decision=body.decision.upper(),
            execution_time=exec_time,
            status="PENDING",
            reasoning=body.reasoning or "",
        )
        db.add(d)
        db.commit()
        db.refresh(d)
        return d.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/bot/decisions/{decision_id}")
async def update_bot_decision(
    decision_id: int,
    body: DecisionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a decision (manual edit)"""
    from models.bot import Decision
    from datetime import datetime as dt
    d = db.query(Decision).filter(Decision.id == decision_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Decision not found")
    if body.symbol is not None:
        d.symbol = body.symbol.strip().upper()
    if body.decision is not None:
        d.decision = body.decision.upper()
    if body.execution_time is not None:
        try:
            d.execution_time = dt.fromisoformat(body.execution_time.replace("Z", "+00:00"))
        except Exception:
            pass
    if body.reasoning is not None:
        d.reasoning = body.reasoning
    if body.status is not None:
        d.status = body.status.upper()
    db.commit()
    db.refresh(d)
    return d.to_dict()

@app.delete("/api/bot/decisions/{decision_id}")
async def delete_bot_decision(
    decision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete/cancel a decision"""
    from models.bot import Decision
    d = db.query(Decision).filter(Decision.id == decision_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Decision not found")
    db.delete(d)
    db.commit()
    return {"message": "Decision deleted"}

@app.post("/api/bot/decisions/{decision_id}/execute")
async def execute_bot_decision(
    decision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Immediately execute a pending decision"""
    print(f"[API] executing bot decision id: {decision_id}")
    from models.bot import Decision, Bot
    from services.bot_service import bot_service
    from services.ig_service import IGMarketsService
    from services.alpaca_service import AlpacaService, ALPACA_AVAILABLE
    from services.symbol_mapper import symbol_mapper
    
    # 1. Get Decision
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
        
    if decision.status == "EXECUTED":
         raise HTTPException(status_code=400, detail="Order already executed")
         
    # 2. Get Bot & Service
    bot = db.query(Bot).filter(Bot.id == decision.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot associated with decision not found")
        
    service = bot_service._get_configured_service(db, bot)
    if not service:
        raise HTTPException(status_code=400, detail="Trading service not configured for this bot")
        
    try:
        # 3. Prepare Execution
        original_symbol = decision.symbol
        action = decision.decision # BUY/SELL
        
        symbol = symbol_mapper.normalize_symbol(original_symbol)
        
        # Calculate Quantity (Same logic as scheduler)
        ORDER_AMOUNT_USD = 1000.0 
        qty = 1.0
        current_price = 0.0
        
        try:
            quote = await market_data_service.get_quote(symbol) 
            current_price = quote.get('price', 0.0)
        except Exception as e:
            print(f"Could not get price: {e}")
            
        if current_price > 0:
            raw_qty = ORDER_AMOUNT_USD / current_price
            qty = round(raw_qty, 4)
            if qty < 0.0001: qty = 0.0001
        
        print(f"[EXECUTE-API] Executing {action} {symbol} Qty:{qty} Price:{current_price}")
        
        # 4. Execute
        order_result = None
        if isinstance(service, IGMarketsService):
            epic = service.get_epic_for_symbol(symbol)
            if not epic:
                raise HTTPException(status_code=400, detail=f"Could not resolve epic for {symbol}")
            order_result = await service.place_market_order(
                epic=epic,
                direction=action.upper(),
                size=1 # Keep 1 for IG for now
            )
        elif isinstance(service, AlpacaService):
            if not ALPACA_AVAILABLE:
                raise HTTPException(
                    status_code=503,
                    detail="Alpaca library not available in this backend process. Close ALL backend terminal windows, then restart: from project folder run start-dev.bat (or in backend folder: python main.py). Ensure alpaca-py is installed: pip install alpaca-py"
                )
            order_result = await service.place_market_order(
                symbol=symbol,
                qty=qty,
                side=action.lower()
            )
        else:
            raise HTTPException(status_code=400, detail="Unknown execution service")
            
        # 5. Update Decision
        decision.status = "EXECUTED"
        decision.executed_at = datetime.now(timezone.utc)
        order_id = order_result.get('deal_reference') or order_result.get('id') or 'N/A'
        decision.reasoning = (decision.reasoning or "") + f" | MANUALLY EXECUTED | Order ID: {order_id} | Qty: {qty}"
        
        db.commit()
        db.refresh(decision)
        return decision.to_dict()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

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

@app.get("/api/alpaca/search")
async def search_alpaca_assets(query: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Search Alpaca assets for autocomplete"""
    print(f"[SEARCH_DEBUG] Received query: '{query}'")
    if not alpaca_service:
        # Fallback if Alpaca is not configured/installed - use local mapper
        return {"results": symbol_mapper.search(query)}
        
    try:
        # If globally configured, use it
        if alpaca_service.is_configured():
            results = await alpaca_service.search_assets(query)
            return {"results": results}
            
        # If not globally configured, check user's accounts
        from models.account import Account
        alpaca_acc = db.query(Account).filter(
            Account.user_id == current_user.id,
            Account.platform == 'Alpaca',
            Account.is_active == True
        ).first()
        
        if alpaca_acc:
            creds = alpaca_acc.get_credentials()
            api_key = creds.get('api_key')
            # Handle different key names from frontend form (api_key vs api_key_id)
            if not api_key: api_key = creds.get('api_key_id')
            
            api_secret = creds.get('secret_key')
            paper = creds.get('paper_trading', True)
            
            if api_key and api_secret:
                results = await alpaca_service.search_assets(query, api_key, api_secret, paper)
                return {"results": results}
                
        # Default fallback to local mapper if no Alpaca config found
        return {"results": symbol_mapper.search(query)}
    except Exception as e:
        print(f"Error searching Alpaca assets: {e}")
        # Fallback to local mapper on error
        return {"results": symbol_mapper.search(query)}


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
                gemini_model = (getattr(current_user, 'gemini_model', None) or '').strip() or None
                gemini = GeminiService(api_key=current_user.gemini_api_key, model_name=gemini_model)
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
        email = None
        identifier = None
        password = None
        
        print(f"[LOGIN] Content-Type: {content_type}")
        
        # Try to parse as form-data first (OAuth2PasswordRequestForm standard)
        if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            try:
                form_data = await request.form()
                username = form_data.get("username")
                email = form_data.get("email")
                identifier = form_data.get("identifier")
                password = form_data.get("password")
                print(f"[LOGIN] Parsed form-data: username={username is not None}, email={email is not None}")
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
                    email = body.get("email")
                    identifier = body.get("identifier")
                    password = body.get("password")
                    print(f"[LOGIN] Parsed JSON: username={username is not None}, email={email is not None}")
            except Exception as e:
                print(f"[LOGIN] Error parsing JSON: {e}")

        if not username:
            username = email or identifier
        
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
                "llama_api_key": user.llama_api_key,
                "gemini_model": user.gemini_model,
                "openai_model": user.openai_model,
                "anthropic_model": user.anthropic_model,
                "deepseek_model": user.deepseek_model,
                "llama_model": user.llama_model,
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
        "llama_api_key": current_user.llama_api_key,
        "gemini_model": current_user.gemini_model,
        "openai_model": current_user.openai_model,
        "anthropic_model": current_user.anthropic_model,
        "deepseek_model": current_user.deepseek_model,
        "llama_model": current_user.llama_model,
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
        if profile_data.llama_api_key is not None:
            current_user.llama_api_key = profile_data.llama_api_key
        if profile_data.gemini_model is not None:
            current_user.gemini_model = profile_data.gemini_model
        if profile_data.openai_model is not None:
            current_user.openai_model = profile_data.openai_model
        if profile_data.anthropic_model is not None:
            current_user.anthropic_model = profile_data.anthropic_model
        if profile_data.deepseek_model is not None:
            current_user.deepseek_model = profile_data.deepseek_model
        if profile_data.llama_model is not None:
            current_user.llama_model = profile_data.llama_model

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
            "llama_api_key": current_user.llama_api_key,
            "gemini_model": current_user.gemini_model,
            "openai_model": current_user.openai_model,
            "anthropic_model": current_user.anthropic_model,
            "deepseek_model": current_user.deepseek_model,
            "llama_model": current_user.llama_model,
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
async def _process_ai_background(user_id: int, message: str, invite_llama: bool = False, invite_gemini: bool = False, is_search: bool = False):
    """Background task: process AI response with a fresh DB session"""
    db = SessionLocal()
    try:
        await chat_service.process_ai_response(
            user_id, message, db,
            invite_llama=invite_llama,
            invite_gemini=invite_gemini,
            is_search=is_search,
            ws_manager=ws_manager,
        )
    except Exception as e:
        print(f"[Chat] AI background error: {e}")
    finally:
        db.close()

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
        
        # Ritorna subito: il frontend mostra il messaggio dalla risposta
        # L'AI gira in background e invia la risposta via WebSocket
        asyncio.create_task(_process_ai_background(
            current_user.id, message.message,
            invite_llama=message.invite_llama,
            invite_gemini=message.invite_gemini,
            is_search=message.is_search,
        ))
        
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
        
        # Global Account
        if config.account_id:
            config_dict['account_id'] = config.account_id
        if config.broker:
            config_dict['broker'] = config.broker
            
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

@app.post("/api/bots/test-connection")
async def test_bot_connection(request: TestConnectionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Test broker connection with provided configuration"""
    try:
        broker = request.broker
        config = request.config
        
        # If account_id is provided, fetch credentials from DB
        account_id = config.get('account_id')
        if account_id:
            from models.account import Account
            saved_account = db.query(Account).filter(
                Account.id == account_id,
                Account.user_id == current_user.id
            ).first()
            
            if saved_account:
                creds = saved_account.get_credentials()
                # Merge credentials into config (giving precedence to manual overrides if any, though usually hidden)
                # We update config with saved credentials where missing
                if saved_account.platform == 'Alpaca':
                    if not config.get('alpaca_api_key'): config['alpaca_api_key'] = creds.get('api_key') or creds.get('api_key_id')
                    if not config.get('alpaca_api_secret'): config['alpaca_api_secret'] = creds.get('secret_key')
                    if config.get('alpaca_paper') is None: config['alpaca_paper'] = creds.get('paper_trading', True)
                elif saved_account.platform == 'IG':
                    if not config.get('ig_username'): config['ig_username'] = creds.get('username')
                    if not config.get('ig_password'): config['ig_password'] = creds.get('password')
                    if not config.get('ig_api_key'): config['ig_api_key'] = creds.get('api_key')
                    if not config.get('ig_acc_type'): config['ig_acc_type'] = creds.get('account_type', 'DEMO')

        if broker == 'IG':
            from services.ig_service import IGMarketsService
            
            username = config.get('ig_username')
            password = config.get('ig_password')
            api_key = config.get('ig_api_key')
            acc_type = config.get('ig_acc_type', 'DEMO')
            
            if not username or not password or not api_key:
                return {"success": False, "message": "Missing required IG credentials"}
                
            service = IGMarketsService(
                username=username,
                password=password,
                api_key=api_key,
                acc_type=acc_type
            )
            
            if service.is_configured():
                # Try to fetch account to verify
                try:
                    account = await service.get_account()
                    if account:
                        return {
                            "success": True, 
                            "message": f"Successfully connected to IG {acc_type} account: {account.get('account_name')}"
                        }
                except Exception as e:
                    return {"success": False, "message": f"Connection failed: {str(e)}"}
            
            return {"success": False, "message": "Could not initialize IG service with provided credentials"}
            
        if broker == 'Alpaca':
            from services.alpaca_service import AlpacaService
            
            print(f"[DEBUG] Test Connection Request. Config: {config}")
            if account_id:
               print(f"[DEBUG] Found account_id: {account_id}. Attempting DB lookup.")
               
            api_key = config.get('alpaca_api_key', '').strip()
            api_secret = config.get('alpaca_api_secret', '').strip()
            paper = config.get('alpaca_paper', True)
            
            # Auto-detect paper mode if key starts with PK (standard for Alpaca Paper)
            if api_key.startswith('PK'):
                paper = True
            
            print(f"[DEBUG] Keys after lookup/strip - Key len: {len(api_key)}, Secret len: {len(api_secret)}, Paper: {paper}")
            
            if not api_key or not api_secret:
                print("[DEBUG] Missing credentials")
                return {
                    "success": False,
                    "message": "Servono entrambi: API Key ID (es. PK...) e Secret Key. Su Alpaca la Secret si vede una sola volta alla creazione; se non ce l'hai più, clicca Regenerate e copia entrambi."
                }
            
            try:
                # Initialize service (may fail if alpaca-py is not installed)
                service = AlpacaService(api_key=api_key, api_secret=api_secret, paper=paper)
                
                if service.is_configured() and service.client:
                    # SDK available and configured: verify with get_account()
                    try:
                        account = await service.get_account()
                        if account:
                            return {"success": True, "message": "Successfully connected to Alpaca"}
                    except Exception as e:
                        return {"success": False, "message": f"Alpaca account error: {str(e)}"}
                
                # SDK not available or not configured: verify credentials via REST (no alpaca-py needed)
                ok, rest_msg = _verify_alpaca_credentials_rest(api_key, api_secret, paper)
                if ok:
                    return {
                        "success": True,
                        "message": "Successfully connected to Alpaca (credentials verified via API). Install alpaca-py for full trading features."
                    }
                return {"success": False, "message": f"Connection Failed: {rest_msg}"}
            except Exception as e:
                # Last resort: try REST verification (e.g. exception was from SDK init)
                ok, rest_msg = _verify_alpaca_credentials_rest(api_key, api_secret, paper)
                if ok:
                    return {
                        "success": True,
                        "message": "Successfully connected to Alpaca (credentials verified via API). Install alpaca-py for full trading features."
                    }
                import traceback
                traceback.print_exc()
                return {"success": False, "message": f"Alpaca connection failed: {str(e)}"}
                
        else:
            # For other brokers (placeholders)
            return {"success": False, "message": f"Connection test for {broker} is not yet implemented (Coming Soon)"}
            
    except Exception as e:
        print(f"Error testing connection: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

class TestAIConnectionRequest(BaseModel):
    provider: str  # gemini, openai, anthropic, deepseek, llama
    api_key: str

@app.post("/api/auth/test-ai-connection")
async def test_ai_connection(request: TestAIConnectionRequest, current_user: User = Depends(get_current_user)):
    """Test AI API connection with provided API key"""
    try:
        provider = request.provider.lower()
        api_key = request.api_key.strip()
        
        if not api_key:
            return {"success": False, "message": "API key is required"}
        
        if provider == 'gemini':
            try:
                from services.gemini_service import GeminiService
                # Get model from user's profile if available, otherwise use default
                gemini_model = (getattr(current_user, 'gemini_model', None) or '').strip() or None
                service = GeminiService(api_key=api_key, model_name=gemini_model)
                if service.available and service.client:
                    # Try a simple test call to verify the API key works (uses fallback on 429)
                    try:
                        response = service._generate_with_fallback("test")
                        # Verify we got a response (don't access .text to avoid errors)
                        if response is not None:
                            return {"success": True, "message": f"Gemini API key is valid (using model: {service.model_name})"}
                        else:
                            return {"success": False, "message": "Received empty response from Gemini API"}
                    except Exception as e:
                        error_msg = str(e)
                        # Check for common error types
                        if "404" in error_msg or "not found" in error_msg.lower():
                            return {"success": False, "message": f"Model '{service.model_name}' not found. Please check the model name in your settings."}
                        elif "403" in error_msg or "permission" in error_msg.lower():
                            return {"success": False, "message": "API key is invalid or lacks required permissions"}
                        elif "401" in error_msg or "unauthorized" in error_msg.lower():
                            return {"success": False, "message": "API key is invalid or unauthorized"}
                        else:
                            return {"success": False, "message": f"Gemini connection failed: {error_msg}"}
                else:
                    return {"success": False, "message": "Could not initialize Gemini service"}
            except Exception as e:
                import traceback
                traceback.print_exc()
                return {"success": False, "message": f"Gemini test failed: {str(e)}"}
        
        elif provider == 'openai':
            try:
                from services.llm_factory import OpenAIClient
                client = OpenAIClient(api_key)
                # Make a minimal test call
                response = client.generate_content("test")
                if "Error calling OpenAI" in response:
                    return {"success": False, "message": response}
                return {"success": True, "message": "OpenAI API key is valid"}
            except Exception as e:
                return {"success": False, "message": f"OpenAI test failed: {str(e)}"}
        
        elif provider == 'anthropic' or provider == 'claude':
            try:
                from services.llm_factory import AnthropicClient
                client = AnthropicClient(api_key)
                # Make a minimal test call
                response = client.generate_content("test")
                if "Error calling Anthropic" in response:
                    return {"success": False, "message": response}
                return {"success": True, "message": "Claude API key is valid"}
            except Exception as e:
                return {"success": False, "message": f"Claude test failed: {str(e)}"}
        
        elif provider == 'deepseek':
            try:
                from services.llm_factory import DeepseekClient
                client = DeepseekClient(api_key)
                # Make a minimal test call
                response = client.generate_content("test")
                if "Error calling Deepseek" in response:
                    return {"success": False, "message": response}
                return {"success": True, "message": "DeepSeek API key is valid"}
            except Exception as e:
                return {"success": False, "message": f"DeepSeek test failed: {str(e)}"}
        
        elif provider == 'llama':
            # For Llama API, we'd need to check if there's a way to test it
            # For now, just validate the key format
            if api_key.startswith('LA-'):
                return {"success": True, "message": "Llama API key format is valid"}
            else:
                return {"success": False, "message": "Invalid Llama API key format (should start with 'LA-')"}
        
        else:
            return {"success": False, "message": f"Unknown provider: {provider}"}
            
    except Exception as e:
        print(f"Error testing AI connection: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

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
        # Prefer profile key (site-wide) so user's Profile API key is used everywhere
        config = bot.get_config()
        gemini_api_key = (
            current_user.gemini_api_key
            or config.get('gemini_api_key')
            or os.getenv('GOOGLE_GEMINI_API_KEY')
        )
        if not gemini_api_key:
            raise HTTPException(
                status_code=400,
                detail="No Gemini API key configured. Add one in Profile settings.",
            )
        gemini_model = (getattr(current_user, 'gemini_model', None) or '').strip() or None
        gemini_service = GeminiService(api_key=gemini_api_key, model_name=gemini_model)
        
        if request and request.prompt:
            # Chat mode
            history = request.history or []
            explanation = await gemini_service.chat_about_bot(context, history, request.prompt)
        else:
            # Initial explanation mode
            explanation = await gemini_service.generate_explanation(context)
        
        return {"explanation": explanation}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bots/{bot_id}/call/weekly-plan")
async def call_weekly_plan(
    bot_id: int,
    request: Optional[BotChatRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly trading plan from AI"""
    try:
        bot = bot_service.get_bot(db, bot_id, current_user.id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")

        # 1. Get Watchlist
        watchlist = watchlist_service.get_watchlist()
        
        # 2. Get Quotes for Watchlist
        market_data = []
        for item in watchlist:
            try:
                quote = await market_data_service.get_quote(item['symbol'])
                market_data.append(f"{item['symbol']} ({item['name']}): Price ${quote.get('price')}, Change {quote.get('change_percent')}%")
            except Exception:
                market_data.append(f"{item['symbol']}: Data unavailable")
        
        market_context = "\n".join(market_data)

        # 3. Construct Context
        context = f"Bot Name: {bot.name}\n"
        context += f"Current Watchlist & Market Data:\n{market_context}\n\n"
        context += "Task: Analyze the watchlist and provide a trading plan for the upcoming week. Identify potential entry/exit points and key levels to watch."

        # 4. Call AI (Gemini preferred)
        # Prefer profile key (site-wide) so user's Profile API key is used everywhere
        config = bot.get_config()
        gemini_api_key = (
            current_user.gemini_api_key
            or config.get('gemini_api_key')
            or os.getenv('GOOGLE_GEMINI_API_KEY')
        )
        if gemini_api_key:
            gemini_model = (getattr(current_user, 'gemini_model', None) or '').strip() or None
            gemini_service = GeminiService(api_key=gemini_api_key, model_name=gemini_model)
            if request and request.prompt:
                history = request.history or []
                explanation = await gemini_service.chat_about_bot(context, history, request.prompt)
            else:
                explanation = await gemini_service.generate_explanation(context)
        else:
            # Fallback to Llama
            if request and request.prompt:
                history = request.history or []
                explanation = llama_service.chat_about_bot(context, history, request.prompt)
            else:
                explanation = llama_service.generate_explanation(context)
        
        return {"explanation": explanation}
    except Exception as e:
        print(f"Error calling Weekly Plan: {e}")
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


@app.get("/api/users/by-username")
async def get_user_by_username(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Look up user by username (for private chat). Returns id and username if found."""
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="Username required")
    user = get_user_by_username(db, username.strip())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot chat with yourself")
    return {"id": user.id, "username": user.username}


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

        # Fallback to cached calendar if API returns empty
        if not earnings_data:
            try:
                if start_date:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
                else:
                    start_dt = datetime.now().date()
                cached_calendar = earnings_service._get_cached_calendar(start_dt, months)
                if cached_calendar:
                    earnings_data = cached_calendar
                    print(f"[API] Using cached calendar fallback with {len(earnings_data)} items")
            except Exception as cache_error:
                print(f"[API] Cache fallback failed: {cache_error}")
        
        # Includiamo tutti i giorni (anche sabato e domenica)
        print(f"[API] Returning {len(earnings_data)} earnings (including weekends)")
        
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
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Hot reload for development
        log_level="info"
    )


# ---------------------------------------------------------------------
# Bot Decisions Endpoints
# ---------------------------------------------------------------------

class DecisionCreate(BaseModel):
    bot_id: int
    symbol: str
    decision: str
    execution_time: Optional[datetime] = None
    reasoning: Optional[str] = None
    status: Optional[str] = "PENDING"

class DecisionUpdate(BaseModel):
    symbol: Optional[str] = None
    decision: Optional[str] = None
    execution_time: Optional[datetime] = None
    reasoning: Optional[str] = None
    status: Optional[str] = None

@app.get("/api/bot/decisions")
async def get_bot_decisions(
    limit: int = 50,
    bot_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bot decisions, optionally filtered by bot_id"""
    try:
        query = db.query(Decision)
        
        # If bot_id is provided, filter by it
        if bot_id:
            # Verify bot belongs to user
            bot = bot_service.get_bot(db, bot_id, current_user.id)
            if not bot:
                # If not found for user, return empty or error? Customary to return empty or 404.
                # But here we filter, so maybe empty list is safer if bot doesn't match?
                # Actually, strictly enforcing ownership:
                return {"decisions": []}
            query = query.filter(Decision.bot_id == bot_id)
        else:
            # Filter by user's bots if no bot_id specified? 
            # Or just all decisions? 
            # To be safe, filter by user's bots
            user_bot_ids = [b.id for b in bot_service.get_user_bots(db, current_user.id)]
            if user_bot_ids:
                query = query.filter(Decision.bot_id.in_(user_bot_ids))
            else:
                return {"decisions": []}
                
        decisions = query.order_by(Decision.created_at.desc()).limit(limit).all()
        return {"decisions": [d.to_dict() for d in decisions]}
    except Exception as e:
        print(f"Error fetching decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/bot/decisions/{decision_id}")
async def update_bot_decision(
    decision_id: int,
    decision_update: DecisionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a decision"""
    try:
        db_decision = db.query(Decision).filter(Decision.id == decision_id).first()
        if not db_decision:
            raise HTTPException(status_code=404, detail="Decision not found")
            
        # Verify ownership via bot
        bot = bot_service.get_bot(db, db_decision.bot_id, current_user.id)
        if not bot:
             raise HTTPException(status_code=403, detail="Not authorized")

        if decision_update.symbol:
            db_decision.symbol = decision_update.symbol.upper()
        if decision_update.decision:
            db_decision.decision = decision_update.decision.upper()
        if decision_update.execution_time:
            db_decision.execution_time = decision_update.execution_time
        if decision_update.status:
            db_decision.status = decision_update.status.upper()
        if decision_update.reasoning is not None:
            db_decision.reasoning = decision_update.reasoning
            
        db.commit()
        db.refresh(db_decision)
        return db_decision.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bot/decisions/{decision_id}")
async def delete_bot_decision(
    decision_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a decision"""
    try:
        db_decision = db.query(Decision).filter(Decision.id == decision_id).first()
        if not db_decision:
            raise HTTPException(status_code=404, detail="Decision not found")
            
        # Verify ownership
        bot = bot_service.get_bot(db, db_decision.bot_id, current_user.id)
        if not bot:
             raise HTTPException(status_code=403, detail="Not authorized")
             
        db.delete(db_decision)
        db.commit()
        return {"message": "Decision deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bot/profit")
async def get_bot_profit(current_user: User = Depends(get_current_user)):
    """Get bot profit summary (simple implementation)"""
    try:
        # Just return the latest profitto.json content for now
        # Ideally this should be per-bot or aggregated
        profit_path = os.path.join("backend", "profitto.json")
        if os.path.exists(profit_path):
            with open(profit_path, "r") as f:
                data = json.load(f)
                return data
        return None
    except Exception as e:
        print(f"Error getting profit: {e}")
        return None

# Account Management Endpoints

class AccountCreate(BaseModel):
    platform: str # IG, Alpaca, eToro
    name: str # "My IG Live", "eToro Demo"
    credentials: Dict[str, Any]
    is_active: bool = True
    is_default: bool = False

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

@app.get("/api/accounts", response_model=Dict[str, List[Dict[str, Any]]])
async def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all accounts for the current user"""
    accounts = current_user.accounts
    return {"accounts": [acc.to_dict(include_credentials=False) for acc in accounts]}

@app.post("/api/accounts")
async def create_account(
    account_in: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new account"""
    # If this is set as default, unset other defaults for same platform
    if account_in.is_default:
        existing_defaults = db.query(Account).filter(
            Account.user_id == current_user.id,
            Account.platform == account_in.platform,
            Account.is_default == True
        ).all()
        for acc in existing_defaults:
            acc.is_default = False
    
    account = Account(
        user_id=current_user.id,
        platform=account_in.platform,
        name=account_in.name,
        is_active=account_in.is_active,
        is_default=account_in.is_default
    )
    account.set_credentials(account_in.credentials)
    
    db.add(account)
    db.commit()
    db.refresh(account)
    return account.to_dict()

@app.put("/api/accounts/{account_id}")
async def update_account(
    account_id: int,
    account_in: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an account"""
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if account_in.name is not None:
        account.name = account_in.name
    
    if account_in.is_active is not None:
        account.is_active = account_in.is_active
        
    if account_in.credentials is not None:
        account.set_credentials(account_in.credentials)
        
    if account_in.is_default is not None:
        if account_in.is_default and not account.is_default:
            # Unset other defaults
            existing_defaults = db.query(Account).filter(
                Account.user_id == current_user.id,
                Account.platform == account.platform,
                Account.is_default == True
            ).all()
            for acc in existing_defaults:
                acc.is_default = False
        account.is_default = account_in.is_default
        
    db.commit()
    db.refresh(account)
    return account.to_dict()

@app.delete("/api/accounts/{account_id}")
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an account"""
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    db.delete(account)
    db.commit()
    return {"message": "Account deleted"}

@app.post("/api/accounts/{account_id}/test")
async def test_account_connection(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test connection for a saved account"""
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    creds = account.get_credentials()
    
    # Reuse the existing test logic from bot_service or a new service
    # For now, we'll manually call the test logic here or import it
    
    try:
        from services.bot_service import bot_service
        # Reuse existing test_connection logic but adapt the input
        # Note: bot_service.test_connection expects {'broker': ..., 'config': ...}
        
        # Map credentials to what bot_service expects
        test_config = {}
        if account.platform == 'Alpaca':
            test_config = {
                'alpaca_api_key': creds.get('api_key'),
                'alpaca_api_secret': creds.get('secret_key'),
                'alpaca_paper': creds.get('paper_trading', True)
            }
        elif account.platform in ('IG', 'eToro'):
            return {"success": False, "message": "Platform no longer supported. Use Alpaca."}

        # Call existing service
        # We might need to expose a helper in bot_service or just replicate logic
        # For simplicity, let's just use the existing behavior if possible
        
        # Since bot_service.test_connection is an instance method, we can try using it if we have an instance
        # It's instantiated as bot_service in this file
        
        result = await bot_service.test_connection(account.platform, test_config)
        return result
        
    except Exception as e:
        return {"success": False, "message": str(e)}

